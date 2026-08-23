# Validation Layer Design

## Architecture Overview

```
User Question
    ↓
Cortex generates SQL
    ↓
┌─────────────────────────────────┐
│  VALIDATION LAYER               │
├─────────────────────────────────┤
│ 1. SQL Parse                    │
│    ↓ Extract: SELECT, FROM, WHERE, JOIN, GROUP BY
│                                 │
│ 2. Schema Validation            │
│    ↓ Compare vs known schema    │
│                                 │
│ 3. Grain Check                  │
│    ↓ Verify GROUP BY matches    │
│      primary key definition     │
│                                 │
│ 4. Execute Query (LIMIT 1000)   │
│    ↓ Get actual results         │
│                                 │
│ 5. Result Validation            │
│    ├─ Duplicate Detection       │
│    ├─ Fan-out Detection         │
│    └─ Cardinality Check         │
│                                 │
│ 6. Decision                     │
│    ├─ PASS → Execute full query │
│    ├─ WARN → Execute + flag     │
│    └─ FAIL → Reject + explain   │
└─────────────────────────────────┘
    ↓
Execute Full Query
    ↓
Return Results
```

## Design Components

### 1. **Schema Registry** (Static Metadata)

```python
# src/validation/schema_registry.py

FACT_TABLES = {
    'FACT_POPULATION_AGE': {
        'grain': ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX'],
        'expected_rows': 'BLOCK_GROUPS * AGE_GROUPS * SEX_VALUES',
        # block_groups ≈ 220k, age_groups = 23, sex = 2-3
        # Expected: ~10M rows
        'metrics': ['POPULATION_ESTIMATE', 'MARGIN_OF_ERROR'],
        'dimensions': ['DIM_AGE', 'DIM_BLOCK_GROUP'],
    },
    'FACT_RACE_ETHNICITY': {
        'grain': ['CENSUS_BLOCK_GROUP', 'RACE_ID'],
        'expected_rows': 'BLOCK_GROUPS * RACE_CATEGORIES',
        # ~220k * 9 ≈ 2M rows
        'metrics': ['POPULATION_ESTIMATE', 'MARGIN_OF_ERROR'],
    },
    'FACT_HOUSEHOLD_COMPOSITION': {
        'grain': ['CENSUS_BLOCK_GROUP', 'HOUSEHOLD_TYPE_ID'],
        'expected_rows': 'BLOCK_GROUPS * HOUSEHOLD_TYPES',
        # ~220k * 8 ≈ 1.7M rows
        'metrics': ['HOUSEHOLD_COUNT', 'MARGIN_OF_ERROR'],
    }
}

DIM_TABLES = {
    'DIM_AGE': {'expected_rows': 23},
    'DIM_BLOCK_GROUP': {'expected_rows': 220000},
    'DIM_RACE': {'expected_rows': 9},
    'DIM_HOUSEHOLD_TYPE': {'expected_rows': 8},
}

EXPECTED_AGGREGATIONS = {
    # state level: 50 states (should return ~50 rows when grouped by state)
    'BY_STATE': 50,
    # age groups: 23 age groups
    'BY_AGE': 23,
    # race categories: 9 categories
    'BY_RACE': 9,
    # sex: 2-3 values (Male, Female, Total)
    'BY_SEX': 3,
}
```

### 2. **Query Parser** (SQL Analysis)

```python
# src/validation/query_parser.py

class QueryParser:
    def parse(self, sql: str) -> QueryStructure:
        """Extract structure from SQL"""
        return QueryStructure(
            tables_accessed=['FACT_POPULATION_AGE', 'DIM_AGE'],
            group_by_columns=['STATE_NAME_FULL', 'AGE_LABEL'],
            select_columns=['STATE_NAME_FULL', 'AGE_LABEL', 'POPULATION_ESTIMATE'],
            join_conditions=[...],
            where_conditions=[...],
            limit=None,
        )
```

### 3. **Grain Validator** (Mechanical Check)

```python
# src/validation/grain_validator.py

class GrainValidator:
    def validate(self, parsed_query: QueryStructure) -> ValidationResult:
        """
        Check: Does GROUP BY match fact table grain?
        
        Mechanical rule:
        - Extract GROUP BY columns from query
        - For each fact table accessed, check if GROUP BY includes
          all grain columns (or is at higher aggregation level)
        
        Example:
          Query: SELECT state, POPULATION_ESTIMATE FROM FACT_POPULATION_AGE
          Missing: GROUP BY - This aggregates across age/sex
          Result: ⚠️ WARN - Implicit aggregation (valid but explicit is better)
          
          Query: SELECT state, age, sex, POPULATION_ESTIMATE FROM ... GROUP BY state, age, sex
          Check: DIM_BLOCK_GROUP grain not in GROUP BY
          Result: ✅ PASS - Aggregating at higher level (valid)
        """
        
        for table in parsed_query.tables_accessed:
            table_grain = SCHEMA_REGISTRY[table]['grain']
            group_by = parsed_query.group_by_columns
            
            # Valid patterns:
            # 1. GROUP BY includes ALL grain columns (grain-preserving)
            # 2. GROUP BY includes SUBSET of grain columns (rolling up aggregation)
            # 3. No GROUP BY with aggregation function (implicit aggregation)
            
            grain_match = self._check_grain_match(table_grain, group_by)
            
            if grain_match == 'PRESERVE':
                return ValidationResult.PASS
            elif grain_match == 'ROLLUP':
                return ValidationResult.PASS
            elif grain_match == 'IMPLICIT':
                return ValidationResult.WARN
            else:
                return ValidationResult.FAIL('Grain mismatch')
```

### 4. **Result Validator** (Post-Execution Check)

```python
# src/validation/result_validator.py

class ResultValidator:
    def validate_duplicates(self, results: pd.DataFrame, grain: List[str]) -> ValidationResult:
        """
        Check: Are there duplicate rows at grain level?
        
        Mechanical rule:
        - Count rows by grain columns
        - If any grain combination appears >1 time: FAIL
        
        Example:
          Grain: [STATE, AGE_GROUP, SEX]
          Query result has 2 rows with STATE='CA', AGE='25-29', SEX='Male'
          Result: ❌ FAIL - Duplicate grain detected
        """
        duplicates = results.duplicated(subset=grain, keep=False)
        if duplicates.any():
            dup_count = duplicates.sum()
            return ValidationResult.FAIL(f'{dup_count} duplicate rows at grain level')
        return ValidationResult.PASS
    
    def validate_no_fanout(self, results: pd.DataFrame, grain: List[str]) -> ValidationResult:
        """
        Check: Did a JOIN cause unexpected row multiplication?
        
        Mechanical rule:
        - Count expected rows based on grain
        - Compare to actual rows returned
        - If actual >> expected: possible fan-out
        
        Example:
          Expected: 50 states (grain: STATE)
          Actual: 50 * 23 = 1150 rows (also has AGE_GROUP)
          Analysis: JOIN with age table multiplied rows
          Decision: ✅ PASS if this was intentional
                    ❌ FAIL if unintentional
                    
        Algorithm:
          1. Get cardinality of each grain column
          2. Multiply: CARD(STATE) × CARD(AGE) × CARD(SEX)
          3. Compare to actual row count
          4. If actual ≤ expected: PASS
          5. If actual > expected: WARN (possible fan-out)
        """
        expected_rows = self._calculate_expected_cardinality(grain)
        actual_rows = len(results)
        
        if actual_rows <= expected_rows:
            return ValidationResult.PASS
        elif actual_rows > expected_rows * 1.1:  # 10% tolerance
            return ValidationResult.WARN(
                f'Possible fan-out: expected ~{expected_rows}, got {actual_rows}'
            )
        return ValidationResult.PASS
    
    def validate_cardinality(self, results: pd.DataFrame, table: str) -> ValidationResult:
        """
        Check: Do row counts match expectations?
        
        Mechanical rule:
        - Compare actual row count to SCHEMA_REGISTRY expectations
        - Flag if significantly different
        
        Example:
          Expected for FACT_POPULATION_AGE: ~10M rows
          Actual: 100 rows
          Analysis: Query heavily filtered (or missing data)
          Result: ⚠️ WARN - Unexpected low cardinality
        """
        expected = SCHEMA_REGISTRY[table]['expected_rows']
        actual = len(results)
        
        # Tolerance: ±50% acceptable (filtering is normal)
        if expected * 0.5 <= actual <= expected * 1.5:
            return ValidationResult.PASS
        else:
            return ValidationResult.WARN(
                f'Cardinality mismatch: expected ~{expected}, got {actual}'
            )
```

### 5. **Validator Orchestrator** (Main Entry Point)

```python
# src/validation/validator.py

class QueryValidator:
    def validate_compiled_query(
        self,
        sql: str,
        max_preview_rows: int = 1000
    ) -> ValidationReport:
        """
        Entry point: Validate SQL before full execution
        
        Steps:
        1. Parse SQL structure
        2. Validate grain
        3. Execute with LIMIT for preview
        4. Validate duplicates, fan-out, cardinality
        5. Return report
        """
        
        # Step 1: Parse
        parsed = QueryParser().parse(sql)
        
        # Step 2: Validate grain
        grain_result = GrainValidator().validate(parsed)
        if grain_result.status == FAIL:
            return ValidationReport(
                status=FAIL,
                reason=grain_result.message,
                details={'grain_issue': grain_result.message}
            )
        
        # Step 3: Execute with limit for preview
        preview = self._execute_preview_query(sql, max_preview_rows)
        
        # Step 4: Validate results
        validator = ResultValidator()
        
        results = {
            'duplicates': validator.validate_duplicates(preview, grain),
            'fan_out': validator.validate_no_fanout(preview, grain),
            'cardinality': validator.validate_cardinality(preview, table),
        }
        
        # Step 5: Decide
        return self._compile_report(results)
```

### 6. **Integration Point** (In cortex_analyst.py)

```python
# In src/cortex_analyst.py query() method

def query(user_message: str, conversation_history: list = None) -> dict:
    # ... existing code ...
    
    # After Cortex generates SQL
    if sql_query:
        # NEW: Validate before execution
        validator = QueryValidator()
        validation = validator.validate_compiled_query(sql_query)
        
        if validation.status == FAIL:
            return {
                'response': f"Query validation failed: {validation.reason}",
                'data': [],
                'success': True,
                'error': None,
                'validation': validation
            }
        elif validation.status == WARN:
            logger.warning(f"Query validation warning: {validation.reason}")
            # Continue but flag in response
        
        # Execute full query
        data_results = SnowflakeClient.query(sql_query)
        # ... rest of code ...
```

## Validation Result Structure

```python
class ValidationResult:
    status: str  # PASS, WARN, FAIL
    message: str
    details: dict
    
    # Example FAIL result:
    {
        'status': 'FAIL',
        'message': 'Duplicate rows detected at grain level',
        'details': {
            'grain': ['STATE', 'AGE_GROUP', 'SEX'],
            'duplicate_count': 45,
            'example_duplicates': [
                {'STATE': 'CA', 'AGE_GROUP': '25-29', 'SEX': 'Male'},
            ]
        }
    }
```

## File Structure

```
src/validation/
├── __init__.py
├── schema_registry.py      # Static metadata
├── query_parser.py         # SQL extraction
├── grain_validator.py      # Grain check
├── result_validator.py     # Duplicates, fan-out, cardinality
├── validator.py            # Orchestrator
└── test_validators.py      # Unit tests
```

## Testing Strategy

### Unit Tests (No DB)
- Parse SQL variations
- Grain matching logic
- Cardinality calculations

### Integration Tests (With DB)
- Full validation pipeline
- Preview query execution
- Real result validation

### Examples

```python
# Test: Grain validation
test_grain_validation():
    sql = "SELECT STATE, AGE_GROUP, SUM(POPULATION) FROM FACT_POPULATION_AGE GROUP BY STATE, AGE_GROUP"
    result = GrainValidator().validate(parse(sql))
    assert result.status == PASS  # Grain preserved

# Test: Duplicate detection
test_duplicate_detection():
    results = pd.DataFrame({
        'STATE': ['CA', 'CA'],
        'AGE_GROUP': ['25-29', '25-29'],
        'POPULATION': [1000, 1000]  # Duplicate row!
    })
    result = ResultValidator().validate_duplicates(results, ['STATE', 'AGE_GROUP'])
    assert result.status == FAIL

# Test: Fan-out detection
test_fanout_detection():
    results = pd.DataFrame(...)  # 50 states * 23 ages = 1150 rows
    result = ResultValidator().validate_no_fanout(results, ['STATE'])
    assert result.status == WARN  # Unexpected multiplication
```

## Benefits

✅ **Mechanical** - No heuristics, pure logic  
✅ **Deterministic** - Same query always produces same validation result  
✅ **Early Detection** - Catches issues before full execution  
✅ **Maintainable** - Schema changes update registry, not code  
✅ **Testable** - Each validator independently testable  
✅ **Scalable** - Add new validators without touching orchestrator  

## Future Extensions

- Query cost estimation
- Performance warnings (slow query detection)
- Authorization checks (user can query these tables?)
- Privacy checks (PII column access?)
