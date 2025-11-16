#!/usr/bin/env python3
"""
Test script for message debouncing functionality.

This script simulates a user sending multiple messages in quick succession
to verify that they are properly combined by the debouncing mechanism.
"""

import asyncio
import time
from datetime import datetime
import httpx


BASE_URL = "http://localhost:8000"
API_KEY = None  # Set if your server requires API key


async def send_message(client: httpx.AsyncClient, message: str, user_id: str):
    """Send a single message to the async endpoint."""
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    payload = {
        "message": message,
        "user_id": user_id,
        "enable_debounce": True,  # Explicitly enable debouncing
        "debounce_window": 3.0,  # 3 second window
    }

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] 📤 Sending: '{message}'")

    response = await client.post(f"{BASE_URL}/chat/async", json=payload, headers=headers)
    result = response.json()

    print(f"[{timestamp}] ✅ Response: {result}")
    return result


async def test_rapid_messages():
    """Test Case 1: Rapid successive messages (should be combined)."""
    print("\n" + "=" * 60)
    print("TEST 1: Rapid Successive Messages")
    print("=" * 60)
    print("Scenario: User sends 'Hello', 'How', 'are', 'you?' in quick succession")
    print("Expected: All 4 messages combined into one task\n")

    user_id = "test_user_1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Send messages rapidly
        await send_message(client, "Hello", user_id)
        await asyncio.sleep(0.3)  # 300ms delay

        await send_message(client, "How", user_id)
        await asyncio.sleep(0.3)

        await send_message(client, "are", user_id)
        await asyncio.sleep(0.3)

        await send_message(client, "you?", user_id)

        print(
            "\n⏳ Waiting 4 seconds for debounce timer to expire and task to be created..."
        )
        await asyncio.sleep(4)

        print("\n✅ Test 1 Complete!")
        print("Check server logs to verify messages were combined\n")


async def test_delayed_messages():
    """Test Case 2: Messages with long delay (should NOT be combined)."""
    print("\n" + "=" * 60)
    print("TEST 2: Delayed Messages")
    print("=" * 60)
    print(
        "Scenario: User sends 'First message', waits 4s, then sends 'Second message'"
    )
    print("Expected: Two separate tasks created\n")

    user_id = "test_user_2"

    async with httpx.AsyncClient(timeout=30.0) as client:
        await send_message(client, "First message", user_id)

        print("\n⏳ Waiting 4 seconds (longer than debounce window)...")
        await asyncio.sleep(4)

        await send_message(client, "Second message", user_id)

        print("\n⏳ Waiting 4 seconds for second message to process...")
        await asyncio.sleep(4)

        print("\n✅ Test 2 Complete!")
        print("Check server logs to verify two separate tasks were created\n")


async def test_debounce_disabled():
    """Test Case 3: Debouncing disabled (immediate processing)."""
    print("\n" + "=" * 60)
    print("TEST 3: Debouncing Disabled")
    print("=" * 60)
    print("Scenario: User sends messages with debouncing explicitly disabled")
    print("Expected: Each message creates a task immediately\n")

    user_id = "test_user_3"

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        # Send with debouncing disabled
        payload1 = {
            "message": "Message 1",
            "user_id": user_id,
            "enable_debounce": False,  # Disable debouncing
        }

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 📤 Sending: 'Message 1' (debounce=False)")
        response = await client.post(
            f"{BASE_URL}/chat/async", json=payload1, headers=headers
        )
        result = response.json()
        print(f"[{timestamp}] ✅ Response: {result}")

        await asyncio.sleep(0.5)

        payload2 = {
            "message": "Message 2",
            "user_id": user_id,
            "enable_debounce": False,
        }

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 📤 Sending: 'Message 2' (debounce=False)")
        response = await client.post(
            f"{BASE_URL}/chat/async", json=payload2, headers=headers
        )
        result = response.json()
        print(f"[{timestamp}] ✅ Response: {result}")

        print("\n✅ Test 3 Complete!")
        print("Both messages should have created tasks immediately\n")


async def test_timer_reset():
    """Test Case 4: Timer reset on new message (debounce window extends)."""
    print("\n" + "=" * 60)
    print("TEST 4: Timer Reset")
    print("=" * 60)
    print("Scenario: User sends message every 2s (debounce window is 3s)")
    print("Expected: Timer keeps resetting, all messages combined when user stops\n")

    user_id = "test_user_4"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Send 3 messages, 2 seconds apart
        await send_message(client, "Part 1", user_id)
        await asyncio.sleep(2)

        await send_message(client, "Part 2", user_id)
        await asyncio.sleep(2)

        await send_message(client, "Part 3", user_id)

        print("\n⏳ Waiting 4 seconds for debounce timer to expire...")
        await asyncio.sleep(4)

        print("\n✅ Test 4 Complete!")
        print("All 3 messages should have been combined into one task\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Message Debouncing Test Suite")
    print("=" * 60)
    print(f"Server: {BASE_URL}")
    print("Make sure the server is running with debouncing enabled!\n")

    try:
        # Check server health
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Server is healthy\n")
            else:
                print("❌ Server health check failed")
                return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server first: claude-code-server --config config.yaml")
        return

    # Run tests
    await test_rapid_messages()
    await test_delayed_messages()
    await test_debounce_disabled()
    await test_timer_reset()

    print("=" * 60)
    print("All Tests Complete!")
    print("=" * 60)
    print(
        "\n💡 Review the server logs to verify message combining behavior"
    )


if __name__ == "__main__":
    asyncio.run(main())
