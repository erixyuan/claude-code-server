#!/usr/bin/env python3
"""
Webhook bot example - How to use claude-code-server in a webhook/chat bot scenario.

This example shows the pattern for integrating with messaging platforms like:
- Feishu/Lark
- Slack
- Discord
- WeChat
etc.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from claude_code_server import ClaudeClient, SessionManager, ClaudeConfig
from typing import Dict


class ChatBot:
    """
    Example chatbot using Claude Code Server.

    This demonstrates the pattern for webhook-based chat applications.
    """

    def __init__(self):
        self.client = ClaudeClient(config=ClaudeConfig(timeout=120))
        self.session_manager = SessionManager()

    def handle_message(self, user_id: str, message: str) -> str:
        """
        Handle incoming message from a user.

        Args:
            user_id: Unique user identifier
            message: User's message

        Returns:
            Claude's response
        """
        # Use user_id as session_id to maintain per-user context
        session_id = f"user_{user_id}"

        # Get or create session
        self.session_manager.get_or_create_session(
            session_id=session_id, user_id=user_id
        )

        # Send to Claude with session context
        response = self.client.chat(message, session_id=session_id)

        # Save to history
        self.session_manager.add_message(session_id, "user", message)
        self.session_manager.add_message(session_id, "assistant", response.content)

        return response.content

    def get_user_history(self, user_id: str) -> list:
        """Get conversation history for a user."""
        session_id = f"user_{user_id}"
        try:
            return self.session_manager.get_conversation_history(session_id)
        except:
            return []


def simulate_webhook():
    """Simulate webhook requests from multiple users."""
    print("=" * 60)
    print("Claude Code Server - Webhook Bot Example")
    print("=" * 60)

    bot = ChatBot()

    # Simulate messages from different users
    messages = [
        ("alice_123", "Hi! My favorite color is blue."),
        ("bob_456", "Hello! I'm a Python developer."),
        ("alice_123", "What's my favorite color?"),  # Should remember
        ("bob_456", "What's my profession?"),  # Should remember
    ]

    for user_id, message in messages:
        print(f"\n[Webhook] User {user_id}: {message}")
        response = bot.handle_message(user_id, message)
        print(f"[Response] → {response[:200]}...")

    # Show histories
    print("\n" + "=" * 60)
    print("User Histories:")
    print("=" * 60)

    for user_id in ["alice_123", "bob_456"]:
        history = bot.get_user_history(user_id)
        print(f"\n{user_id} ({len(history)} messages):")
        for msg in history[:4]:  # Show first 4
            print(f"  {msg.role}: {msg.content[:60]}...")


if __name__ == "__main__":
    simulate_webhook()
