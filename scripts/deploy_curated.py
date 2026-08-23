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

    # Split statements and filter out empty/comment-only ones
    statements = []
    for s in sql.split(';'):
        s = s.strip()
        if s and not s.startswith('--'):
            statements.append(s)

    for i, stmt in enumerate(statements, 1):
        try:
            SnowflakeClient.query(stmt)
            # Extract object name from CREATE statement
            parts = stmt.upper().split()
            if 'TABLE' in parts or 'VIEW' in parts:
                idx = max(
                    parts.index('TABLE') if 'TABLE' in parts else -1,
                    parts.index('VIEW') if 'VIEW' in parts else -1
                )
                name = parts[idx + 1] if idx >= 0 and idx + 1 < len(parts) else f'statement {i}'
            else:
                name = f'statement {i}'
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ Error: {str(e)[:150]}")
            return False

    print("\n✓ Curated layer deployed successfully")
    return True

if __name__ == "__main__":
    success = deploy_curated()
    sys.exit(0 if success else 1)
