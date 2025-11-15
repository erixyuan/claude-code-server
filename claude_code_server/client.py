"""Claude Agent SDK 客户端实现

使用官方 claude-agent-sdk 与 Claude 交互。
Simple is better than complex.
"""

import asyncio
from pathlib import Path
from typing import Optional

from .exceptions import ClaudeExecutionError, InvalidConfigError
from .types import ClaudeConfig, ClaudeResponse

# 尝试导入 Claude Agent SDK
try:
    from claude_agent_sdk import ClaudeAgentOptions, query
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    query = None
    ClaudeAgentOptions = None


class ClaudeClient:
    """Claude 客户端 - 使用官方 Agent SDK
    
    最简单的使用方式：
        >>> client = ClaudeClient()
        >>> response = client.chat("你好")
        >>> print(response.content)
    """

    def __init__(self, config: Optional[ClaudeConfig] = None):
        """初始化客户端
        
        Args:
            config: 配置对象，默认使用 ClaudeConfig()
        """
        if not SDK_AVAILABLE:
            raise InvalidConfigError(
                "claude-agent-sdk 未安装。请运行：pip install claude-agent-sdk"
            )
        self.config = config or ClaudeConfig()

    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        claude_session_id: Optional[str] = None,
        config_override: Optional[ClaudeConfig] = None,
    ) -> ClaudeResponse:
        """发送消息给 Claude
        
        Args:
            message: 要发送的消息
            session_id: 用户会话 ID（仅用于引用）
            claude_session_id: Claude SDK 的会话 ID（用于恢复对话）
            config_override: 覆盖默认配置
            
        Returns:
            ClaudeResponse 包含响应内容和元数据
        """
        config = config_override or self.config
        
        # 调试信息（如果启用）
        if config.debug_print_command:
            self._print_debug_info(message, claude_session_id, config)
        
        try:
            # 1. 构建选项
            options = self._build_options(config, claude_session_id)
            
            # 2. 调用 SDK（异步转同步）
            messages = self._run_query(message, options)
            
            # 3. 解析响应
            return self._parse_response(messages)
            
        except Exception as e:
            raise ClaudeExecutionError(
                f"Claude Agent SDK 执行失败: {str(e)}",
                return_code=-1,
            )

    def _run_query(self, message: str, options: ClaudeAgentOptions) -> list:
        """运行异步查询（同步方式）
        
        SDK 的 query 是异步生成器，这里转换为同步调用。
        """
        async def collect_messages():
            """收集所有消息"""
            messages = []
            async for msg in query(prompt=message, options=options):
                messages.append(msg)
            return messages
        
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(collect_messages())

    def _build_options(
        self, 
        config: ClaudeConfig, 
        session_id: Optional[str]
    ) -> ClaudeAgentOptions:
        """构建 SDK 选项
        
        将我们的 ClaudeConfig 转换为 SDK 所需的 ClaudeAgentOptions。
        注意：SDK 使用不同的参数名（如 cwd 而不是 working_directory）
        """
        options = {}
        
        # 模型
        if config.model:
            options["model"] = config.model
        
        # 权限模式
        if config.permission_mode:
            options["permission_mode"] = config.permission_mode
        
        # 系统提示（从配置文件加载）
        system_prompt = self._load_system_prompt(config)
        if system_prompt:
            options["system_prompt"] = system_prompt
        
        # 工作目录（SDK 使用 'cwd'）
        if config.working_directory:
            options["cwd"] = config.working_directory
        
        # 允许的工具
        if config.allowed_tools:
            options["allowed_tools"] = config.allowed_tools
        
        # 恢复会话（SDK 使用 'resume'）
        if session_id:
            options["resume"] = session_id
        
        # 设置来源（加载用户/项目/本地配置）
        options["setting_sources"] = ["user", "project", "local"]
        
        return ClaudeAgentOptions(**options)

    def _load_system_prompt(self, config: ClaudeConfig) -> Optional[str]:
        """加载系统提示
        
        按优先级加载：
        1. 配置中的 append_system_prompt
        2. .claude/CLAUDE.md 或 CLAUDE.md
        3. SYSTEM_PROMPT.md
        """
        prompt_parts = []
        
        # 配置中的提示
        if config.append_system_prompt:
            prompt_parts.append(config.append_system_prompt)
        
        # 从文件加载
        if config.working_directory:
            working_dir = Path(config.working_directory)
            
            # 尝试加载 CLAUDE.md
            for path in [working_dir / ".claude" / "CLAUDE.md", working_dir / "CLAUDE.md"]:
                if path.exists():
                    try:
                        prompt_parts.insert(0, path.read_text(encoding='utf-8'))
                        break  # 只使用第一个找到的
                    except OSError:
                        pass  # 忽略读取错误
            
            # 尝试加载 SYSTEM_PROMPT.md
            system_prompt_path = working_dir / "SYSTEM_PROMPT.md"
            if system_prompt_path.exists():
                try:
                    prompt_parts.append(system_prompt_path.read_text(encoding='utf-8'))
                except OSError:
                    pass
        
        return "\n\n".join(prompt_parts) if prompt_parts else None

    def _parse_response(self, messages: list) -> ClaudeResponse:
        """解析 SDK 响应
        
        SDK 返回三种消息类型：
        - SystemMessage: 系统初始化信息（包含 session_id）
        - AssistantMessage: Claude 的回复（包含实际内容）
        - ResultMessage: 结果统计（包含总结）
        """
        content_parts = []
        session_id = None
        
        for msg in messages:
            msg_type = type(msg).__name__
            # 提取会话 ID（来自 SystemMessage 或 ResultMessage）
            if hasattr(msg, 'session_id') and msg.session_id:
                session_id = msg.session_id
            
            # 提取内容（来自 AssistantMessage）
            if msg_type == 'AssistantMessage' and hasattr(msg, 'content'):
                for block in msg.content:
                    if hasattr(block, 'text'):  # TextBlock
                        content_parts.append(block.text)
                    elif isinstance(block, str):  # 字符串
                        content_parts.append(block)
        
        return ClaudeResponse(
            content="".join(content_parts),
            raw_output=str(messages),
            success=True,
            metadata={
                "claude_session_id": session_id,
                "message_count": len(messages),
            },
        )

    def _print_debug_info(self, message: str, session_id: Optional[str], config: ClaudeConfig):
        """打印调试信息"""
        print("\n" + "=" * 80)
        print("🚀 执行 Claude Agent SDK")
        print("=" * 80)
        print(f"消息: {message[:100]}{'...' if len(message) > 100 else ''}")
        print(f"会话: {session_id or '新会话'}")
        print(f"目录: {config.working_directory or '当前目录'}")
        print("=" * 80 + "\n")
