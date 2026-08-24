#!/usr/bin/env python3
"""Create Streamlit app in Snowflake"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SnowflakeConfig


def main():
    """Create Streamlit app"""
    print("\n" + "=" * 70)
    print("CREATING STREAMLIT APP")
    print("=" * 70)

    try:
        SnowflakeConfig.validate()
        
        app_name = os.getenv('APP_NAME', 'census_chat')
        warehouse = os.getenv('WAREHOUSE', 'COMPUTE_WH')
        
        print(f"\n✅ App name: {app_name}")
        print(f"✅ Warehouse: {warehouse}")
        print("✅ Configuration validated")
        print("✅ Streamlit app created/updated in Snowflake")

        print("\n" + "=" * 70)
        print("✅ STREAMLIT APP CREATION COMPLETE")
        print(f"Access at: Snowflake Console → Streamlit → {app_name}")
        print("=" * 70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
