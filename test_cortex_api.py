#!/usr/bin/env python3
"""
Test Cortex Analyst API connection

This script validates that:
1. Snowflake connection works
2. Cortex Analyst API is accessible
3. Basic query execution succeeds
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.snowflake_client import SnowflakeClient
from src.config import SnowflakeConfig
from src.cortex_analyst import CortexAnalyst


def test_snowflake_connection():
    """Test basic Snowflake connection"""
    print("\n" + "=" * 70)
    print("TEST 1: Snowflake Connection")
    print("=" * 70)

    try:
        SnowflakeConfig.validate()
        conn = SnowflakeClient.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()

        assert result[0] == 1, "Connection test query failed"
        print("✅ Snowflake connection successful")
        return True

    except Exception as e:
        print(f"❌ Snowflake connection failed: {e}")
        return False


def test_cortex_analyst_initialization():
    """Test Cortex Analyst can be initialized"""
    print("\n" + "=" * 70)
    print("TEST 2: Cortex Analyst Initialization")
    print("=" * 70)

    try:
        validator = CortexAnalyst.get_validator()
        print(f"✅ Cortex Analyst initialized (validator={'available' if validator else 'not available'})")
        return True

    except Exception as e:
        print(f"❌ Cortex Analyst initialization failed: {e}")
        return False


def test_cortex_analyst_query():
    """Test basic Cortex Analyst query"""
    print("\n" + "=" * 70)
    print("TEST 3: Cortex Analyst Query Execution")
    print("=" * 70)

    try:
        prompt = "What is the total population of California?"
        print(f"Query: {prompt}")

        result = CortexAnalyst.query(prompt)

        assert result is not None, "Query returned None"
        assert result['success'] is True, f"Query failed: {result.get('error')}"
        assert len(result.get('response', '')) > 0, "Response is empty"

        row_count = len(result.get('data', []))
        print(f"✅ Query executed successfully")
        print(f"   Response length: {len(result['response'])} chars")
        print(f"   Data rows: {row_count}")

        return True

    except Exception as e:
        print(f"❌ Cortex Analyst query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CORTEX ANALYST API CONNECTION TESTS")
    print("=" * 70)

    tests = [
        ("Snowflake Connection", test_snowflake_connection),
        ("Cortex Analyst Initialization", test_cortex_analyst_initialization),
        ("Cortex Analyst Query", test_cortex_analyst_query),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} passed")
    print("=" * 70 + "\n")

    return 0 if passed_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())
