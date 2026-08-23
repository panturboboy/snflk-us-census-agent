# RAW Layer

**Purpose**: Direct ingestion from Snowflake Marketplace US Census dataset.

## Characteristics

- **Minimal transformation**: Only rename tables to namespace them (e.g., `census_raw_*`)
- **Original structure preserved**: Columns, data types, nullability as provided by source
- **Read-only access**: Used for traceability and lineage tracking
- **Retention**: Keep indefinitely for audit trail

## Tables in This Layer

Define the original Census tables from Snowflake Marketplace here. These are your source-of-truth snapshots.

**Example structure**:
```
RAW_CENSUS_DATA (or similar)
├── Raw demographics by block group
├── Raw geographies
└── Raw population estimates
```

## Next Step

The CURATED layer will read from these tables and apply transformations.
