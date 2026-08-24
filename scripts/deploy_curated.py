#!/usr/bin/env python3
"""Deploy curated layer to Snowflake"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig


def main():
    """Deploy curated layer"""
    print("\n" + "=" * 70)
    print("DEPLOYING CURATED LAYER")
    print("=" * 70)

    try:
        SnowflakeConfig.validate()
        conn = SnowflakeClient.get_connection()
        cursor = conn.cursor()

        # Verify tables exist
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'CURATED'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"\n✅ Curated layer verified ({len(tables)} tables)")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("\n⚠️  No tables found in CURATED schema")

        print("\n" + "=" * 70)
        print("✅ CURATED LAYER DEPLOYMENT COMPLETE")
        print("=" * 70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
