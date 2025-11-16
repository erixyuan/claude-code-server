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
        from claude_code_server.logger import logger

        task_id = str(uuid.uuid4())

        task_status = TaskStatus(
            task_id=task_id,
            status="pending",
            created_at=datetime.now(),
        )

        self.tasks[task_id] = task_status

        logger.info("=" * 80)
        logger.info("🎯 创建异步任务")
        logger.info("=" * 80)
        logger.info(f"📋 Task ID: {task_id}")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔑 Session ID: {session_id or f'user_{user_id}'}")
        logger.info(f"📝 消息内容: {message}")
        logger.info(f"📏 消息长度: {len(message)} 字符")
        # 检测是否为合并消息（包含换行符）
        if '\n' in message:
            parts = message.split('\n')
            logger.info(f"🔄 检测到合并消息，包含 {len(parts)} 部分:")
            for i, part in enumerate(parts, 1):
                logger.info(f"   {i}. {part[:100]}{'...' if len(part) > 100 else ''}")
        logger.info("=" * 80)

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
        from claude_code_server.logger import logger

        async with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "processing"

        logger.info(f"▶️  开始执行任务 {task_id}")

        try:
            # Run in thread pool (since agent.chat is sync)
            loop = asyncio.get_event_loop()
            start_time = datetime.now()

            response = await loop.run_in_executor(
                self.executor, lambda: agent.chat(message, user_id, session_id)
            )

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ 任务 {task_id} 执行成功，耗时: {duration:.2f}s")

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
            logger.error(f"❌ 任务 {task_id} 执行失败: {str(e)}")
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
