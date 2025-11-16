#!/usr/bin/env python3
"""
Unit tests for MessageBuffer class.
"""

import asyncio
import pytest
from claude_code_server_api.message_buffer import MessageBuffer


class TestMessageBuffer:
    """Test cases for MessageBuffer."""

    @pytest.mark.asyncio
    async def test_single_message_immediate_flush(self):
        """Test that a single message is flushed after debounce window."""
        buffer = MessageBuffer(default_window=0.1)  # 100ms for fast testing
        received_messages = []

        async def callback(combined_message: str):
            received_messages.append(combined_message)

        # Send message
        await buffer.add_message(
            session_id="test_session_1",
            message="Hello",
            callback=callback,
            debounce_window=0.1,
        )

        # Wait for timer
        await asyncio.sleep(0.15)

        # Check callback was called
        assert len(received_messages) == 1
        assert received_messages[0] == "Hello"

    @pytest.mark.asyncio
    async def test_multiple_messages_combined(self):
        """Test that multiple rapid messages are combined."""
        buffer = MessageBuffer(default_window=0.2)
        received_messages = []

        async def callback(combined_message: str):
            received_messages.append(combined_message)

        # Send 3 messages rapidly
        await buffer.add_message(
            session_id="test_session_2", message="Hello", callback=callback
        )
        await asyncio.sleep(0.05)  # 50ms delay

        await buffer.add_message(
            session_id="test_session_2", message="How", callback=callback
        )
        await asyncio.sleep(0.05)

        await buffer.add_message(
            session_id="test_session_2", message="are you?", callback=callback
        )

        # Wait for timer
        await asyncio.sleep(0.3)

        # Check all messages were combined into one
        assert len(received_messages) == 1
        assert received_messages[0] == "Hello\nHow\nare you?"

    @pytest.mark.asyncio
    async def test_timer_reset_on_new_message(self):
        """Test that timer resets when new message arrives."""
        buffer = MessageBuffer(default_window=0.2)
        received_messages = []
        call_times = []

        async def callback(combined_message: str):
            received_messages.append(combined_message)
            call_times.append(asyncio.get_event_loop().time())

        start_time = asyncio.get_event_loop().time()

        # Send first message
        await buffer.add_message(
            session_id="test_session_3", message="First", callback=callback
        )

        # Wait 150ms (within 200ms window)
        await asyncio.sleep(0.15)

        # Send second message - should reset timer
        await buffer.add_message(
            session_id="test_session_3", message="Second", callback=callback
        )

        # Wait for timer
        await asyncio.sleep(0.25)

        # Check callback was called once
        assert len(received_messages) == 1
        assert received_messages[0] == "First\nSecond"

        # Check timing - should be ~350ms (150ms + 200ms), not ~200ms
        elapsed = call_times[0] - start_time
        assert elapsed >= 0.35  # At least 350ms

    @pytest.mark.asyncio
    async def test_different_sessions_independent(self):
        """Test that different sessions maintain separate buffers."""
        buffer = MessageBuffer(default_window=0.2)
        received_messages = {"session1": [], "session2": []}

        async def callback_1(msg):
            received_messages["session1"].append(msg)

        async def callback_2(msg):
            received_messages["session2"].append(msg)

        # Send to session 1
        await buffer.add_message(
            session_id="session1", message="Session 1 Message", callback=callback_1
        )

        # Send to session 2
        await buffer.add_message(
            session_id="session2", message="Session 2 Message", callback=callback_2
        )

        # Wait for timers
        await asyncio.sleep(0.3)

        # Check both were processed independently
        assert len(received_messages["session1"]) == 1
        assert len(received_messages["session2"]) == 1
        assert received_messages["session1"][0] == "Session 1 Message"
        assert received_messages["session2"][0] == "Session 2 Message"

    @pytest.mark.asyncio
    async def test_custom_separator(self):
        """Test using custom message separator."""
        buffer = MessageBuffer(default_window=0.1, message_separator=" | ")
        received_messages = []

        async def callback(msg):
            received_messages.append(msg)

        await buffer.add_message(
            session_id="test_session_5", message="Part1", callback=callback
        )
        await buffer.add_message(
            session_id="test_session_5", message="Part2", callback=callback
        )
        await buffer.add_message(
            session_id="test_session_5", message="Part3", callback=callback
        )

        await asyncio.sleep(0.15)

        assert len(received_messages) == 1
        assert received_messages[0] == "Part1 | Part2 | Part3"

    @pytest.mark.asyncio
    async def test_get_pending_count(self):
        """Test getting pending message count."""
        buffer = MessageBuffer(default_window=0.5)

        async def callback(msg):
            pass

        # No messages yet
        count = await buffer.get_pending_count("test_session_6")
        assert count == 0

        # Add messages
        await buffer.add_message(
            session_id="test_session_6", message="Msg1", callback=callback
        )
        count = await buffer.get_pending_count("test_session_6")
        assert count == 1

        await buffer.add_message(
            session_id="test_session_6", message="Msg2", callback=callback
        )
        count = await buffer.get_pending_count("test_session_6")
        assert count == 2

        # Wait for flush
        await asyncio.sleep(0.6)
        count = await buffer.get_pending_count("test_session_6")
        assert count == 0

    @pytest.mark.asyncio
    async def test_cancel_pending(self):
        """Test cancelling pending timer."""
        buffer = MessageBuffer(default_window=0.5)
        received_messages = []

        async def callback(msg):
            received_messages.append(msg)

        # Add message
        await buffer.add_message(
            session_id="test_session_7", message="Test", callback=callback
        )

        # Cancel timer
        cancelled = await buffer.cancel_pending("test_session_7")
        assert cancelled is True

        # Wait to ensure callback isn't called
        await asyncio.sleep(0.6)
        assert len(received_messages) == 0


if __name__ == "__main__":
    # Run tests
    print("Running MessageBuffer unit tests...\n")

    async def run_all_tests():
        test = TestMessageBuffer()

        print("Test 1: Single message immediate flush...")
        await test.test_single_message_immediate_flush()
        print("✅ PASSED\n")

        print("Test 2: Multiple messages combined...")
        await test.test_multiple_messages_combined()
        print("✅ PASSED\n")

        print("Test 3: Timer reset on new message...")
        await test.test_timer_reset_on_new_message()
        print("✅ PASSED\n")

        print("Test 4: Different sessions independent...")
        await test.test_different_sessions_independent()
        print("✅ PASSED\n")

        print("Test 5: Custom separator...")
        await test.test_custom_separator()
        print("✅ PASSED\n")

        print("Test 6: Get pending count...")
        await test.test_get_pending_count()
        print("✅ PASSED\n")

        print("Test 7: Cancel pending...")
        await test.test_cancel_pending()
        print("✅ PASSED\n")

        print("=" * 50)
        print("All tests passed! ✅")
        print("=" * 50)

    asyncio.run(run_all_tests())
