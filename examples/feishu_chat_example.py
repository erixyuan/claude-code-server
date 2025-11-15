"""
飞书消息处理示例

演示如何使用飞书消息格式化器和 SYSTEM_PROMPT.md。
"""

from claude_code_server import ClaudeAgent, ClaudeConfig, get_formatter

# 配置 Claude
config = ClaudeConfig(
    working_directory="/path/to/your/project",  # 设置你的工作目录
    timeout=300,
)

# 获取飞书消息格式化器
formatter = get_formatter("feishu")

# 创建 Agent
agent = ClaudeAgent(
    config=config,
    message_formatter=formatter,
)

# 模拟飞书消息
def handle_feishu_message(message: str, user_id: str):
    """
    处理飞书消息。
    
    Args:
        message: 用户消息内容
        user_id: 用户ID
    """
    print(f"\n📨 收到飞书消息:")
    print(f"   用户ID: {user_id}")
    print(f"   消息内容: {message}")
    
    # 发送给 Claude（会自动格式化为：以下是user_id=xxx发过来的飞书消息: xxx）
    response = agent.chat(
        message=message,
        user_id=user_id,
    )
    
    print(f"\n🤖 Claude 回复:")
    print(f"   {response.content}")
    
    return response


# 示例使用
if __name__ == "__main__":
    # 示例1：简单问候
    handle_feishu_message(
        message="我叫eric",
        user_id="2f3b45d586d43978b712950b",
    )
    
    # 示例2：后续对话（会记住之前的对话）
    handle_feishu_message(
        message="我刚才说我叫什么名字？",
        user_id="2f3b45d586d43978b712950b",
    )

