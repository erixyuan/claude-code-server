#!/usr/bin/env python3
"""
简单的测试脚本 - 验证 Claude Agent SDK 实现
"""

from claude_code_server import ClaudeClient, ClaudeAgent, ClaudeConfig

def main():
    print("=" * 80)
    print("测试 Claude Code Server (SDK 版本)")
    print("=" * 80)
    
    # 测试 1: ClaudeClient
    print("\n测试 1: ClaudeClient 基础功能")
    print("-" * 80)
    try:
        config = ClaudeConfig(
            working_directory=".",
            debug_print_command=True,
        )
        client = ClaudeClient(config=config)
        response = client.chat("Hello! Please respond with 'Hi there!'")
        print(f"✅ 响应: {response.content[:100]}")
        print(f"✅ 成功: {response.success}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    # 测试 2: ClaudeAgent
    print("\n\n测试 2: ClaudeAgent 多轮对话")
    print("-" * 80)
    try:
        agent = ClaudeAgent(config=config)
        
        # 第一轮
        response1 = agent.chat("My name is Alice", user_id="test_user")
        print(f"✅ 第一轮: {response1.content[:100]}")
        
        # 第二轮
        response2 = agent.chat("What's my name?", user_id="test_user")
        print(f"✅ 第二轮: {response2.content[:100]}")
        
        # 历史
        history = agent.get_conversation_history("test_user")
        print(f"✅ 历史记录: {len(history)} 条消息")
        
        agent.clear_session("test_user")
        print("✅ 会话已清除")
        
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    main()

