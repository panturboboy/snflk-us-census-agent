# SEMANTIC Layer

**Purpose**: Business-optimized, query-efficient tables designed specifically for LLM agent use.

## Characteristics

- **Agent-optimized**: Tables are structured to make SQL generation straightforward and reliable
- **Pre-aggregated**: Common queries are pre-computed to reduce complexity
- **Lookup tables**: Geography, age groups, reference data normalized for fast joins
- **Predictable cost**: Queries are simple, bounded, and efficient
- **Clear semantics**: Column names match business terminology (no confusing abbreviations)

## Design for LLM Agent

The agent needs to:
1. **Understand available data quickly**: Simple schema, clear naming
2. **Generate reliable SQL**: Predictable patterns, minimal edge cases
3. **Return results fast**: Pre-aggregated views where possible
4. **Handle ambiguity gracefully**: Reference tables for standardization

## Recommended Tables

### Core Fact Tables
- **DEMOGRAPHICS_FACTS**: Pre-aggregated population by geography + age + sex
  - Columns: BLOCK_GROUP, AGE_GROUP, SEX, POPULATION_ESTIMATE, MARGIN_OF_ERROR
  - Granularity: Block group × age group × sex

### Lookup Tables
- **GEO_REFERENCE**: Block group hierarchies and metadata
  - Columns: BLOCK_GROUP, STATE, COUNTY, TRACT, NAME, COORDINATES
  
- **AGE_REFERENCE**: Age group standardization
  - Columns: AGE_ID, AGE_CODE, AGE_GROUP_NAME, AGE_RANGE_START, AGE_RANGE_END

## Materialization Strategy

- **Fact tables**: Materialized tables (updated daily/weekly)
- **Lookup tables**: Small reference tables (static or rarely updated)
- **Views**: Optional: Pre-filtered views for common queries (e.g., recent data only)

## Agent Query Patterns

The agent will typically generate:
```sql
SELECT AGE_GROUP, SUM(POPULATION_ESTIMATE) AS total_pop
FROM DEMOGRAPHICS_FACTS
WHERE BLOCK_GROUP IN (...)
GROUP BY AGE_GROUP
ORDER BY total_pop DESC
```

**Goal**: Make this the simplest, most reliable pattern possible.

---

**Note**: Add columns to semantic tables if they make common queries simpler.
