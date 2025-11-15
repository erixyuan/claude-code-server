"""
消息格式化示例

展示如何使用不同的消息格式化器为 Claude 提供上下文信息
"""

from claude_code_server import (
    ClaudeAgent,
    ClaudeConfig,
    simple_formatter,
    imessage_formatter,
    platform_formatter,
    detailed_formatter,
    create_custom_formatter,
)


def example_1_no_formatter():
    """示例 1: 不使用格式化器（默认）"""
    print("=" * 80)
    print("示例 1: 不使用格式化器")
    print("=" * 80)

    agent = ClaudeAgent()

    # 原始消息直接发送
    response = agent.chat("你是谁？", user_id="eric")
    print(f"响应: {response.content[:200]}")
    print()


def example_2_simple_formatter():
    """示例 2: 使用简单格式化器"""
    print("=" * 80)
    print("示例 2: 简单格式化器")
    print("=" * 80)

    agent = ClaudeAgent(message_formatter=simple_formatter)

    # 实际发送: "[用户 eric] 你是谁？"
    response = agent.chat("你是谁？", user_id="eric")
    print(f"响应: {response.content[:200]}")
    print()


def example_3_imessage_formatter():
    """示例 3: iMessage 格式化器"""
    print("=" * 80)
    print("示例 3: iMessage 格式化器")
    print("=" * 80)

    agent = ClaudeAgent(message_formatter=imessage_formatter)

    # 实际发送:
    # "# 以下是用户id为eric发过来的iMessage消息
    # 你是谁？"
    response = agent.chat("你是谁？", user_id="eric")
    print(f"响应: {response.content[:200]}")
    print()


def example_4_platform_formatter():
    """示例 4: 平台感知格式化器"""
    print("=" * 80)
    print("示例 4: 平台感知格式化器")
    print("=" * 80)

    agent = ClaudeAgent(message_formatter=platform_formatter)

    # 传递平台信息
    response = agent.chat(
        "你是谁？",
        user_id="eric",
        metadata={"source": "feishu"}  # 飞书平台
    )
    # 实际发送: "# 以下是用户id为eric发过来的feishu消息\n你是谁？"
    print(f"响应: {response.content[:200]}")
    print()


def example_5_detailed_formatter():
    """示例 5: 详细格式化器"""
    print("=" * 80)
    print("示例 5: 详细格式化器")
    print("=" * 80)

    agent = ClaudeAgent(message_formatter=detailed_formatter)

    # 传递详细信息
    response = agent.chat(
        "帮我分析一下代码",
        user_id="eric",
        metadata={
            "source": "slack",
            "username": "Eric Yuan",
            "timestamp": "2025-11-14 15:30:00"
        }
    )
    print(f"响应: {response.content[:200]}")
    print()


def example_6_custom_formatter():
    """示例 6: 自定义格式化器"""
    print("=" * 80)
    print("示例 6: 自定义格式化器")
    print("=" * 80)

    # 创建自定义模板
    custom_formatter = create_custom_formatter(
        "🔔 来自 {source} 平台的用户 {user_id} ({username}) 说:\n{message}"
    )

    agent = ClaudeAgent(message_formatter=custom_formatter)

    response = agent.chat(
        "你好",
        user_id="eric",
        metadata={
            "source": "WeChat",
            "username": "Eric"
        }
    )
    # 实际发送: "🔔 来自 WeChat 平台的用户 eric (Eric) 说:\n你好"
    print(f"响应: {response.content[:200]}")
    print()


def example_7_lambda_formatter():
    """示例 7: 使用 Lambda 表达式"""
    print("=" * 80)
    print("示例 7: Lambda 格式化器")
    print("=" * 80)

    # 直接使用 lambda
    agent = ClaudeAgent(
        message_formatter=lambda msg, uid, meta: f"[{uid}@{meta.get('channel', 'unknown')}]: {msg}"
    )

    response = agent.chat(
        "测试消息",
        user_id="eric",
        metadata={"channel": "general"}
    )
    # 实际发送: "[eric@general]: 测试消息"
    print(f"响应: {response.content[:200]}")
    print()


def example_8_chatbot_scenario():
    """示例 8: 实际聊天机器人场景"""
    print("=" * 80)
    print("示例 8: 飞书聊天机器人场景")
    print("=" * 80)

    # 模拟飞书机器人
    def feishu_formatter(message: str, user_id: str, metadata: dict) -> str:
        """飞书机器人专用格式化器"""
        display_name = metadata.get("display_name", user_id)
        department = metadata.get("department", "未知部门")

        return f"""# 飞书消息上下文
- 用户: {display_name} (ID: {user_id})
- 部门: {department}
- 平台: 飞书企业通讯

用户消息:
{message}
"""

    agent = ClaudeAgent(message_formatter=feishu_formatter)

    # 模拟飞书消息
    response = agent.chat(
        "请帮我生成本周工作总结",
        user_id="ou_7d8a6e6e",
        metadata={
            "display_name": "张三",
            "department": "技术部"
        }
    )

    print(f"响应: {response.content[:200]}")
    print()


if __name__ == "__main__":
    print("\n" + "🎯 消息格式化器示例".center(80, "="))
    print()

    # 运行所有示例（注释掉实际调用，避免 API 调用）
    print("⚠️  本示例展示了如何使用格式化器")
    print("💡 实际运行需要 Claude CLI 和正确的配置\n")

    # 取消注释以下行来运行实际示例
    # example_1_no_formatter()
    # example_2_simple_formatter()
    # example_3_imessage_formatter()
    # example_4_platform_formatter()
    # example_5_detailed_formatter()
    # example_6_custom_formatter()
    # example_7_lambda_formatter()
    # example_8_chatbot_scenario()

    print("\n" + "=" * 80)
    print("✅ 所有示例展示完成")
    print("=" * 80)
