#!/usr/bin/env python3
"""Test context preservation across multiple turns"""

import os
from dotenv import load_dotenv
from src.cortex_analyst import CortexAnalyst

load_dotenv()

print("=" * 70)
print("Testing Context Preservation")
print("=" * 70)

# Simulate multi-turn conversation
conversation = []

test_conversation = [
    "What is the population of Texas?",
    "What about age breakdown for that state?",
    "Which age group has the most people?",
    "Now show me the same data for California",
]

for i, question in enumerate(test_conversation, 1):
    print(f"\n{'─' * 70}")
    print(f"Turn {i}: {question}")
    print(f"{'─' * 70}")

    # Add user message to conversation
    conversation.append({
        "role": "user",
        "content": question
    })

    # Query with context
    result = CortexAnalyst.query(question, conversation[:-1])

    # Show response
    print(f"Response: {result['response'][:200]}...")

    if result.get('data'):
        print(f"Data rows: {len(result['data'])}")

    # Add assistant response to conversation
    conversation.append({
        "role": "assistant",
        "content": result['response'],
        "data": result.get('data', [])
    })

    print(f"\nContext window size: {len(conversation[:-1])} messages")
    print(f"Cortex will receive last 3: {[msg['content'][:50] + '...' if len(msg['content']) > 50 else msg['content'] for msg in conversation[-3:-1]]}")

print("\n" + "=" * 70)
print("Context Preservation Test Complete")
print("=" * 70)
print(f"\nFinal conversation length: {len(conversation)} messages")
print("\nConversation transcript:")
for i, msg in enumerate(conversation):
    role = msg['role'].upper()
    content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
    print(f"{i+1}. [{role}] {content}")
