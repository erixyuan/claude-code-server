#!/usr/bin/env python3
"""
Basic test script to verify Claude Code Server functionality.
Run this without dependencies to test core functionality.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from claude_code_server import (
    ClaudeCodeClient,
    ClaudeConfig,
    OutputFormat,
    PermissionMode,
    SessionManager,
)


def test_version():
    """Test 1: Get Claude version."""
    print("Test 1: Getting Claude CLI version...")
    try:
        client = ClaudeCodeClient()
        version = client.get_version()
        print(f"  ✓ Claude version: {version}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_simple_chat():
    """Test 2: Simple chat without session."""
    print("\nTest 2: Simple chat (no session)...")
    try:
        client = ClaudeCodeClient(
            config=ClaudeConfig(
                output_format=OutputFormat.JSON,
                permission_mode=PermissionMode.BYPASS_PERMISSIONS,
                timeout=30,
            )
        )

        response = client.chat("Say 'Hello from Claude Code Server' and nothing else.")
        print(f"  ✓ Response received: {response.content[:100]}...")
        print(f"  ✓ Success: {response.success}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_chat():
    """Test 3: Multi-turn conversation with session."""
    print("\nTest 3: Multi-turn conversation with session...")
    try:
        client = ClaudeCodeClient(
            config=ClaudeConfig(
                output_format=OutputFormat.JSON,
                permission_mode=PermissionMode.BYPASS_PERMISSIONS,
                timeout=30,
            )
        )

        session_id = "test_basic_session"

        # First turn
        print("  → Turn 1: Telling Claude to remember a number...")
        response1 = client.chat(
            "Remember this number: 12345. Just respond with 'OK, remembered'.",
            session_id=session_id,
        )
        print(f"  ← Claude: {response1.content[:100]}")

        # Second turn
        print("  → Turn 2: Asking Claude to recall the number...")
        response2 = client.chat(
            "What number did I ask you to remember? Reply with just the number.",
            session_id=session_id,
        )
        print(f"  ← Claude: {response2.content[:100]}")

        if "12345" in response2.content:
            print("  ✓ Session memory works! Claude remembered the number.")
            return True
        else:
            print("  ✗ Session memory failed. Claude didn't remember.")
            return False

    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_manager():
    """Test 4: Session manager."""
    print("\nTest 4: Testing SessionManager...")
    try:
        manager = SessionManager()

        # Create session
        session = manager.create_session("test_session", user_id="user_123")
        print(f"  ✓ Session created: {session.session_id}")

        # Add messages
        manager.add_message("test_session", "user", "Hello")
        manager.add_message("test_session", "assistant", "Hi there!")

        # Get history
        history = manager.get_conversation_history("test_session")
        print(f"  ✓ History has {len(history)} messages")

        # Verify content
        assert history[0].content == "Hello"
        assert history[1].content == "Hi there!"
        print("  ✓ Message history correct")

        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Claude Code Server - Basic Functionality Tests")
    print("=" * 60)

    results = []

    results.append(("Version Check", test_version()))
    results.append(("Simple Chat", test_simple_chat()))
    results.append(("Session Chat", test_session_chat()))
    results.append(("Session Manager", test_session_manager()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
