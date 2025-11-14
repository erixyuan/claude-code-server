"""
Tests for SessionManager.
"""

import pytest
from claude_code_server import SessionManager, InMemorySessionStore
from claude_code_server.exceptions import SessionNotFoundError


def test_create_session():
    """Test session creation."""
    manager = SessionManager()
    session = manager.create_session("test_001", user_id="user_123")

    assert session.session_id == "test_001"
    assert session.user_id == "user_123"
    assert len(session.conversation_history) == 0


def test_get_session():
    """Test retrieving existing session."""
    manager = SessionManager()
    manager.create_session("test_001")

    session = manager.get_session("test_001")
    assert session.session_id == "test_001"


def test_get_nonexistent_session():
    """Test error when getting nonexistent session."""
    manager = SessionManager()

    with pytest.raises(SessionNotFoundError):
        manager.get_session("nonexistent")


def test_get_or_create_session():
    """Test get_or_create_session behavior."""
    manager = SessionManager()

    # Should create new session
    session1 = manager.get_or_create_session("test_001")
    assert session1.session_id == "test_001"

    # Should return existing session
    session2 = manager.get_or_create_session("test_001")
    assert session2.session_id == "test_001"


def test_add_message():
    """Test adding messages to session."""
    manager = SessionManager()
    manager.create_session("test_001")

    # Add user message
    manager.add_message("test_001", "user", "Hello")
    session = manager.get_session("test_001")
    assert len(session.conversation_history) == 1
    assert session.conversation_history[0].role == "user"
    assert session.conversation_history[0].content == "Hello"

    # Add assistant message
    manager.add_message("test_001", "assistant", "Hi there!")
    session = manager.get_session("test_001")
    assert len(session.conversation_history) == 2


def test_conversation_history():
    """Test getting conversation history."""
    manager = SessionManager()
    manager.create_session("test_001")

    manager.add_message("test_001", "user", "Message 1")
    manager.add_message("test_001", "assistant", "Reply 1")
    manager.add_message("test_001", "user", "Message 2")

    history = manager.get_conversation_history("test_001")
    assert len(history) == 3
    assert history[0].content == "Message 1"
    assert history[1].content == "Reply 1"
    assert history[2].content == "Message 2"


def test_delete_session():
    """Test session deletion."""
    manager = SessionManager()
    manager.create_session("test_001")

    manager.delete_session("test_001")

    with pytest.raises(SessionNotFoundError):
        manager.get_session("test_001")


if __name__ == "__main__":
    # Quick manual test
    print("Running session manager tests...")

    test_create_session()
    print("✓ Create session test passed")

    test_get_session()
    print("✓ Get session test passed")

    test_add_message()
    print("✓ Add message test passed")

    test_conversation_history()
    print("✓ Conversation history test passed")

    print("\nAll session tests passed!")
