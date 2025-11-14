"""
Tests for ClaudeCodeClient.
"""

import pytest
from claude_code_server import ClaudeCodeClient, ClaudeConfig, OutputFormat, PermissionMode
from claude_code_server.exceptions import ClaudeExecutionError, InvalidConfigError


def test_client_initialization():
    """Test client can be initialized."""
    client = ClaudeCodeClient()
    assert client is not None
    assert client.config is not None


def test_get_version():
    """Test getting Claude CLI version."""
    client = ClaudeCodeClient()
    version = client.get_version()
    assert version
    assert "Claude Code" in version or "claude" in version.lower()


def test_simple_chat():
    """Test simple chat interaction."""
    client = ClaudeCodeClient(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            permission_mode=PermissionMode.DENY_ALL,  # Don't allow any tool usage
            timeout=30,
        )
    )

    response = client.chat("Say 'Hello World' and nothing else.")
    assert response.success
    assert response.content
    assert "hello" in response.content.lower()


def test_chat_with_session():
    """Test multi-turn conversation with session."""
    client = ClaudeCodeClient(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            permission_mode=PermissionMode.DENY_ALL,
        )
    )

    # First message
    session_id = "test_session_001"
    response1 = client.chat(
        "Remember this number: 42. Just respond 'OK'.",
        session_id=session_id,
    )
    assert response1.success

    # Second message - should remember the number
    response2 = client.chat(
        "What number did I tell you to remember?",
        session_id=session_id,
    )
    assert response2.success
    assert "42" in response2.content


def test_invalid_claude_bin():
    """Test error handling for invalid Claude binary."""
    with pytest.raises(InvalidConfigError):
        client = ClaudeCodeClient(claude_bin="/nonexistent/claude")


def test_custom_config():
    """Test custom configuration."""
    config = ClaudeConfig(
        output_format=OutputFormat.TEXT,
        permission_mode=PermissionMode.ACCEPT_EDITS,
        timeout=60,
        allowed_tools=["Read", "Grep"],
    )

    client = ClaudeCodeClient(config=config)
    assert client.config.timeout == 60
    assert client.config.allowed_tools == ["Read", "Grep"]


if __name__ == "__main__":
    # Quick manual test
    print("Running quick manual test...")
    test_get_version()
    print("✓ Version test passed")

    test_simple_chat()
    print("✓ Simple chat test passed")

    test_chat_with_session()
    print("✓ Session test passed")

    print("\nAll tests passed!")
