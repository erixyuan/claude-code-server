"""
High-level agent that combines ClaudeCodeClient with SessionManager.

This provides a simplified API that handles session management automatically.
"""

from typing import Optional, Callable
from .client import ClaudeCodeClient
from .session import SessionManager, SessionStore
from .types import ClaudeConfig, ClaudeResponse


class ClaudeAgent:
    """
    High-level agent that manages Claude Code interactions with automatic session handling.

    This class combines ClaudeCodeClient and SessionManager to provide a simple API
    that automatically handles Claude's UUID session IDs.

    Example:
        >>> agent = ClaudeAgent()
        >>> # First message
        >>> response = agent.chat("Hello!", user_id="alice")
        >>> # Second message - automatically remembers context
        >>> response = agent.chat("What did I say?", user_id="alice")
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        session_store: Optional[SessionStore] = None,
        message_formatter: Optional[Callable[[str, str, Optional[dict]], str]] = None,
    ):
        """
        Initialize Claude Agent.

        Args:
            config: Configuration for Claude CLI
            session_store: Storage backend for sessions (defaults to InMemory)
            message_formatter: Optional function to format messages before sending to Claude.
                             Signature: (message: str, user_id: str, metadata: dict) -> str
                             Example: lambda msg, uid, meta: f"User {uid}: {msg}"
        """
        self.client = ClaudeCodeClient(config=config)
        self.session_manager = SessionManager(store=session_store)
        self.message_formatter = message_formatter

    def chat(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        config_override: Optional[ClaudeConfig] = None,
        metadata: Optional[dict] = None,
    ) -> ClaudeResponse:
        """
        Send a message to Claude with automatic session management.

        Args:
            message: The message to send
            user_id: User identifier (used for session tracking)
            session_id: Optional custom session ID (defaults to user_id)
            config_override: Override default config for this request
            metadata: Optional metadata for message formatting (e.g., {"source": "imessage"})

        Returns:
            ClaudeResponse containing the response and metadata
        """
        # Use user_id as session_id if not provided
        session_id = session_id or f"user_{user_id}"

        # Get or create session
        session = self.session_manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
        )

        # Format message if formatter is provided
        formatted_message = message
        if self.message_formatter:
            formatted_message = self.message_formatter(message, user_id, metadata or {})

        # Get Claude's UUID session ID from previous conversation (if any)
        claude_session_id = session.claude_session_id

        # Send formatted message to Claude
        response = self.client.chat(
            message=formatted_message,
            session_id=session_id,  # User's session ID (for reference)
            claude_session_id=claude_session_id,  # Claude's UUID session ID
            config_override=config_override,
        )

        # Extract and save Claude's session ID from response
        if "claude_session_id" in response.metadata:
            new_claude_session_id = response.metadata["claude_session_id"]
            if new_claude_session_id:
                self.session_manager.update_claude_session_id(
                    session_id, new_claude_session_id
                )

        # Save messages to history
        self.session_manager.add_message(session_id, "user", message)
        self.session_manager.add_message(session_id, "assistant", response.content)

        return response

    def get_conversation_history(self, user_id: str, session_id: Optional[str] = None):
        """
        Get conversation history for a user.

        Args:
            user_id: User identifier
            session_id: Optional session ID (defaults to user_id)

        Returns:
            List of messages in the conversation
        """
        session_id = session_id or f"user_{user_id}"
        return self.session_manager.get_conversation_history(session_id)

    def clear_session(self, user_id: str, session_id: Optional[str] = None) -> None:
        """
        Clear a user's session.

        Args:
            user_id: User identifier
            session_id: Optional session ID (defaults to user_id)
        """
        session_id = session_id or f"user_{user_id}"
        self.session_manager.delete_session(session_id)
