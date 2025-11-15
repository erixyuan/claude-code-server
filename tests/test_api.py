#!/usr/bin/env python3
"""
Test Claude Code Server API.

Run this after starting the server with:
  python start_server.py
"""

import time
import requests

API_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("\n1️⃣  Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    data = response.json()
    print(f"   ✓ Status: {data['status']}")
    print(f"   ✓ Version: {data['version']}")
    print(f"   ✓ Claude: {data.get('claude_version', 'N/A')}")


def test_sync_chat():
    """Test synchronous chat."""
    print("\n2️⃣  Testing /chat (sync mode)...")
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": "Say only the number 42", "user_id": "test_user"},
    )
    assert response.status_code == 200
    data = response.json()
    print(f"   ✓ Response: {data['content'][:100]}")
    print(f"   ✓ Session ID: {data['session_id']}")
    return data["session_id"]


def test_session_memory(session_id):
    """Test session memory (multi-turn)."""
    print("\n3️⃣  Testing session memory...")

    # First message
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": "Remember: my favorite color is blue", "user_id": "test_user"},
    )
    assert response.status_code == 200
    print("   → Sent: Remember my favorite color is blue")

    # Second message - should remember
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": "What's my favorite color?", "user_id": "test_user"},
    )
    assert response.status_code == 200
    data = response.json()
    print(f"   ← Claude: {data['content'][:100]}")

    if "blue" in data["content"].lower():
        print("   ✓ Session memory working!")
    else:
        print("   ⚠️  Session memory may not be working")


def test_async_chat():
    """Test async chat."""
    print("\n4️⃣  Testing /chat/async (async mode)...")

    # Submit task
    response = requests.post(
        f"{API_URL}/chat/async",
        json={"message": "Count to 5", "user_id": "async_user"},
    )
    assert response.status_code == 200
    data = response.json()
    task_id = data["task_id"]
    print(f"   ✓ Task submitted: {task_id}")

    # Poll for completion
    print("   ⏳ Waiting for completion...")
    max_attempts = 30
    for i in range(max_attempts):
        response = requests.get(f"{API_URL}/task/{task_id}")
        assert response.status_code == 200
        status = response.json()

        if status["status"] == "completed":
            print(f"   ✓ Task completed!")
            print(f"   ✓ Result: {status['result']['content'][:100]}")
            return

        elif status["status"] == "failed":
            print(f"   ✗ Task failed: {status['error']}")
            return

        time.sleep(1)

    print("   ⚠️  Task timeout")


def test_history():
    """Test conversation history."""
    print("\n5️⃣  Testing /session/{id}/history...")
    response = requests.get(f"{API_URL}/session/user_test_user/history")
    assert response.status_code == 200
    data = response.json()
    print(f"   ✓ Total messages: {data['total_messages']}")
    for i, msg in enumerate(data["messages"][:2], 1):
        print(f"   {i}. {msg['role'].upper()}: {msg['content'][:50]}...")


def main():
    print("=" * 60)
    print("Claude Code Server API - Test Suite")
    print("=" * 60)
    print()
    print("⚠️  Make sure the server is running:")
    print("   python start_server.py")
    print()

    try:
        test_health()
        session_id = test_sync_chat()
        test_session_memory(session_id)
        test_async_chat()
        test_history()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("   Make sure the server is running on http://localhost:8000")
        return 1

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
