#!/usr/bin/env python3
"""
Multi-turn conversation example - Using sessions to maintain context.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from claude_code_server import ClaudeCodeClient, SessionManager, ClaudeConfig, OutputFormat


def main():
    print("=" * 60)
    print("Claude Code Server - Multi-Turn Conversation Example")
    print("=" * 60)

    # Create client and session manager
    client = ClaudeCodeClient(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            timeout=60,
        )
    )

    session_manager = SessionManager()
    session_id = "example_session_001"

    # Create session
    session = session_manager.create_session(
        session_id=session_id,
        user_id="user_123",
        metadata={"app": "example"},
    )
    print(f"\nCreated session: {session.session_id}")

    # Conversation turns
    conversations = [
        ("user", "My name is Alice and I love Python programming."),
        ("user", "What's my name?"),
        ("user", "What programming language did I mention?"),
    ]

    for role, message in conversations:
        print(f"\n→ User: {message}")

        # Send message with session
        response = client.chat(message, session_id=session_id)

        print(f"← Claude: {response.content[:200]}...")

        # Save to session history
        session_manager.add_message(session_id, "user", message)
        session_manager.add_message(session_id, "assistant", response.content)

    # Show conversation history
    print("\n" + "=" * 60)
    print("Conversation History:")
    print("=" * 60)

    history = session_manager.get_conversation_history(session_id)
    for i, msg in enumerate(history, 1):
        print(f"{i}. {msg.role.upper()}: {msg.content[:100]}...")


if __name__ == "__main__":
    main()
