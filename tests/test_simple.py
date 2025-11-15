#!/usr/bin/env python3
"""
Test SimpleAgent - No --resume, avoids cache_control limit.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from claude_code_server import SimpleAgent, ClaudeConfig, OutputFormat


def main():
    print("=" * 60)
    print("SimpleAgent Test - No --resume")
    print("=" * 60)

    agent = SimpleAgent(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            timeout=30,
        ),
        max_history_length=5,  # Keep last 5 turns
    )

    user_id = "test_user"

    print("\n[1] First message")
    r1 = agent.chat("My favorite number is 42", user_id=user_id)
    print(f"✓ Claude: {r1.content[:100]}")

    print("\n[2] Second message - should remember context")
    r2 = agent.chat("What's my favorite number?", user_id=user_id)
    print(f"✓ Claude: {r2.content[:100]}")

    if "42" in r2.content:
        print("\n✅ Context remembered! (via history in prompt)")
    else:
        print("\n⚠️  Context not found in response")

    # Show history
    print("\n" + "=" * 60)
    print("Conversation History:")
    print("=" * 60)
    history = agent.get_conversation_history(user_id)
    for i, msg in enumerate(history, 1):
        print(f"{i}. {msg.role.upper()}: {msg.content[:60]}...")

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
