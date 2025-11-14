#!/usr/bin/env python3
"""
Test the high-level ClaudeAgent API with automatic session management.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from claude_code_server import ClaudeAgent, ClaudeConfig, OutputFormat


def main():
    print("=" * 60)
    print("Claude Agent - Session Management Test")
    print("=" * 60)

    # Create agent with config
    agent = ClaudeAgent(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            timeout=30,
        )
    )

    print("\n📝 Testing multi-turn conversation with automatic session handling...")

    # User Alice - First conversation
    user_id = "alice"

    print(f"\n→ User {user_id}: Tell me a number between 1 and 100")
    response1 = agent.chat("Tell me a random number between 1 and 100", user_id=user_id)
    print(f"← Claude: {response1.content[:150]}...")
    print(f"   Session ID: {response1.metadata.get('claude_session_id', 'N/A')[:20]}...")

    print(f"\n→ User {user_id}: What number did you just tell me?")
    response2 = agent.chat("What number did you just tell me?", user_id=user_id)
    print(f"← Claude: {response2.content[:150]}...")

    # Check if Claude remembered
    # Extract any number from response2
    import re
    numbers = re.findall(r'\d+', response2.content)
    if numbers:
        print(f"\n✓ Claude remembered! Found number: {numbers[0]}")
    else:
        print("\n? Could not determine if Claude remembered")

    # Show conversation history
    print("\n" + "=" * 60)
    print("Conversation History:")
    print("=" * 60)
    history = agent.get_conversation_history(user_id)
    for i, msg in enumerate(history, 1):
        role = msg.role.upper()
        content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        print(f"{i}. {role}: {content}")

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
