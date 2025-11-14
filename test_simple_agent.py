#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from claude_code_server import ClaudeAgent

agent = ClaudeAgent()

print("Test 1: First message")
r1 = agent.chat("Say only the number 42", user_id="test")
print(f"✓ Response: {r1.content}")

print("\nTest 2: Second message (with retry fallback)")
r2 = agent.chat("What number did you say?", user_id="test")
print(f"✓ Response: {r2.content}")

print("\n✅ Test completed!")
