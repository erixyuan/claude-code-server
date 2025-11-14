#!/usr/bin/env python3
"""
ClaudeAgent example - The recommended high-level API.

This shows how to use ClaudeAgent for automatic session management.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from claude_code_server import ClaudeAgent, ClaudeConfig, OutputFormat


def main():
    print("=" * 60)
    print("ClaudeAgent Example - Simple Multi-User Chatbot")
    print("=" * 60)

    # Create agent
    agent = ClaudeAgent(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            timeout=60,
        )
    )

    # Simulate two users chatting
    print("\n--- User Alice ---")
    print("Alice: My favorite color is blue")
    response1 = agent.chat("My favorite color is blue", user_id="alice")
    print(f"Claude: {response1.content[:100]}...\n")

    print("--- User Bob ---")
    print("Bob: I love Python programming")
    response2 = agent.chat("I love Python programming", user_id="bob")
    print(f"Claude: {response2.content[:100]}...\n")

    # Second turn - Alice
    print("--- User Alice (2nd message) ---")
    print("Alice: What's my favorite color?")
    response3 = agent.chat("What's my favorite color?", user_id="alice")
    print(f"Claude: {response3.content[:100]}...")
    if "blue" in response3.content.lower():
        print("✓ Claude remembered Alice's context!")

    # Second turn - Bob
    print("\n--- User Bob (2nd message) ---")
    print("Bob: What do I love?")
    response4 = agent.chat("What do I love?", user_id="bob")
    print(f"Claude: {response4.content[:100]}...")
    if "python" in response4.content.lower():
        print("✓ Claude remembered Bob's context!")

    # Show histories
    print("\n" + "=" * 60)
    print("Conversation Histories:")
    print("=" * 60)

    print("\nAlice's history:")
    alice_history = agent.get_conversation_history("alice")
    for msg in alice_history:
        print(f"  {msg.role}: {msg.content[:60]}...")

    print("\nBob's history:")
    bob_history = agent.get_conversation_history("bob")
    for msg in bob_history:
        print(f"  {msg.role}: {msg.content[:60]}...")


if __name__ == "__main__":
    main()
