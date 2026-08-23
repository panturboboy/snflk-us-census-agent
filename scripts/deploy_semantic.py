#!/usr/bin/env python3
"""Deploy semantic layer to Snowflake."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.snowflake_client import SnowflakeClient

def deploy_semantic():
    """Execute semantic layer DDL."""

    print("=== Deploying Semantic Layer ===\n")

    ddl_file = Path(__file__).parent.parent / "ddl" / "semantic" / "create_semantic_tables.sql"

    with open(ddl_file, 'r') as f:
        sql = f.read()

    try:
        # Semantic views need full SQL execution
        SnowflakeClient.query("USE ROLE ACCOUNTADMIN")
        SnowflakeClient.query(sql)
        print("✓ Semantic model deployed")
    except Exception as e:
        print(f"✗ Error: {str(e)[:150]}")
        return False

    print("\n✓ Semantic layer deployed successfully")
    return True

if __name__ == "__main__":
    success = deploy_semantic()
    sys.exit(0 if success else 1)
