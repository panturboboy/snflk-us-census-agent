#!/usr/bin/env python3
"""Create or update Streamlit app in Snowflake."""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.snowflake_client import SnowflakeClient

def create_streamlit_app():
    """Create Streamlit app in Snowflake."""

    print("=== Creating Streamlit App in Snowflake ===\n")

    app_name = os.getenv('APP_NAME', 'census_chat_prod')
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'CENSUS_DEV_WH')

    # Ensure ACCOUNTADMIN role
    SnowflakeClient.query("USE ROLE ACCOUNTADMIN")

    create_sql = f"""
    CREATE OR REPLACE STREAMLIT CENSUS_NEIGHBORHOOD_INSIGHTS.PUBLIC.{app_name}
      ROOT_LOCATION = @CENSUS_NEIGHBORHOOD_INSIGHTS.PUBLIC.STREAMLIT_STAGE
      MAIN_FILE = '/streamlit_app.py'
      QUERY_WAREHOUSE = {warehouse}
      COMMENT = 'Interactive Census Demographics Chat - Powered by Cortex Analyst'
    """

    try:
        SnowflakeClient.query(create_sql)
        print(f"✓ Streamlit app created: {app_name}")
        print(f"  Warehouse: {warehouse}")
        print(f"  Root location: @STREAMLIT_STAGE")
        print(f"\n✓ Access the app in Snowflake Console:")
        print(f"  → Streamlit apps → {app_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to create Streamlit app: {e}")
        return False

if __name__ == "__main__":
    success = create_streamlit_app()
    sys.exit(0 if success else 1)
