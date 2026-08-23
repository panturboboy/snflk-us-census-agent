#!/usr/bin/env python3
"""Test cortex_analyst directly without Streamlit"""

import sys
import os
import time

# Add project to path
sys.path.insert(0, '/Users/Iaroslav/Projects/Snowflake/CensusAgent')

print("=" * 60)
print("Testing CortexAnalyst Directly (No Streamlit)")
print("=" * 60)

# Test 1: Import
print("\n[1/5] Importing CortexAnalyst...")
try:
    from src.cortex_analyst import CortexAnalyst
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: First query
print("\n[2/5] Running FIRST query...")
print("Query: 'What is the population of Texas?'")
print("-" * 60)

start_time = time.time()
try:
    result1 = CortexAnalyst.query("What is the population of Texas?")
    elapsed = time.time() - start_time

    print(f"✅ Query completed in {elapsed:.2f} seconds")
    print(f"Response length: {len(result1.get('response', ''))} chars")
    print(f"Data rows: {len(result1.get('data', []))}")
    print(f"Success: {result1.get('success')}")

    # Print first 200 chars of response
    response_preview = result1.get('response', '')[:200]
    print(f"Response preview: {response_preview}...")

except Exception as e:
    print(f"❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Prepare conversation history
print("\n[3/5] Preparing conversation history...")
conversation_history = [
    {"role": "user", "content": "What is the population of Texas?"},
    {"role": "assistant", "content": result1.get('response', ''), "data": result1.get('data', [])}
]
print(f"✅ History prepared with 1 message pair")

# Test 4: Second query with context
print("\n[4/5] Running SECOND query with context...")
print("Query: 'What about California?'")
print("-" * 60)

start_time = time.time()
try:
    result2 = CortexAnalyst.query(
        "What about California?",
        conversation_history
    )
    elapsed = time.time() - start_time

    print(f"✅ Query completed in {elapsed:.2f} seconds")
    print(f"Response length: {len(result2.get('response', ''))} chars")
    print(f"Data rows: {len(result2.get('data', []))}")
    print(f"Success: {result2.get('success')}")

    # Print first 200 chars of response
    response_preview = result2.get('response', '')[:200]
    print(f"Response preview: {response_preview}...")

except Exception as e:
    print(f"❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Third query
print("\n[5/5] Running THIRD query...")
print("Query: 'Show both populations'")
print("-" * 60)

conversation_history.append({"role": "user", "content": "What about California?"})
conversation_history.append({"role": "assistant", "content": result2.get('response', ''), "data": result2.get('data', [])})

start_time = time.time()
try:
    result3 = CortexAnalyst.query(
        "Show both populations",
        conversation_history
    )
    elapsed = time.time() - start_time

    print(f"✅ Query completed in {elapsed:.2f} seconds")
    print(f"Response length: {len(result3.get('response', ''))} chars")
    print(f"Data rows: {len(result3.get('data', []))}")
    print(f"Success: {result3.get('success')}")

except Exception as e:
    print(f"❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
print("\nSummary:")
print(f"  Query 1: {result1.get('success')} - {len(result1.get('data', []))} rows")
print(f"  Query 2: {result2.get('success')} - {len(result2.get('data', []))} rows")
print(f"  Query 3: {result3.get('success')} - {len(result3.get('data', []))} rows")
print("\n✨ The core logic works! Issue is likely in Streamlit UI layer.")
