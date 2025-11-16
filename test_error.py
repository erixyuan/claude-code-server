#!/usr/bin/env python3
"""
测试脚本 - 检查错误日志
"""

import httpx
import time

BASE_URL = "http://localhost:8000"

def test_chat_endpoint():
    """测试 /chat 端点"""
    print("=" * 60)
    print("测试 /chat 端点...")
    print("=" * 60)

    try:
        response = httpx.post(
            f"{BASE_URL}/chat",
            json={
                "message": "你好",
                "user_id": "test_user"
            },
            timeout=30.0
        )

        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

    except Exception as e:
        print(f"错误: {e}")

def test_chat_async_endpoint():
    """测试 /chat/async 端点"""
    print("\n" + "=" * 60)
    print("测试 /chat/async 端点...")
    print("=" * 60)

    try:
        response = httpx.post(
            f"{BASE_URL}/chat/async",
            json={
                "message": "你好",
                "user_id": "test_user"
            },
            timeout=30.0
        )

        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    # 先检查服务器是否运行
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        print(f"✅ 服务器正在运行: {response.json()}\n")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请先启动服务器: claude-code-server --config config.yaml")
        exit(1)

    test_chat_endpoint()
    test_chat_async_endpoint()
