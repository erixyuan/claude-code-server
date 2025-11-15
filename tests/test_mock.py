#!/usr/bin/env python3
"""
Mock test to understand the session flow.
"""

import json

# Simulate first response (from user's output)
first_response_json = {
    'type': 'result',
    'subtype': 'success',
    'is_error': False,
    'duration_ms': 3248,
    'duration_api_ms': 8000,
    'num_turns': 1,
    'result': '42',
    'session_id': '894eaf27-80f8-4404-b6fa-c7f5e8a1c9d3',  # UUID from user's output
}

print("Simulating first response parsing:")
print(f"JSON session_id: {first_response_json.get('session_id')}")

# Extract result (what our code does)
result_field = first_response_json.get('result')
print(f"Result field: {result_field}")

# What metadata we save
metadata = {
    **first_response_json,
    "claude_session_id": first_response_json.get("session_id"),
}
print(f"Saved claude_session_id: {metadata['claude_session_id']}")

# Second call - what command would we build?
print("\nSecond call command would be:")
print(f"claude -p 'What number...' --output-format json --resume {metadata['claude_session_id']}")

print("\n✓ The UUID format looks correct!")
print("  If this still fails, the error stderr should tell us why.")
