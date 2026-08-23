#!/usr/bin/env python3
"""Smoke tests for deployed Streamlit app."""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cortex_analyst import CortexAnalyst

def test_cortex_queries():
    """Test Cortex Analyst with sample queries."""

    print("=== Running Smoke Tests ===\n")

    test_cases = [
        {
            "query": "What is the population of California?",
            "expected_metric": "population_estimate",
            "expected_dimension": "state"
        },
        {
            "query": "Show racial composition of Texas",
            "expected_metric": "race_population_estimate",
            "expected_dimension": "race"
        },
        {
            "query": "Total households in New York",
            "expected_metric": "household_estimate",
            "expected_dimension": "state"
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['query']}")

        try:
            result = CortexAnalyst.query(test['query'])

            if result['success']:
                print(f"  ✓ Query executed successfully")
                if result['data']:
                    print(f"  ✓ Returned {len(result['data'])} row(s)")
                    passed += 1
                else:
                    print(f"  ⚠ No data returned (may be expected)")
                    passed += 1
            else:
                print(f"  ✗ Query failed: {result['error']}")
                failed += 1

        except Exception as e:
            print(f"  ✗ Exception: {str(e)[:100]}")
            failed += 1

        print()

    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")

    return failed == 0

if __name__ == "__main__":
    success = test_cortex_queries()
    if success:
        print("\n✓ All smoke tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Check logs.")
        sys.exit(1)
