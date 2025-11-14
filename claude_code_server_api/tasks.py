"""
Async task management for background processing.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from .models import TaskStatus, ChatResponse
from claude_code_server import ClaudeAgent


class TaskManager:
    """Manages async tasks for chat processing."""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, TaskStatus] = {}
        self._lock = asyncio.Lock()

    def create_task(
        self, agent: ClaudeAgent, message: str, user_id: str, session_id: Optional[str]
    ) -> str:
        """
        Create a new async task.

        Returns:
            task_id: Unique task identifier
        """
        task_id = str(uuid.uuid4())

        task_status = TaskStatus(
            task_id=task_id,
            status="pending",
            created_at=datetime.now(),
        )

        self.tasks[task_id] = task_status

        # Submit to executor
        asyncio.create_task(self._execute_task(task_id, agent, message, user_id, session_id))

        return task_id

    async def _execute_task(
        self,
        task_id: str,
        agent: ClaudeAgent,
        message: str,
        user_id: str,
        session_id: Optional[str],
    ):
        """Execute chat task in background."""
        async with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "processing"

        try:
            # Run in thread pool (since agent.chat is sync)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor, lambda: agent.chat(message, user_id, session_id)
            )

            # Update task with result
            async with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "completed"
                    self.tasks[task_id].completed_at = datetime.now()
                    self.tasks[task_id].result = ChatResponse(
                        content=response.content,
                        session_id=session_id or f"user_{user_id}",
                        claude_session_id=response.metadata.get("claude_session_id"),
                        success=response.success,
                        metadata=response.metadata,
                    )

        except Exception as e:
            async with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "failed"
                    self.tasks[task_id].completed_at = datetime.now()
                    self.tasks[task_id].error = str(e)

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status by ID."""
        async with self._lock:
            return self.tasks.get(task_id)

    async def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Clean up old completed tasks."""
        now = datetime.now()
        async with self._lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(task_id)

            for task_id in to_remove:
                del self.tasks[task_id]
