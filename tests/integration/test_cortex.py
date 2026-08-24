#!/usr/bin/env python3
"""Test Cortex Analyst without Streamlit

This module can be run as a script to validate Cortex Analyst setup:
  python3 tests/integration/test_cortex.py

When imported by pytest, the validation is skipped and the module is empty
to allow the test suite to complete normally.
"""

import os
import sys
from dotenv import load_dotenv


def main():
    """Run Cortex validation checks"""
    # Load .env
    load_dotenv()

    # Test imports
    try:
        from src.snowflake_client import SnowflakeClient
        from src.config import SnowflakeConfig
        print("✓ Imports successful")
    except Exception as e:
        print(f"✗ Import error: {e}")
        sys.exit(1)

    # Validate config
    try:
        SnowflakeConfig.validate()
        print(f"✓ Config valid")
        print(f"  Account: {SnowflakeConfig.ACCOUNT}")
        print(f"  User: {SnowflakeConfig.USER}")
        print(f"  Database: {SnowflakeConfig.DATABASE}")
        print(f"  Warehouse: {SnowflakeConfig.WAREHOUSE}")
    except Exception as e:
        print(f"✗ Config error: {e}")
        sys.exit(1)

    # Test Snowflake connection
    try:
        result = SnowflakeClient.query("SELECT 1 AS test")
        print(f"✓ Snowflake connected: {result}")
    except Exception as e:
        print(f"✗ Connection error: {e}")
        sys.exit(1)

    # Test semantic view exists
    try:
        result = SnowflakeClient.query("""
            SELECT TABLE_NAME, TABLE_SCHEMA
            FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_NAME = 'CENSUS_DEMOGRAPHICS_MODEL'
            AND TABLE_SCHEMA = 'SEMANTIC'
        """)
        if result:
            print(f"✓ Semantic view found: {result[0]}")
        else:
            print(f"✗ Semantic view NOT found")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Query error: {e}")
        sys.exit(1)

    # Test Cortex Analyst
    print("\n--- Testing Cortex Analyst ---")
    try:
        query = "What is the population of California?"
        print(f"Query: {query}")

        sql = f"""
        SELECT SNOWFLAKE.CORTEX.ANALYST(
            'What is the population of California?',
            'CENSUS_NEIGHBORHOOD_INSIGHTS.SEMANTIC.CENSUS_DEMOGRAPHICS_MODEL'
        ) AS response
        """

        result = SnowflakeClient.query(sql)
        if result:
            response = result[0]['RESPONSE']
            print(f"\n✓ Cortex Response:\n{response}")
        else:
            print("✗ No response from Cortex")

    except Exception as e:
        print(f"✗ Cortex error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    main()
