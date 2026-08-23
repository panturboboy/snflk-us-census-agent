#!/usr/bin/env python3
"""Test context preservation with data summaries"""

import os
from dotenv import load_dotenv
from src.cortex_analyst import CortexAnalyst

load_dotenv()

print("=" * 70)
print("Testing Context with Data Summaries")
print("=" * 70)

# Test 1: Which states are in data
q1 = "which states are in your data"
print(f"\n{'─' * 70}")
print(f"Q1: {q1}")
print(f"{'─' * 70}")
result1 = CortexAnalyst.query(q1, [])
data_count_1 = len(result1.get('data', []))
print(f"Response: {result1['response'][:150]}...")
print(f"Data rows: {data_count_1}")

# Test 2: Rank them (anaphoric reference)
conversation1 = [
    {"role": "user", "content": q1},
    {"role": "assistant", "content": result1['response'], "data": result1.get('data', [])}
]

q2 = "rank them by population from highest to lowest"
print(f"\n{'─' * 70}")
print(f"Q2 (with Q1 context + {data_count_1} rows): {q2}")
print(f"{'─' * 70}")
result2 = CortexAnalyst.query(q2, conversation1)
data_count_2 = len(result2.get('data', []))
print(f"Response: {result2['response'][:150]}...")
print(f"Data rows: {data_count_2}")

# Test 3: Compare top states
conversation2 = conversation1 + [
    {"role": "user", "content": q2},
    {"role": "assistant", "content": result2['response'], "data": result2.get('data', [])}
]

q3 = "Show me top 5 states by population"
print(f"\n{'─' * 70}")
print(f"Q3 (with Q1+Q2 context): {q3}")
print(f"{'─' * 70}")
result3 = CortexAnalyst.query(q3, conversation2)
data_count_3 = len(result3.get('data', []))
print(f"Response: {result3['response'][:150]}...")
print(f"Data rows: {data_count_3}")

# Summary
print(f"\n{'=' * 70}")
print("Test Results:")
print(f"{'=' * 70}")
print(f"Q1 (no context): {data_count_1} rows")
print(f"Q2 (with {data_count_1} rows context): {data_count_2} rows")
print(f"Q3 (with context): {data_count_3} rows")
print()

if data_count_2 > 0 and data_count_3 > 0:
    print("✅ SUCCESS: Multi-turn conversation with data context works!")
else:
    print("⚠️  CHECK: Some queries didn't return data")
