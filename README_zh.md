# Claude Code Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

一个使用官方 Claude Agent SDK 与 Claude 交互的 Python 库。将 Claude 转变为强大的后端服务，支持聊天机器人、自动化工作流和 AI 代理系统。

[English](README.md) | 简体中文

## 🎯 这是什么？

**Claude Code Server** 使用官方 Claude Agent SDK 提供简洁的 Python API，使您能够：

- ✅ 构建由 Claude 驱动的聊天机器人（Slack、Discord、飞书/Lark、微信等）
- ✅ 创建具有会话管理的多用户 AI 代理服务
- ✅ 自动化代码审查、分析和生成工作流
- ✅ 以编程方式利用 Claude 的所有功能
- ✅ 在多轮对话中维护上下文

## 🚀 快速开始

### 前置要求

- Python 3.11+
- Claude Agent SDK

### 安装

```bash
# 从源码安装
git clone https://github.com/viralt/claude-code-server.git
cd claude-code-server
pip install -e .
```

### 基础用法

```python
from claude_code_server import ClaudeAgent

# 创建代理（自动处理会话）
agent = ClaudeAgent()

# 发送消息 - 会话由 user_id 自动管理
response1 = agent.chat("我的名字是 Alice", user_id="alice_123")
response2 = agent.chat("我的名字是什么？", user_id="alice_123")

print(response2.content)  # "你的名字是 Alice"
```

### 高级用法

```python
from claude_code_server import ClaudeClient, ClaudeConfig

# 使用自定义配置创建客户端
client = ClaudeClient(
    config=ClaudeConfig(output_format="json", timeout=60)
)

# 发送消息
response = client.chat("你好，Claude！")
print(response.content)
```

## 📚 核心概念

### ClaudeAgent（推荐）⭐

**具有自动会话管理的高级 API**。非常适合聊天机器人和多用户应用程序。

```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()

# 自动处理每个用户的会话
response = agent.chat("你好！", user_id="user_123")
response = agent.chat("继续...", user_id="user_123")  # 记住上下文

# 获取对话历史
history = agent.get_conversation_history("user_123")

# 清除会话
agent.clear_session("user_123")
```

**主要特性：**
- ✅ 使用官方 Claude Agent SDK
- ✅ 自动管理 Claude 会话 ID
- ✅ 按用户跟踪对话
- ✅ 内置消息历史
- ✅ 简单的 API - 只需提供 user_id

### ClaudeClient（低级）

直接访问 Claude SDK，用于高级用例。

```python
from claude_code_server import ClaudeClient, ClaudeConfig

client = ClaudeClient(
    config=ClaudeConfig(
        output_format="json",
        timeout=120,
        allowed_tools=["Read", "Grep"],
    )
)

response = client.chat("你好")
```

### SessionManager

管理多用户的对话会话。

```python
from claude_code_server import SessionManager, InMemorySessionStore

# 内存存储（用于开发）
manager = SessionManager(store=InMemorySessionStore())

# 创建会话
session = manager.create_session("session_id", user_id="user_123")

# 添加消息
manager.add_message("session_id", "user", "你好")
manager.add_message("session_id", "assistant", "你好！")

# 获取历史
history = manager.get_conversation_history("session_id")
```

**存储后端：**
- `InMemorySessionStore` - 用于开发/测试
- `RedisSessionStore` - 用于生产环境（需要 redis）

### 配置选项

```python
from claude_code_server import ClaudeConfig, OutputFormat, PermissionMode

config = ClaudeConfig(
    output_format=OutputFormat.JSON,              # text, json, streaming-json
    permission_mode=PermissionMode.ACCEPT_EDITS,  # default, acceptEdits, bypassPermissions, plan
    allowed_tools=["Read", "Write", "Bash"],      # 限制 Claude 可以使用的工具
    timeout=300,                                  # 超时时间（秒）
    working_directory="/path/to/project",         # Claude 的工作目录
    append_system_prompt="自定义指令",             # 附加系统提示
    model="claude-sonnet-4-5",                    # 模型选择
)
```

## 🎯 使用场景

### 1. 飞书/Lark 聊天机器人

```python
from fastapi import FastAPI, Request
from claude_code_server import ClaudeAgent

app = FastAPI()
agent = ClaudeAgent()

@app.post("/feishu/webhook")
async def handle_feishu_message(request: Request):
    data = await request.json()
    user_id = data["sender"]["user_id"]
    message = data["message"]["content"]

    # 简单！会话自动管理
    response = agent.chat(message, user_id=user_id)

    # 发送回飞书
    return {"text": response.content}
```

### 2. 自动化代码审查

```python
def review_code(file_path: str) -> str:
    client = ClaudeClient(
        config=ClaudeConfig(
            allowed_tools=["Read", "Grep"],
            permission_mode=PermissionMode.ACCEPT_EDITS,
        )
    )

    prompt = f"审查 {file_path} 中的代码，检查最佳实践、错误和改进建议。"
    response = client.chat(prompt)
    return response.content
```

### 3. 多用户 AI 服务

```python
from claude_code_server import ClaudeAgent

class AIService:
    def __init__(self):
        self.agent = ClaudeAgent()

    def handle_user_message(self, user_id: str, message: str) -> str:
        response = self.agent.chat(message, user_id=user_id)
        return response.content

# 使用 - 每个用户的会话自动管理！
service = AIService()
response = service.handle_user_message("alice", "帮我处理 Python 问题")
```

## 📖 示例

查看 [`examples/`](./examples) 目录获取完整的工作示例：

- **simple_chat.py** - 基本聊天交互
- **multi_turn_chat.py** - 带记忆的对话
- **webhook_bot.py** - Webhook 聊天机器人模式
- **agent_example.py** - ClaudeAgent 完整示例

运行示例：

```bash
python examples/simple_chat.py
python examples/agent_example.py
```

## 🏗️ 架构

```
┌─────────────────────┐
│  你的应用程序        │
│  (聊天机器人/服务)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Claude Code Server  │
│  - ClaudeClient     │
│  - ClaudeAgent      │
│  - SessionManager   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Claude Agent SDK    │
│  (官方 SDK)         │
└─────────────────────┘
```

## 🔧 开发

### 设置

```bash
# 克隆仓库
git clone https://github.com/viralt/claude-code-server.git
cd claude-code-server

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行基础测试脚本
python test_simple.py
```

## ⚙️ 配置

### 会话存储

**内存存储（开发）：**
```python
from claude_code_server import SessionManager, InMemorySessionStore

manager = SessionManager(store=InMemorySessionStore())
```

**Redis（生产）：**
```python
import redis
from claude_code_server import SessionManager, RedisSessionStore

redis_client = redis.Redis(host='localhost', port=6379, db=0)
manager = SessionManager(
    store=RedisSessionStore(redis_client, ttl=3600)
)
```

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 基于 Anthropic 的官方 Claude Agent SDK 构建

## 📞 支持

- 🐛 [报告问题](https://github.com/viralt/claude-code-server/issues)
- 💬 [讨论](https://github.com/viralt/claude-code-server/discussions)

---

由 Viralt 团队用 ❤️ 打造
