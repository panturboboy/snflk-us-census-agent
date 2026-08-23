# Snowflake Semantic Layer Contract Properties

## Question: Can we use Snowflake's semantic model as the source of truth?

**Short Answer:** YES - Snowflake provides metadata through:
1. INFORMATION_SCHEMA views
2. Semantic View introspection
3. Cortex Analyst model definitions

## What Snowflake Exposes

### 1. **INFORMATION_SCHEMA** (Standard SQL Views)

```sql
-- Get semantic view definition
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_MODELS
WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';

-- Get tables in semantic model
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_TABLES
WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';

-- Get dimensions defined
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_DIMENSIONS
WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';

-- Get metrics defined
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_METRICS
WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';

-- Get relationships
SELECT * FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_RELATIONSHIPS
WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
```

### 2. **Table Metadata**

```sql
-- Get primary key definition for fact tables
SELECT 
    TABLE_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'CURATED'
AND CONSTRAINT_TYPE = 'PRIMARY KEY';

-- Get column data types
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'CURATED';

-- Get row count (approximate)
SELECT 
    TABLE_NAME,
    ROW_COUNT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'CURATED';
```

### 3. **Dynamic Schema Discovery**

```python
# Instead of hard-coded SCHEMA_REGISTRY, query Snowflake

from src.snowflake_client import SnowflakeClient

class SemanticMetadataProvider:
    """Query Snowflake's semantic model for contract properties"""
    
    def get_semantic_model_schema(self):
        """Fetch semantic model definition from Snowflake"""
        query = """
        SELECT 
            SEMANTIC_MODEL_NAME,
            COLUMN_NAME,
            COLUMN_ROLE  -- 'DIMENSION' or 'METRIC'
        FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_COLUMNS
        WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL'
        ORDER BY SEMANTIC_MODEL_NAME, COLUMN_NAME;
        """
        return SnowflakeClient.query(query)
    
    def get_fact_table_grain(self, table_name: str) -> List[str]:
        """Get grain (primary key) for a fact table"""
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
        """Get approximate row count from stats"""
        query = f"""
        SELECT ROW_COUNT
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = '{table_name}'
        AND TABLE_SCHEMA = 'CURATED';
        """
        result = SnowflakeClient.query(query)
        return result[0]['ROW_COUNT'] if result else None
    
    def get_dimension_values(self, dimension_name: str) -> List[str]:
        """Get available values for a dimension"""
        # Example: Get all available states
        query = f"""
        SELECT DISTINCT STATE_NAME_FULL
        FROM CURATED.DIM_BLOCK_GROUP
        ORDER BY STATE_NAME_FULL;
        """
        results = SnowflakeClient.query(query)
        return [row['STATE_NAME_FULL'] for row in results]
    
    def get_relationships(self) -> Dict:
        """Get relationship definitions from semantic model"""
        query = """
        SELECT 
            RELATIONSHIP_NAME,
            FROM_TABLE,
            TO_TABLE,
            FROM_COLUMN,
            TO_COLUMN
        FROM INFORMATION_SCHEMA.SEMANTIC_MODEL_RELATIONSHIPS
        WHERE SEMANTIC_MODEL_NAME = 'CENSUS_DEMOGRAPHICS_MODEL';
        """
        return SnowflakeClient.query(query)
```

## Benefits of Dynamic Schema Discovery

| Approach | Pros | Cons |
|----------|------|------|
| **Hard-coded Registry** | Fast, no DB calls, simple logic | Maintenance burden, prone to drift, brittleness |
| **Dynamic from Snowflake** | 🎯 Single source of truth, self-documenting, auto-updates | Slower (DB queries), cache invalidation |
| **Hybrid (Cache + Refresh)** | 🏆 Best of both, performance + accuracy | Complexity, cache staleness |

## Recommended: Hybrid Approach

```python
class SemanticMetadataCache:
    """Cache semantic metadata with periodic refresh"""
    
    def __init__(self, refresh_interval_minutes=60):
        self.metadata = {}
        self.last_refresh = None
        self.refresh_interval = refresh_interval_minutes
    
    def get_grain(self, table_name: str) -> List[str]:
        """Get cached grain, refresh if needed"""
        if self._needs_refresh():
            self._refresh_cache()
        return self.metadata.get(table_name, {}).get('grain', [])
    
    def _refresh_cache(self):
        """Query Snowflake for latest metadata"""
        provider = SemanticMetadataProvider()
        self.metadata = {
            'FACT_POPULATION_AGE': {
                'grain': provider.get_fact_table_grain('FACT_POPULATION_AGE'),
                'row_count': provider.get_table_row_count('FACT_POPULATION_AGE'),
            },
            'FACT_RACE_ETHNICITY': {
                'grain': provider.get_fact_table_grain('FACT_RACE_ETHNICITY'),
                'row_count': provider.get_table_row_count('FACT_RACE_ETHNICITY'),
            },
            # ... etc
        }
        self.last_refresh = datetime.now()
    
    def _needs_refresh(self) -> bool:
        """Check if cache is stale"""
        if not self.last_refresh:
            return True
        age = (datetime.now() - self.last_refresh).total_seconds() / 60
        return age > self.refresh_interval
```

## What Snowflake Semantic Layer Provides

### ✅ Available Through INFORMATION_SCHEMA

```python
# Grain definition (primary keys)
grain = get_fact_table_grain('FACT_POPULATION_AGE')
# → ['CENSUS_BLOCK_GROUP', 'AGE_ID', 'SEX']

# Relationships
relationships = get_relationships()
# → [
#     {'from': 'population_age.AGE_ID', 'to': 'age.AGE_ID'},
#     {'from': 'population_age.CENSUS_BLOCK_GROUP', 'to': 'block_group.BLOCK_GROUP'}
#   ]

# Dimensions (from semantic model)
dimensions = get_semantic_dimensions()
# → ['state', 'age_group', 'race', 'household_type']

# Metrics (from semantic model)
metrics = get_semantic_metrics()
# → ['population_estimate', 'margin_of_error', 'household_count']

# Row counts (approximate, from stats)
row_count = get_table_row_count('FACT_POPULATION_AGE')
# → 10487832
```

### ✅ Available Through Cortex Analyst API

```python
# Cortex knows the semantic model structure
# When generating SQL, it understands:
# - What dimensions are available
# - What metrics can be aggregated
# - How tables are related
# - Expected aggregation levels

# We can potentially:
# 1. Ask Cortex what it "knows" about the model
# 2. Extract metadata from the SQL it generates
# 3. Validate against what Snowflake metadata says
```

### ❌ NOT Directly Available (Would need to infer)

```python
# Expected cardinality (how many distinct values)
# - Can calculate dynamically: SELECT COUNT(DISTINCT STATE) FROM DIM_BLOCK_GROUP
# - But requires execution

# Data quality metrics (duplicates, nulls, etc)
# - Need to scan actual data
# - Not in semantic model definition

# Fan-out relationships
# - Inferred from JOIN logic
# - Not explicitly defined in metadata
```

## Revised Validation Architecture

```python
# OLD: Hard-coded SCHEMA_REGISTRY
# NEW: Dynamic + Cached approach

class ValidationValidator:
    def __init__(self):
        self.metadata_cache = SemanticMetadataCache(refresh_interval_minutes=60)
    
    def validate_grain(self, sql: str) -> ValidationResult:
        """
        Instead of checking hard-coded grain,
        query Snowflake for actual grain definition
        """
        # Parse SQL to find tables
        tables = QueryParser().extract_tables(sql)
        
        # For each table, get grain from Snowflake
        for table in tables:
            actual_grain = self.metadata_cache.get_grain(table)
            
            # Check if GROUP BY matches
            group_by = QueryParser().extract_group_by(sql)
            
            if self._grain_matches(actual_grain, group_by):
                return ValidationResult.PASS
            else:
                return ValidationResult.FAIL(f'Grain mismatch for {table}')
    
    def validate_fanout(self, results: pd.DataFrame, sql: str) -> ValidationResult:
        """
        Get expected cardinality from Snowflake,
        compare to actual results
        """
        tables = QueryParser().extract_tables(sql)
        group_by = QueryParser().extract_group_by(sql)
        
        # Calculate expected cardinality from Snowflake
        expected = self._calculate_expected_cardinality_from_snowflake(
            tables, group_by
        )
        
        actual = len(results)
        
        if actual > expected * 1.1:
            return ValidationResult.WARN(f'Possible fan-out')
        return ValidationResult.PASS
```

## Implementation Plan

### Phase 1: Hybrid Approach
- Start with cache (fast)
- Query Snowflake on first use
- Refresh every 60 minutes
- Falls back to hard-coded defaults if Snowflake unavailable

### Phase 2: Full Dynamic
- Remove hard-coded registry entirely
- All metadata from Snowflake
- Better maintainability
- Single source of truth

### Phase 3: Cortex Integration
- Ask Cortex about its semantic understanding
- Cross-validate Cortex's SQL against Snowflake metadata
- Detect discrepancies

## Recommended: Start with Phase 1

**Why?**
1. ✅ Performance (cached lookups)
2. ✅ Reliability (fallback to hard-coded)
3. ✅ Maintainability (source of truth in Snowflake)
4. ✅ No hard-coded drift

**Implementation:**
```
validation/
├── schema_metadata.py      # SemanticMetadataProvider
├── schema_cache.py         # SemanticMetadataCache
├── grain_validator.py      # Uses cache instead of SCHEMA_REGISTRY
├── result_validator.py
└── validator.py
```

## Questions to Answer

1. **Should we cache?** YES - Performance matters
2. **How often refresh?** 60 minutes (config)
3. **What if Snowflake unavailable?** Fall back to hard-coded
4. **Which queries to use?** Snowflake recommends INFORMATION_SCHEMA
5. **How to handle schema changes?** Cache invalidation on model change

This approach gives you **the best of both**: Snowflake as source of truth, with intelligent caching for performance.
