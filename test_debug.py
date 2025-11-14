#!/usr/bin/env python3
"""
Debug test to see what's happening with session resumption.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from claude_code_server import ClaudeAgent, ClaudeConfig, OutputFormat


def main():
    print("=" * 60)
    print("Debug Session Test")
    print("=" * 60)

    agent = ClaudeAgent(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            timeout=30,
        )
    )

    user_id = "debug_user"

    # First call
    print("\n[1] First call - No session yet")
    try:
        response1 = agent.chat("Say the number 42", user_id=user_id)
        print(f"✓ Success!")
        print(f"  Content: {response1.content[:100]}")
        print(f"  Claude session ID: {response1.metadata.get('claude_session_id', 'N/A')}")

        # Check what was saved
        session = agent.session_manager.get_session(f"user_{user_id}")
        print(f"  Saved claude_session_id: {session.claude_session_id}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return 1

    # Second call
    print("\n[2] Second call - Should resume with session")
    try:
        response2 = agent.chat("What number did you say?", user_id=user_id)
        print(f"✓ Success!")
        print(f"  Content: {response2.content[:100]}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return 1

    print("\n✅ All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
