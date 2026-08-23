# CURATED Layer

**Purpose**: Cleaned, deduplicated, and standardized tables ready for analysis and downstream use.

## Characteristics

- **Data quality applied**: Deduplication, null handling, validation
- **Standardized schema**: Consistent naming, data types, and conventions
- **Documented lineage**: Clear mapping to RAW layer sources
- **Quality flags**: Columns to track data completeness, confidence, etc.
- **Incremental updates**: Can be refreshed as source data changes

## Your Existing Tables

This is where your 3 curated demographic tables live:

1. **Demographics by Block Group** (or similar)
   - Age breakdowns (AGE_ID, AGE_CODE)
   - Sex breakdowns (SEX)
   - Estimates and margin of error
   - Census block group geography

2. **[Table 2 Name]**
   - [Schema description]

3. **[Table 3 Name]**
   - [Schema description]

## Design Decisions

- **Block group as primary geography**: Finest granularity available
- **Age/Sex as categorical dimensions**: Supports demographic breakdowns
- **Estimates + margin of error**: Preserves statistical confidence

## Transformation Logic

Document any significant transformations applied to RAW data:
- Null handling strategy
- Data type conversions
- Deduplication keys
- Validation rules applied

---

**Note**: The SEMANTIC layer will further optimize these tables for the LLM agent.
