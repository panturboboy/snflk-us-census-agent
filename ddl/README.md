# Data Definition Language (DDL) - Layered Architecture

This directory contains SQL definitions for a three-layer data warehouse architecture:

## Architecture Layers

### 1. **RAW** (`./raw/`)
Direct ingestion from Snowflake Marketplace US Census dataset.
- Minimal transformation
- Preserves original structure and naming from source
- Used as the source of truth for auditing and lineage tracking
- **Access pattern**: Internal data pipelines only

### 2. **CURATED** (`./curated/`)
Cleaned, deduplicated, and standardized tables ready for analytics.
- Removes duplicates and nulls
- Standardizes data types and naming conventions
- Adds data quality flags
- **These tables**: Your existing 3 demographic tables
- **Access pattern**: Data analysts, business intelligence

### 3. **SEMANTIC** (`./semantic/`)
Business-optimized, pre-aggregated tables for specific use cases.
- Pre-computed common aggregations
- Denormalized for query performance
- Includes lookup tables for fast joins
- **Access pattern**: LLM agent queries (fast, predictable cost, no complex joins)

## Usage

1. Deploy RAW layer first (one-time ingest)
2. Deploy CURATED layer transformations
3. Deploy SEMANTIC layer views/tables for agent access

## Files

- `raw/`: Source system definitions
- `curated/`: Transformation and staging definitions
- `semantic/`: Agent-optimized table schemas

---

**Note**: Each subdirectory has its own README with layer-specific guidance.
