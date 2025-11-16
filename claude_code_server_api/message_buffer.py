"""
Message buffering and debouncing for async chat requests.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from claude_code_server.logger import logger


@dataclass
class PendingMessage:
    """A pending message waiting to be processed."""

    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BufferState:
    """State for a message buffer."""

    messages: List[PendingMessage] = field(default_factory=list)
    timer_task: Optional[asyncio.Task] = None
    is_processing: bool = False


class MessageBuffer:
    """
    Message buffer with time-window debouncing.

    This class buffers incoming messages and automatically merges them
    if they arrive within a specified time window (debounce_window).

    Usage:
        buffer = MessageBuffer(default_window=2.0)
        await buffer.add_message(
            session_id="user_123",
            message="Hello",
            callback=process_combined_message,
            debounce_window=2.0
        )
    """

    def __init__(self, default_window: float = 2.0, message_separator: str = "\n"):
        """
        Initialize message buffer.

        Args:
            default_window: Default debounce window in seconds
            message_separator: String to join messages when combining
        """
        self.default_window = default_window
        self.message_separator = message_separator
        self.buffers: Dict[str, BufferState] = {}
        self._lock = asyncio.Lock()

    async def add_message(
        self,
        session_id: str,
        message: str,
        callback: Callable[[str], None],
        debounce_window: Optional[float] = None,
    ) -> None:
        """
        Add a message to the buffer.

        If this is the first message for the session, starts a debounce timer.
        If messages already exist, cancels the existing timer and starts a new one.

        Args:
            session_id: Unique identifier for the conversation session
            message: Message content to buffer
            callback: Async function to call with combined message when timer expires
            debounce_window: Debounce window in seconds (uses default if None)
        """
        window = debounce_window if debounce_window is not None else self.default_window

        async with self._lock:
            # Initialize buffer state if not exists
            if session_id not in self.buffers:
                self.buffers[session_id] = BufferState()

            state = self.buffers[session_id]

            # Add message to buffer
            pending_msg = PendingMessage(message=message)
            state.messages.append(pending_msg)

            logger.debug(
                f"📝 Message buffered for session {session_id}: "
                f"'{message[:50]}...' (total: {len(state.messages)} messages)"
            )

            # Cancel existing timer if any
            if state.timer_task and not state.timer_task.done():
                state.timer_task.cancel()
                logger.debug(f"⏱️  Cancelled existing timer for session {session_id}")

            # Start new debounce timer
            state.timer_task = asyncio.create_task(
                self._debounce_timer(session_id, window, callback)
            )
            logger.debug(
                f"⏱️  Started {window}s debounce timer for session {session_id}"
            )

    async def _debounce_timer(
        self, session_id: str, delay: float, callback: Callable[[str], None]
    ):
        """
        Wait for debounce period, then flush messages.

        Args:
            session_id: Session identifier
            delay: How long to wait in seconds
            callback: Function to call with combined message
        """
        try:
            logger.debug(f"⏳ Waiting {delay}s for session {session_id}...")
            await asyncio.sleep(delay)

            # Timer expired, flush messages
            await self._flush(session_id, callback)

        except asyncio.CancelledError:
            # Timer was cancelled (new message arrived)
            logger.debug(f"⏱️  Timer cancelled for session {session_id}")
            raise

    async def _flush(self, session_id: str, callback: Callable[[str], None]):
        """
        Combine buffered messages and invoke callback.

        Args:
            session_id: Session identifier
            callback: Function to call with combined message
        """
        async with self._lock:
            if session_id not in self.buffers:
                logger.warning(f"⚠️  No buffer found for session {session_id}")
                return

            state = self.buffers[session_id]

            if not state.messages:
                logger.warning(f"⚠️  No messages to flush for session {session_id}")
                return

            # Mark as processing to prevent concurrent flushes
            if state.is_processing:
                logger.warning(
                    f"⚠️  Already processing messages for session {session_id}"
                )
                return

            state.is_processing = True

            # Combine messages
            message_texts = [msg.message for msg in state.messages]
            combined_message = self.message_separator.join(message_texts)

            message_count = len(state.messages)
            logger.info(
                f"🔄 Flushing {message_count} message(s) for session {session_id}"
            )
            logger.debug(f"   Combined message: '{combined_message[:100]}...'")

            # Clear buffer before invoking callback (to allow new messages during processing)
            state.messages.clear()
            state.timer_task = None

        # Invoke callback outside of lock
        try:
            await callback(combined_message)
            logger.debug(f"✅ Callback completed for session {session_id}")
        except Exception as e:
            logger.error(
                f"❌ Error in callback for session {session_id}: {e}", exc_info=True
            )
        finally:
            # Mark as not processing
            async with self._lock:
                if session_id in self.buffers:
                    self.buffers[session_id].is_processing = False

    async def cancel_pending(self, session_id: str) -> bool:
        """
        Cancel pending debounce timer for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if a timer was cancelled, False otherwise
        """
        async with self._lock:
            if session_id not in self.buffers:
                return False

            state = self.buffers[session_id]

            if state.timer_task and not state.timer_task.done():
                state.timer_task.cancel()
                logger.debug(f"🛑 Cancelled pending timer for session {session_id}")
                return True

            return False

    async def get_pending_count(self, session_id: str) -> int:
        """
        Get number of pending messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of messages currently buffered
        """
        async with self._lock:
            if session_id not in self.buffers:
                return 0
            return len(self.buffers[session_id].messages)

    async def cleanup_session(self, session_id: str):
        """
        Remove buffer state for a session (after processing complete).

        Args:
            session_id: Session identifier
        """
        async with self._lock:
            if session_id in self.buffers:
                state = self.buffers[session_id]
                if state.timer_task and not state.timer_task.done():
                    state.timer_task.cancel()
                del self.buffers[session_id]
                logger.debug(f"🧹 Cleaned up buffer for session {session_id}")
