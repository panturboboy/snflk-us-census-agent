#!/usr/bin/env python3
"""Deploy curated layer DDLs to Snowflake."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.snowflake_client import SnowflakeClient

def deploy_curated():
    """Execute curated layer DDL."""

    print("=== Deploying Curated Layer ===\n")

    ddl_file = Path(__file__).parent.parent / "ddl" / "curated" / "create_curated_tables.sql"

    with open(ddl_file, 'r') as f:
        sql = f.read()

    # Split and execute statements
    statements = [s.strip() for s in sql.split(';') if s.strip()]

    for i, stmt in enumerate(statements, 1):
        try:
            SnowflakeClient.query(stmt)
            name = stmt.split()[-2] if 'TABLE' in stmt or 'VIEW' in stmt else f'statement {i}'
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")
            return False

    print("\n✓ Curated layer deployed successfully")
    return True

if __name__ == "__main__":
    success = deploy_curated()
    sys.exit(0 if success else 1)
