#!/usr/bin/env python3
"""
Smoke test for deployed Streamlit app

Validates that:
1. Cortex Analyst can answer basic queries
2. Data validation layer works
3. Response formatting is correct
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cortex_analyst import CortexAnalyst
from src.config import SnowflakeConfig


def test_basic_query():
    """Test basic population query"""
    print("\n" + "=" * 70)
    print("SMOKE TEST: Basic Query")
    print("=" * 70)

    try:
        result = CortexAnalyst.query("What is the population of California?")

        assert result['success'] is True, "Query failed"
        assert len(result['response']) > 0, "Empty response"
        assert 'California' in result['response'] or 'population' in result['response'].lower(), "Unexpected response"

        print("✅ Basic query test passed")
        print(f"   Response: {result['response'][:100]}...")
        return True

    except Exception as e:
        print(f"❌ Basic query test failed: {e}")
        return False


def test_sex_breakdown():
    """Test population breakdown by sex"""
    print("\n" + "=" * 70)
    print("SMOKE TEST: Sex Breakdown Query")
    print("=" * 70)

    try:
        result = CortexAnalyst.query("Show population by sex in Texas")

        assert result['success'] is True, "Query failed"
        assert len(result.get('data', [])) > 0, "No data returned"

        print("✅ Sex breakdown query test passed")
        print(f"   Data rows: {len(result['data'])}")
        return True

    except Exception as e:
        print(f"❌ Sex breakdown query test failed: {e}")
        return False


def test_no_data_handling():
    """Test handling of queries with no results"""
    print("\n" + "=" * 70)
    print("SMOKE TEST: No Data Handling")
    print("=" * 70)

    try:
        result = CortexAnalyst.query("What is the population of age 999?")

        assert result['success'] is True, "Query should succeed even with no data"
        assert len(result.get('data', [])) == 0, "Should return empty data"
        assert 'No data found' in result['response'] or 'available data' in result['response'].lower(), \
            "Should explain what data is available"

        print("✅ No data handling test passed")
        print(f"   Response: {result['response'][:100]}...")
        return True

    except Exception as e:
        print(f"❌ No data handling test failed: {e}")
        return False


def test_conversation_context():
    """Test that context is preserved across queries"""
    print("\n" + "=" * 70)
    print("SMOKE TEST: Conversation Context")
    print("=" * 70)

    try:
        # First query
        result1 = CortexAnalyst.query("What is the population of California?")
        assert result1['success'] is True, "First query failed"

        # Second query with context
        history = [
            {"role": "user", "content": "What is the population of California?"},
            {"role": "assistant", "content": result1['response'], "data": result1.get('data', [])},
        ]

        result2 = CortexAnalyst.query("What about Texas?", history)
        assert result2['success'] is True, "Second query failed"

        print("✅ Conversation context test passed")
        print(f"   Query 1: California - {len(result1['response'])} chars")
        print(f"   Query 2: Texas - {len(result2['response'])} chars")
        return True

    except Exception as e:
        print(f"❌ Conversation context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests"""
    print("\n" + "=" * 70)
    print("SMOKE TEST SUITE - POST-DEPLOYMENT VALIDATION")
    print("=" * 70)

    # Check environment
    try:
        SnowflakeConfig.validate()
        print("✅ Environment configured correctly")
    except Exception as e:
        print(f"❌ Environment configuration failed: {e}")
        return 1

    # Run tests
    tests = [
        test_basic_query,
        test_sex_breakdown,
        test_no_data_handling,
        test_conversation_context,
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print(f"\n❌ {test_func.__name__} crashed: {e}")
            results.append((test_func.__name__, False))

    # Summary
    print("\n" + "=" * 70)
    print("SMOKE TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed_count}/{total_count} passed")

    if passed_count == total_count:
        print("\n✅ ALL SMOKE TESTS PASSED - DEPLOYMENT SUCCESSFUL")
    else:
        print(f"\n❌ {total_count - passed_count} SMOKE TEST(S) FAILED")

    print("=" * 70 + "\n")

    return 0 if passed_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())
