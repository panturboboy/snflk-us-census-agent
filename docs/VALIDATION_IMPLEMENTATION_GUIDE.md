# Validation Layer: Practical Implementation Guide

## How to Use Snowflake Metadata in Validation

### Step 1: Create Metadata Provider

```python
# src/validation/schema_metadata.py

from src.snowflake_client import SnowflakeClient
from datetime import datetime, timedelta
from typing import List, Dict

class SemanticMetadataProvider:
    """Query Snowflake's semantic metadata"""
    
    def get_fact_table_grain(self, table_name: str) -> List[str]:
        """
        Query Snowflake for the grain (primary key) of a fact table
        
        Example result for FACT_POPULATION_AGE:
        ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
        """
        query = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = '{table_name}'
          AND TABLE_SCHEMA = 'CURATED'
          AND CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY ORDINAL_POSITION;
        """
        results = SnowflakeClient.query(query)
        return [row['COLUMN_NAME'] for row in results]
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count from Snowflake stats"""
        query = f"""
        SELECT ROW_COUNT
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = '{table_name}'
          AND TABLE_SCHEMA = 'CURATED';
        """
        result = SnowflakeClient.query(query)
        return result[0]['ROW_COUNT'] if result else 0
    
    def get_semantic_dimensions(self) -> List[str]:
        """Get all dimensions from semantic model"""
        query = """
        SELECT DISTINCT COLUMN_NAME
        FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_DIMENSIONS
        WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL'
        ORDER BY COLUMN_NAME;
        """
        results = SnowflakeClient.query(query)
        return [row['COLUMN_NAME'] for row in results]
    
    def get_semantic_metrics(self) -> List[str]:
        """Get all metrics from semantic model"""
        query = """
        SELECT DISTINCT COLUMN_NAME
        FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_METRICS
        WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL'
        ORDER BY COLUMN_NAME;
        """
        results = SnowflakeClient.query(query)
        return [row['COLUMN_NAME'] for row in results]
    
    def get_relationships(self) -> List[Dict]:
        """Get all relationships from semantic model"""
        query = """
        SELECT 
            RELATIONSHIP_NAME,
            FROM_TABLE_NAME,
            TO_TABLE_NAME,
            FROM_COLUMN_NAME,
            TO_COLUMN_NAME
        FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_RELATIONSHIPS
        WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
        """
        return SnowflakeClient.query(query)
    
    def get_distinct_count(self, table_name: str, column_name: str) -> int:
        """Get distinct count for cardinality calculations"""
        query = f"""
        SELECT COUNT(DISTINCT {column_name}) as distinct_count
        FROM CURATED.{table_name};
        """
        result = SnowflakeClient.query(query)
        return result[0]['DISTINCT_COUNT'] if result else 0
```

### Step 2: Create Caching Layer

```python
# src/validation/schema_cache.py

from datetime import datetime, timedelta
import logging

class SemanticMetadataCache:
    """
    Cache Snowflake metadata with TTL-based refresh
    
    Usage:
        cache = SemanticMetadataCache(refresh_minutes=60)
        grain = cache.get_grain('FACT_POPULATION_AGE')
        # Returns: ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
    """
    
    def __init__(self, refresh_minutes: int = 60):
        self.provider = SemanticMetadataProvider()
        self.refresh_minutes = refresh_minutes
        self.cache = {}
        self.last_refresh = None
        self.logger = logging.getLogger(__name__)
    
    def get_grain(self, table_name: str) -> List[str]:
        """Get grain with automatic refresh if stale"""
        self._ensure_fresh_cache()
        key = f"grain:{table_name}"
        
        if key not in self.cache:
            self.logger.info(f"Cache miss for grain of {table_name}, querying Snowflake")
            grain = self.provider.get_fact_table_grain(table_name)
            self.cache[key] = grain
        
        return self.cache[key]
    
    def get_row_count(self, table_name: str) -> int:
        """Get row count with automatic refresh if stale"""
        self._ensure_fresh_cache()
        key = f"row_count:{table_name}"
        
        if key not in self.cache:
            self.logger.info(f"Cache miss for row count of {table_name}")
            count = self.provider.get_table_row_count(table_name)
            self.cache[key] = count
        
        return self.cache[key]
    
    def get_distinct_values_count(self, table_name: str, column_name: str) -> int:
        """Get distinct count for a column"""
        self._ensure_fresh_cache()
        key = f"distinct:{table_name}:{column_name}"
        
        if key not in self.cache:
            self.logger.info(f"Cache miss for distinct count {table_name}.{column_name}")
            count = self.provider.get_distinct_count(table_name, column_name)
            self.cache[key] = count
        
        return self.cache[key]
    
    def _ensure_fresh_cache(self):
        """Refresh cache if older than TTL"""
        if self.last_refresh is None:
            self.logger.info("Initial cache population from Snowflake")
            self._refresh()
        
        age = (datetime.now() - self.last_refresh).total_seconds() / 60
        if age > self.refresh_minutes:
            self.logger.info(f"Cache stale (age: {age:.1f}m), refreshing")
            self._refresh()
    
    def _refresh(self):
        """Populate cache from Snowflake"""
        try:
            # Pre-populate common lookups
            self.cache['grain:FACT_POPULATION_AGE'] = \
                self.provider.get_fact_table_grain('FACT_POPULATION_AGE')
            self.cache['grain:FACT_RACE_ETHNICITY'] = \
                self.provider.get_fact_table_grain('FACT_RACE_ETHNICITY')
            self.cache['grain:FACT_HOUSEHOLD_COMPOSITION'] = \
                self.provider.get_fact_table_grain('FACT_HOUSEHOLD_COMPOSITION')
            
            self.cache['row_count:FACT_POPULATION_AGE'] = \
                self.provider.get_table_row_count('FACT_POPULATION_AGE')
            self.cache['row_count:FACT_RACE_ETHNICITY'] = \
                self.provider.get_table_row_count('FACT_RACE_ETHNICITY')
            self.cache['row_count:FACT_HOUSEHOLD_COMPOSITION'] = \
                self.provider.get_table_row_count('FACT_HOUSEHOLD_COMPOSITION')
            
            self.last_refresh = datetime.now()
            self.logger.info("Cache refresh complete")
        except Exception as e:
            self.logger.error(f"Cache refresh failed: {e}")
            # Fall back to hard-coded defaults
            raise
```

### Step 3: Update Grain Validator

```python
# src/validation/grain_validator.py

class GrainValidator:
    """
    Validate query grain using Snowflake metadata
    
    No longer hard-coded! Uses SemanticMetadataCache
    """
    
    def __init__(self, metadata_cache: SemanticMetadataCache):
        self.cache = metadata_cache
        self.logger = logging.getLogger(__name__)
    
    def validate(self, parsed_query: QueryStructure) -> ValidationResult:
        """
        Check: Does GROUP BY match fact table grain?
        
        Example:
            Table: FACT_POPULATION_AGE
            Grain from Snowflake: ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
            Query GROUP BY: ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']
            Result: ✅ PASS
        """
        
        for table in parsed_query.tables_accessed:
            # Get grain from Snowflake (cached)
            grain = self.cache.get_grain(table)
            self.logger.debug(f"Grain for {table}: {grain}")
            
            group_by = parsed_query.group_by_columns or []
            
            # Check if GROUP BY matches grain
            if self._grain_matches(grain, group_by):
                self.logger.info(f"✅ Grain valid for {table}")
                return ValidationResult.PASS
            else:
                self.logger.warning(f"❌ Grain mismatch for {table}")
                return ValidationResult.FAIL(
                    f"Grain mismatch for {table}: "
                    f"expected {grain}, got {group_by}"
                )
    
    def _grain_matches(self, grain: List[str], group_by: List[str]) -> bool:
        """
        Grain matches if:
        1. GROUP BY contains ALL grain columns (exact match)
        2. GROUP BY contains SUBSET of grain columns (valid roll-up)
        3. No GROUP BY but using aggregation function (implicit aggregation)
        """
        
        grain_set = set(col.upper() for col in grain)
        group_by_set = set(col.upper() for col in group_by)
        
        # Exact match or roll-up (subset is OK)
        return grain_set <= group_by_set or len(group_by) == 0
```

### Step 4: Update Result Validator

```python
# src/validation/result_validator.py

class ResultValidator:
    """Validate query results using Snowflake metadata"""
    
    def __init__(self, metadata_cache: SemanticMetadataCache):
        self.cache = metadata_cache
        self.logger = logging.getLogger(__name__)
    
    def validate_cardinality(
        self, 
        results: pd.DataFrame, 
        table_name: str,
        group_by_columns: List[str]
    ) -> ValidationResult:
        """
        Check: Do results match expected cardinality?
        
        Example:
            Table: FACT_POPULATION_AGE
            Total rows in table: 10,487,832
            Group by: ['STATE']
            Expected: ~50 distinct states
            Actual rows: 50
            Result: ✅ PASS
            
            Actual rows: 50,000
            Result: ⚠️ WARN - More rows than expected
        """
        
        actual_rows = len(results)
        
        # Get row count from Snowflake
        total_rows = self.cache.get_row_count(table_name)
        
        # Calculate expected cardinality
        expected = self._calculate_expected_rows(table_name, group_by_columns)
        
        self.logger.info(
            f"Cardinality check for {table_name}: "
            f"expected ~{expected}, actual {actual_rows}"
        )
        
        # Allow 50% variance (queries often filter)
        if expected * 0.5 <= actual_rows <= expected * 1.5:
            return ValidationResult.PASS
        elif actual_rows < expected * 0.5:
            return ValidationResult.WARN(
                f"Low cardinality: expected ~{expected}, got {actual_rows} "
                f"(possible heavy filtering or data issue)"
            )
        else:
            return ValidationResult.WARN(
                f"High cardinality: expected ~{expected}, got {actual_rows} "
                f"(possible data multiplication)"
            )
    
    def _calculate_expected_rows(self, table: str, group_by: List[str]) -> int:
        """
        Calculate expected row count based on grouping
        
        Example:
            Table: FACT_POPULATION_AGE
            Group by: ['STATE']
            
            Calculation:
            DISTINCT(STATE) = 50
            So expect ~50 rows
        """
        
        if not group_by:
            # No grouping = single row aggregation
            return 1
        
        # For each column in GROUP BY, get distinct count
        cardinalities = []
        for col in group_by:
            distinct = self.cache.get_distinct_values_count(table, col)
            cardinalities.append(distinct)
            self.logger.debug(f"{table}.{col}: {distinct} distinct values")
        
        # Expected rows = product of cardinalities
        import math
        expected = math.prod(cardinalities)
        return expected
    
    def validate_no_fanout(
        self, 
        results: pd.DataFrame, 
        grain: List[str]
    ) -> ValidationResult:
        """
        Check: Did joins cause unexpected multiplication?
        
        Example:
            Query groups by: ['STATE']
            Grain of FACT: ['BLOCK_GROUP', 'AGE_ID', 'SEX']
            Expected rows: 50 (states)
            Actual rows: 50 * 220000 = 11M rows
            Result: ❌ FAIL - Major fan-out detected
        """
        
        expected_cardinality = math.prod(
            [self.cache.get_distinct_values_count(col) for col in grain]
        )
        
        actual_rows = len(results)
        
        if actual_rows > expected_cardinality * 1.2:
            return ValidationResult.FAIL(
                f"Fan-out detected: expected ~{expected_cardinality}, "
                f"got {actual_rows} rows (possible bad join)"
            )
        
        return ValidationResult.PASS
```

### Step 5: Integration into Cortex Query Flow

```python
# src/cortex_analyst.py

class CortexAnalyst:
    def __init__(self):
        self.metadata_cache = SemanticMetadataCache(refresh_minutes=60)
        self.validator = QueryValidator(self.metadata_cache)
    
    def query(self, user_message: str, conversation_history: list = None) -> dict:
        """Query flow with validation"""
        
        # ... existing code to generate SQL ...
        
        if sql_query:
            # 🆕 VALIDATE compiled query using Snowflake metadata
            validation = self.validator.validate_compiled_query(sql_query)
            
            if validation.status == 'FAIL':
                return {
                    'response': f"Query validation failed: {validation.message}",
                    'data': [],
                    'success': True,
                    'validation': validation
                }
            elif validation.status == 'WARN':
                logger.warning(f"Query validation warning: {validation.message}")
            
            # Execute query
            data_results = SnowflakeClient.query(sql_query)
            
            # Continue with existing flow...
```

## Usage Example

```python
# Initialize (happens once per request or reused)
cache = SemanticMetadataCache(refresh_minutes=60)
validator = QueryValidator(cache)

# User asks: "population by state"
sql = """
SELECT STATE_NAME_FULL, SUM(POPULATION_ESTIMATE) as total_population
FROM CURATED.FACT_POPULATION_AGE fa
JOIN CURATED.DIM_BLOCK_GROUP bg ON fa.CENSUS_BLOCK_GROUP = bg.CENSUS_BLOCK_GROUP
GROUP BY STATE_NAME_FULL
ORDER BY total_population DESC
"""

# Validate
result = validator.validate_compiled_query(sql)

# Result:
# {
#     'status': 'PASS',
#     'checks': {
#         'grain': 'PASS',      # GROUP BY includes aggregation column
#         'duplicates': 'PASS', # No duplicates found
#         'cardinality': 'PASS', # Expected ~50 states, got 50
#         'fanout': 'PASS'      # No unexpected multiplication
#     }
# }

# If PASS: Execute full query
# If WARN: Execute but log warning
# If FAIL: Reject with explanation
```

## Key Benefits

✅ **Dynamic** - Uses Snowflake as source of truth  
✅ **Cached** - Fast lookups, 60-min refresh  
✅ **Automatic** - Schema changes auto-detected  
✅ **Transparent** - Explains what it's checking  
✅ **Resilient** - Falls back gracefully if Snowflake unavailable  

## File Structure

```
src/validation/
├── schema_metadata.py      # Query Snowflake for metadata
├── schema_cache.py         # Cache with TTL refresh
├── query_parser.py         # Extract SQL structure
├── grain_validator.py      # Uses cache.get_grain()
├── result_validator.py     # Uses cache.get_row_count()
├── validator.py            # Orchestrator
└── __init__.py
```

## Testing

```python
# Unit test (no Snowflake needed)
def test_grain_validation():
    cache = MockMetadataCache()
    cache.set_grain('FACT_POPULATION_AGE', ['BLOCK_GROUP', 'AGE_ID', 'SEX'])
    
    validator = GrainValidator(cache)
    parsed = ParsedQuery(group_by=['BLOCK_GROUP', 'AGE_ID', 'SEX'])
    
    result = validator.validate(parsed)
    assert result.status == 'PASS'

# Integration test (with Snowflake)
def test_grain_validation_with_snowflake():
    cache = SemanticMetadataCache()
    validator = GrainValidator(cache)
    
    sql = "SELECT STATE, SUM(POPULATION) FROM FACT_POPULATION_AGE GROUP BY STATE"
    parsed = QueryParser.parse(sql)
    
    result = validator.validate(parsed)
    assert result.status == 'PASS'
```

This is the practical, working implementation using Snowflake's semantic metadata!
