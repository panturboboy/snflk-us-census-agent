#!/usr/bin/env python3
"""Test Cortex Analyst REST API"""

import os
from dotenv import load_dotenv
from src.cortex_analyst import CortexAnalyst

load_dotenv()

print("=== Testing Cortex Analyst REST API ===\n")

# Test query
test_question = "What is the population of California?"

print(f"Question: {test_question}\n")
print("Calling Cortex Analyst API...")

result = CortexAnalyst.query(test_question)

print(f"\nSuccess: {result['success']}")
print(f"Error: {result['error']}")
print(f"\nResponse:")
print(result['response'])
