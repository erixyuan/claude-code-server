"""
Message formatters for ClaudeAgent.

Formatters add context information to messages before sending to Claude.
"""

from typing import Optional


def simple_formatter(message: str, user_id: str, metadata: dict) -> str:
    """
    Simple formatter that adds user ID prefix.

    Example:
        Input: "你是谁"
        Output: "[用户 eric] 你是谁"
    """
    return f"[用户 {user_id}] {message}"


def imessage_formatter(message: str, user_id: str, metadata: dict) -> str:
    """
    iMessage formatter with context prefix.

    Example:
        Input: "你是谁"
        Output: "# 以下是用户id为eric发过来的iMessage消息\n你是谁"
    """
    return f"# 以下是用户id为{user_id}发过来的iMessage消息\n{message}"


def feishu_formatter(message: str, user_id: str, metadata: dict) -> str:
    """
    飞书消息格式化器。

    Example:
        Input: message="我叫eric", user_id="2f3b45d586d43978b712950b"
        Output: "以下是user_id=2f3b45d586d43978b712950b发过来的飞书消息: 我叫eric"
    """
    return f"以下是user_id={user_id}发过来的飞书消息: {message}"


def platform_formatter(message: str, user_id: str, metadata: dict) -> str:
    """
    Platform-aware formatter that uses metadata["source"].

    Metadata:
        source: Platform name (e.g., "imessage", "feishu", "slack")

    Example:
        Input: message="你是谁", metadata={"source": "imessage"}
        Output: "# 以下是用户id为eric发过来的imessage消息\n你是谁"
    """
    source = metadata.get("source", "未知平台")
    return f"# 以下是用户id为{user_id}发过来的{source}消息\n{message}"


def detailed_formatter(message: str, user_id: str, metadata: dict) -> str:
    """
    Detailed formatter with timestamp and platform info.

    Metadata:
        source: Platform name (optional)
        username: Display name (optional)
        timestamp: Message timestamp (optional)

    Example:
        Input: message="你是谁", metadata={"source": "imessage", "username": "Eric"}
        Output:
            '''
            # 消息上下文
            - 平台: imessage
            - 用户ID: eric
            - 显示名称: Eric

            用户消息:
            你是谁
            '''
    """
    lines = ["# 消息上下文"]

    if "source" in metadata:
        lines.append(f"- 平台: {metadata['source']}")

    lines.append(f"- 用户ID: {user_id}")

    if "username" in metadata:
        lines.append(f"- 显示名称: {metadata['username']}")

    if "timestamp" in metadata:
        lines.append(f"- 时间: {metadata['timestamp']}")

    lines.append("")
    lines.append("用户消息:")
    lines.append(message)

    return "\n".join(lines)


def create_custom_formatter(template: str):
    """
    Create a custom formatter from a template string.

    Template variables:
        {message}: Original message
        {user_id}: User ID
        {source}: Platform source (from metadata)
        {username}: Display name (from metadata)
        Any field from metadata can be used

    Example:
        formatter = create_custom_formatter(
            "# 来自{source}的用户{user_id}说:\n{message}"
        )
        result = formatter("你好", "eric", {"source": "feishu"})
        # Output: "# 来自feishu的用户eric说:\n你好"
    """
    def custom_formatter(message: str, user_id: str, metadata: dict) -> str:
        # Prepare template variables
        template_vars = {
            "message": message,
            "user_id": user_id,
            "source": metadata.get("source", ""),
            "username": metadata.get("username", ""),
        }
        # Add all metadata fields (avoid duplicates)
        for key, value in metadata.items():
            if key not in template_vars:
                template_vars[key] = value

        return template.format(**template_vars)
    return custom_formatter


# Preset formatters
FORMATTERS = {
    "simple": simple_formatter,
    "imessage": imessage_formatter,
    "feishu": feishu_formatter,
    "platform": platform_formatter,
    "detailed": detailed_formatter,
}


def get_formatter(name: str):
    """
    Get a formatter by name.

    Args:
        name: Formatter name ("simple", "imessage", "feishu", "platform", "detailed")

    Returns:
        Formatter function or None if not found

    Example:
        formatter = get_formatter("feishu")
        agent = ClaudeAgent(message_formatter=formatter)
    """
    return FORMATTERS.get(name)
