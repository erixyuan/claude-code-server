"""
SimpleAgent - Alternative implementation without sessions.

This agent doesn't use Claude's session feature.
Instead, it manages context by including conversation history in each prompt.
"""

from typing import Optional
from .client import ClaudeClient
from .session import SessionManager, SessionStore
from .types import ClaudeConfig, ClaudeResponse


class SimpleAgent:
    """
    Simple agent that manages context without using sessions.

    This agent includes conversation history directly in the prompt.

    Example:
        >>> agent = SimpleAgent()
        >>> agent.chat("My name is Alice", user_id="alice")
        >>> response = agent.chat("What's my name?", user_id="alice")
        >>> # Context is maintained via history in prompt
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        session_store: Optional[SessionStore] = None,
        max_history_length: int = 10,
    ):
        """
        Initialize Simple Agent.

        Args:
            config: Configuration for Claude SDK
            session_store: Storage backend for sessions
            max_history_length: Maximum number of conversation turns to include
        """
        self.client = ClaudeClient(config=config)
        self.session_manager = SessionManager(store=session_store)
        self.max_history_length = max_history_length

    def chat(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        config_override: Optional[ClaudeConfig] = None,
    ) -> ClaudeResponse:
        """
        Send a message with context from conversation history.

        Args:
            message: The message to send
            user_id: User identifier
            session_id: Optional custom session ID
            config_override: Override default config

        Returns:
            ClaudeResponse
        """
        session_id = session_id or f"user_{user_id}"

        # Get or create session
        session = self.session_manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
        )

        # Build prompt with conversation history
        history = session.conversation_history[-self.max_history_length * 2 :]
        if history:
            # Include previous conversation as context
            context_parts = []
            for msg in history:
                role = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"{role}: {msg.content}")

            full_prompt = (
                "Previous conversation:\n"
                + "\n".join(context_parts)
                + f"\n\nUser: {message}"
            )
        else:
            full_prompt = message

        # Send to Claude (no session, each call is independent)
        response = self.client.chat(
            message=full_prompt,
            claude_session_id=None,  # Don't use session
            config_override=config_override,
        )

        # Save to history
        self.session_manager.add_message(session_id, "user", message)
        self.session_manager.add_message(session_id, "assistant", response.content)

        return response

    def get_conversation_history(self, user_id: str, session_id: Optional[str] = None):
        """Get conversation history for a user."""
        session_id = session_id or f"user_{user_id}"
        return self.session_manager.get_conversation_history(session_id)

    def clear_session(self, user_id: str, session_id: Optional[str] = None) -> None:
        """Clear a user's session."""
        session_id = session_id or f"user_{user_id}"
        self.session_manager.delete_session(session_id)
