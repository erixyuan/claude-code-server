"""Claude Agent - 高级接口

提供自动会话管理的简化 API。
Readability counts.
"""

from typing import Callable, Optional

from .client import ClaudeClient
from .session import SessionManager, SessionStore
from .types import ClaudeConfig, ClaudeResponse
from .logger import logger


class ClaudeAgent:
    """Claude 代理 - 自动管理会话
    
    最佳的多用户对话方式：
        >>> agent = ClaudeAgent()
        >>> agent.chat("你好", user_id="alice")
        >>> agent.chat("继续", user_id="alice")  # 自动记住上下文
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        session_store: Optional[SessionStore] = None,
        message_formatter: Optional[Callable] = None,
    ):
        """初始化代理
        
        Args:
            config: Claude 配置
            session_store: 会话存储（默认内存存储）
            message_formatter: 消息格式化函数
                签名: (message, user_id, metadata) -> formatted_message
        """
        self.client = ClaudeClient(config=config)
        self.session_manager = SessionManager(store=session_store)
        self.message_formatter = message_formatter

    def chat(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        config_override: Optional[ClaudeConfig] = None,
        metadata: Optional[dict] = None,
    ) -> ClaudeResponse:
        """发送消息（自动管理会话）

        Args:
            message: 消息内容
            user_id: 用户 ID
            session_id: 自定义会话 ID（可选，默认使用 user_id）
            config_override: 临时覆盖配置
            metadata: 元数据（用于消息格式化）

        Returns:
            Claude 的响应
        """
        # 1. 确定会话 ID
        session_id = session_id or f"user_{user_id}"

        logger.info("=" * 80)
        logger.info("📥 Agent 收到消息")
        logger.info("=" * 80)
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔑 Session ID: {session_id}")
        logger.info(f"📝 原始消息: {message}")

        # 2. 获取或创建会话
        session = self.session_manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
        )

        # 3. 格式化消息（如果提供了格式化器）
        formatted_message = self._format_message(message, user_id, metadata)

        if formatted_message != message:
            logger.info(f"✏️  格式化后: {formatted_message}")
        else:
            logger.info("✏️  无需格式化（未配置 formatter 或格式化器返回原文）")

        # 4. 发送消息（使用之前的 Claude 会话 ID）
        logger.info(f"📤 发送给 Claude Client...")
        response = self.client.chat(
            message=formatted_message,
            session_id=session_id,
            claude_session_id=session.claude_session_id,
            config_override=config_override,
        )

        # 5. 更新 Claude 会话 ID（用于下次对话）
        new_session_id = response.metadata.get("claude_session_id")
        if new_session_id:
            self.session_manager.update_claude_session_id(session_id, new_session_id)
            logger.debug(f"🔄 更新 Claude Session ID: {new_session_id}")

        # 6. 保存对话历史
        self.session_manager.add_message(session_id, "user", message)
        self.session_manager.add_message(session_id, "assistant", response.content)
        logger.info(f"💾 已保存对话历史")

        logger.info(f"✅ Agent 处理完成")
        logger.info("=" * 80)

        return response

    def get_conversation_history(self, user_id: str, session_id: Optional[str] = None):
        """获取对话历史
        
        Args:
            user_id: 用户 ID
            session_id: 会话 ID（可选）
            
        Returns:
            消息列表
        """
        session_id = session_id or f"user_{user_id}"
        return self.session_manager.get_conversation_history(session_id)

    def clear_session(self, user_id: str, session_id: Optional[str] = None) -> None:
        """清除会话
        
        Args:
            user_id: 用户 ID
            session_id: 会话 ID（可选）
        """
        session_id = session_id or f"user_{user_id}"
        self.session_manager.delete_session(session_id)

    def _format_message(self, message: str, user_id: str, metadata: Optional[dict]) -> str:
        """格式化消息
        
        如果提供了格式化器，使用格式化器处理消息。
        否则返回原始消息。
        """
        if self.message_formatter:
            return self.message_formatter(message, user_id, metadata or {})
        return message
