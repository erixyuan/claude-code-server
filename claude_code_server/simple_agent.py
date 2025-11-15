"""Simple Agent - 无会话版本

不使用 Claude 的会话功能，通过在提示中包含历史来维护上下文。
适用于不需要或不能使用会话功能的场景。
Explicit is better than implicit.
"""

from typing import Optional

from .client import ClaudeClient
from .session import SessionManager, SessionStore
from .types import ClaudeConfig, ClaudeResponse


class SimpleAgent:
    """简单代理 - 手动管理上下文
    
    通过在每次请求中包含历史消息来维护对话上下文。
    适合：不支持会话或需要完全控制上下文的场景。
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        session_store: Optional[SessionStore] = None,
        max_history_length: int = 10,
    ):
        """初始化简单代理
        
        Args:
            config: Claude 配置
            session_store: 会话存储
            max_history_length: 最大历史轮数（每轮包含用户+助手消息）
        """
        self.client = ClaudeClient(config=config)
        self.session_manager = SessionManager(store=session_store)
        self.max_history_length = max_history_length

    def chat(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        config_override: Optional[ClaudeConfig] = None,
    ) -> ClaudeResponse:
        """发送消息（包含历史上下文）
        
        Args:
            message: 用户消息
            user_id: 用户 ID
            session_id: 会话 ID（可选）
            config_override: 配置覆盖
            
        Returns:
            Claude 的响应
        """
        session_id = session_id or f"user_{user_id}"
        
        # 获取或创建会话
        session = self.session_manager.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
        )
        
        # 构建包含历史的完整提示
        full_prompt = self._build_prompt_with_history(message, session)
        
        # 发送（不使用 Claude 会话）
        response = self.client.chat(
            message=full_prompt,
            claude_session_id=None,  # 显式不使用会话
            config_override=config_override,
        )
        
        # 保存历史
        self.session_manager.add_message(session_id, "user", message)
        self.session_manager.add_message(session_id, "assistant", response.content)
        
        return response

    def _build_prompt_with_history(self, message: str, session) -> str:
        """构建包含历史的提示
        
        格式：
            历史对话：
            User: 消息1
            Assistant: 回复1
            User: 消息2
            Assistant: 回复2
            
            User: 当前消息
        """
        history = session.conversation_history
        
        # 只保留最近的 N 轮对话（每轮 = 用户消息 + 助手回复）
        recent_history = history[-(self.max_history_length * 2):]
        
        if not recent_history:
            return message
        
        # 构建历史上下文
        context_lines = ["历史对话:"]
        for msg in recent_history:
            role = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{role}: {msg.content}")
        
        # 添加当前消息
        context_lines.append(f"\nUser: {message}")
        
        return "\n".join(context_lines)

    def get_conversation_history(self, user_id: str, session_id: Optional[str] = None):
        """获取对话历史"""
        session_id = session_id or f"user_{user_id}"
        return self.session_manager.get_conversation_history(session_id)

    def clear_session(self, user_id: str, session_id: Optional[str] = None) -> None:
        """清除会话"""
        session_id = session_id or f"user_{user_id}"
        self.session_manager.delete_session(session_id)
