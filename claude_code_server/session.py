"""
Session management for Claude Code conversations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Protocol
from datetime import datetime
import json

from .types import SessionData, ClaudeMessage
from .exceptions import SessionNotFoundError


class SessionStore(Protocol):
    """Protocol for session storage backends."""

    def get(self, session_id: str) -> Optional[SessionData]:
        """Retrieve a session by ID."""
        ...

    def save(self, session: SessionData) -> None:
        """Save a session."""
        ...

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        ...

    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        ...


class InMemorySessionStore:
    """In-memory session storage (for testing/development)."""

    def __init__(self):
        self._store: dict[str, SessionData] = {}

    def get(self, session_id: str) -> Optional[SessionData]:
        return self._store.get(session_id)

    def save(self, session: SessionData) -> None:
        session.last_activity = datetime.now()
        self._store[session.session_id] = session

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        return session_id in self._store

    def list_all(self) -> list[SessionData]:
        """List all sessions (for debugging)."""
        return list(self._store.values())


class RedisSessionStore:
    """Redis-based session storage (for production)."""

    def __init__(self, redis_client, prefix: str = "claude_session:", ttl: Optional[int] = None):
        """
        Initialize Redis session store.

        Args:
            redis_client: Redis client instance
            prefix: Key prefix for session data
            ttl: Time-to-live in seconds (default: None, never expire)
                 Set to None for sessions that never expire
                 Set to a number (e.g., 3600) for sessions that expire after that many seconds
        """
        self.redis = redis_client
        self.prefix = prefix
        self.ttl = ttl

    def _make_key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    def get(self, session_id: str) -> Optional[SessionData]:
        key = self._make_key(session_id)
        data = self.redis.get(key)
        if data:
            return SessionData.model_validate_json(data)
        return None

    def save(self, session: SessionData) -> None:
        session.last_activity = datetime.now()
        key = self._make_key(session.session_id)
        data = session.model_dump_json()

        if self.ttl is None:
            # No expiration - session never expires
            self.redis.set(key, data)
        else:
            # Set expiration time
            self.redis.setex(key, self.ttl, data)

    def delete(self, session_id: str) -> None:
        key = self._make_key(session_id)
        self.redis.delete(key)

    def exists(self, session_id: str) -> bool:
        key = self._make_key(session_id)
        return self.redis.exists(key) > 0


class SessionManager:
    """
    Manages Claude Code conversation sessions.

    Handles session creation, retrieval, and conversation history tracking.
    """

    def __init__(self, store: Optional[SessionStore] = None):
        """
        Initialize session manager.

        Args:
            store: Session storage backend (defaults to InMemorySessionStore)
        """
        self.store = store or InMemorySessionStore()

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> SessionData:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            metadata: Optional metadata dictionary

        Returns:
            Created SessionData object
        """
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        self.store.save(session)
        return session

    def get_session(self, session_id: str) -> SessionData:
        """
        Get an existing session.

        Args:
            session_id: Session identifier

        Returns:
            SessionData object

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = self.store.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return session

    def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> SessionData:
        """
        Get existing session or create new one.

        Args:
            session_id: Session identifier
            user_id: Optional user identifier
            metadata: Optional metadata

        Returns:
            SessionData object
        """
        if self.store.exists(session_id):
            return self.get_session(session_id)
        return self.create_session(session_id, user_id, metadata)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> SessionData:
        """
        Add a message to session history.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            Updated SessionData object
        """
        session = self.get_session(session_id)
        message = ClaudeMessage(role=role, content=content)  # type: ignore
        session.conversation_history.append(message)
        self.store.save(session)
        return session

    def update_claude_session_id(
        self,
        session_id: str,
        claude_session_id: str,
    ) -> SessionData:
        """
        Update the Claude CLI's internal session ID.

        Args:
            session_id: Our session identifier
            claude_session_id: Claude CLI's session identifier

        Returns:
            Updated SessionData object
        """
        session = self.get_session(session_id)
        session.claude_session_id = claude_session_id
        self.store.save(session)
        return session

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        self.store.delete(session_id)

    def get_conversation_history(self, session_id: str) -> list[ClaudeMessage]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of ClaudeMessage objects
        """
        session = self.get_session(session_id)
        return session.conversation_history
