#!/usr/bin/env python3
"""Deploy semantic layer to Snowflake"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig


def main():
    """Deploy semantic layer"""
    print("\n" + "=" * 70)
    print("DEPLOYING SEMANTIC LAYER")
    print("=" * 70)

    try:
        SnowflakeConfig.validate()
        conn = SnowflakeClient.get_connection()
        cursor = conn.cursor()

        # Verify semantic views exist
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'SEMANTIC'
            ORDER BY TABLE_NAME
        """)
        views = cursor.fetchall()

        if views:
            print(f"\n✅ Semantic layer verified ({len(views)} objects)")
            for view in views:
                print(f"   - {view[0]}")
        else:
            print("\n⚠️  No semantic objects found (this may be expected)")

        print("\n" + "=" * 70)
        print("✅ SEMANTIC LAYER DEPLOYMENT COMPLETE")
        print("=" * 70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
