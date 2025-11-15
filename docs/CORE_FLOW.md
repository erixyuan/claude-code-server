# 核心主链路文档

一个简洁清晰的系统主链路说明，帮助快速理解代码结构。

## 📦 项目结构

```
claude-code-server/
├── claude_code_server/      # 核心库
│   ├── client.py            # Claude SDK 客户端（最底层）
│   ├── agent.py             # 高级 Agent（推荐使用）
│   ├── simple_agent.py      # 简单 Agent（无会话版本）
│   ├── session.py           # 会话管理
│   ├── types.py             # 类型定义
│   ├── exceptions.py        # 异常定义
│   └── formatters.py        # 消息格式化器
│
├── claude_code_server_api/  # FastAPI 服务器
│   ├── server.py            # API 服务器
│   ├── models.py            # API 模型
│   ├── config.py            # 服务器配置
│   └── tasks.py             # 异步任务
│
└── examples/                # 使用示例
    ├── agent_example.py
    └── webhook_bot.py
```

## 🔄 核心链路

### 链路 1: 直接使用客户端（底层 API）

最简单的使用方式：

```
用户消息
   ↓
ClaudeClient.chat()
   ↓
_build_options()          # 构建 SDK 选项
   ↓
_run_query()              # 调用 claude-agent-sdk
   ↓
_parse_response()         # 解析响应
   ↓
返回 ClaudeResponse
```

**代码示例：**
```python
from claude_code_server import ClaudeClient

client = ClaudeClient()
response = client.chat("你好")
print(response.content)
```

**关键文件：** `claude_code_server/client.py`

---

### 链路 2: 使用 Agent（高级 API，推荐）

自动管理会话的方式：

```
用户消息 + user_id
   ↓
ClaudeAgent.chat()
   ↓
1. 获取或创建会话        # SessionManager
   ↓
2. 格式化消息            # message_formatter（可选）
   ↓
3. 获取 Claude 会话 ID   # 从上次对话中
   ↓
4. 调用 ClaudeClient     # 发送消息
   ↓
5. 更新 Claude 会话 ID   # 保存新的会话 ID
   ↓
6. 保存对话历史          # SessionManager
   ↓
返回 ClaudeResponse
```

**代码示例：**
```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()

# 第一轮对话
response1 = agent.chat("我叫张三", user_id="alice")

# 第二轮对话（自动记住上下文）
response2 = agent.chat("我叫什么", user_id="alice")
# 回复: "你叫张三"
```

**关键文件：** `claude_code_server/agent.py`

---

### 链路 3: FastAPI 服务器（Web API）

通过 HTTP 接口使用：

```
HTTP POST /chat
   ↓
ServerConfig 加载配置      # config.yaml
   ↓
创建 ClaudeAgent           # 使用配置
   ↓
调用 agent.chat()          # 链路 2
   ↓
返回 JSON 响应
```

**API 示例：**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好",
    "user_id": "alice"
  }'
```

**关键文件：** `claude_code_server_api/server.py`

---

## 🧩 核心组件详解

### 1. ClaudeClient (client.py)

**职责：** 封装 claude-agent-sdk，提供同步接口

**核心方法：**
- `chat()` - 发送消息
- `_run_query()` - 异步转同步
- `_build_options()` - 构建 SDK 选项
- `_parse_response()` - 解析响应

**关键逻辑：**
```python
# SDK 的 query 是异步生成器
async for msg in query(prompt=message, options=options):
    messages.append(msg)

# 提取 AssistantMessage 中的文本内容
for msg in messages:
    if type(msg).__name__ == 'AssistantMessage':
        for block in msg.content:
            if hasattr(block, 'text'):
                content_parts.append(block.text)
```

---

### 2. ClaudeAgent (agent.py)

**职责：** 提供高级接口，自动管理会话

**核心方法：**
- `chat()` - 发送消息（6个步骤）
- `get_conversation_history()` - 获取历史
- `clear_session()` - 清除会话

**会话管理流程：**
```python
# 1. 用户 ID → 会话 ID
session_id = f"user_{user_id}"

# 2. 会话 ID → Claude 会话 ID
session = session_manager.get_or_create_session(session_id)
claude_session_id = session.claude_session_id

# 3. 发送消息时使用 Claude 会话 ID
response = client.chat(message, claude_session_id=claude_session_id)

# 4. 保存新的 Claude 会话 ID
new_session_id = response.metadata["claude_session_id"]
session_manager.update_claude_session_id(session_id, new_session_id)
```

---

### 3. SessionManager (session.py)

**职责：** 管理用户会话和对话历史

**核心方法：**
- `get_or_create_session()` - 获取或创建会话
- `add_message()` - 添加消息到历史
- `update_claude_session_id()` - 更新 Claude 会话 ID

**存储后端：**
- `InMemorySessionStore` - 内存存储（开发）
- `RedisSessionStore` - Redis 存储（生产）
- `FileSessionStore` - 文件存储（持久化）

---

## 🎯 关键概念

### 会话 ID 的三层映射

```
用户 ID (alice)
   ↓
会话 ID (user_alice)           ← 我们的内部 ID
   ↓
Claude 会话 ID (uuid)          ← Claude SDK 的会话 ID
```

**为什么需要三层？**
1. **用户 ID** - 业务层标识（如飞书用户 ID）
2. **会话 ID** - 我们的会话管理（可以一个用户多个会话）
3. **Claude 会话 ID** - SDK 内部使用（保持对话上下文）

---

### 消息流转

```
用户消息
   ↓
[格式化器] (可选)
   ↓
"以下是user_id=alice发过来的飞书消息: 你好"
   ↓
[Claude SDK]
   ↓
AssistantMessage(content=[TextBlock(text="你好！...")])
   ↓
[解析器]
   ↓
"你好！..."
   ↓
返回给用户
```

---

## 📝 配置文件 (config.yaml)

核心配置项：

```yaml
# 工作目录（Claude 在此目录执行命令）
working_directory: "/path/to/project"

# Claude 配置
claude_bin: "claude"
model: "claude-sonnet-4-5"
permission_mode: "acceptEdits"

# 会话存储
session_store_type: "memory"  # memory | redis | file

# 消息格式化
message_formatter: "feishu"   # simple | feishu | imessage

# API 配置
host: "0.0.0.0"
port: 8000
```

---

## 🚀 使用场景

### 场景 1: Python 应用直接集成

```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()
response = agent.chat("帮我分析代码", user_id="developer")
```

### 场景 2: Web 服务 (FastAPI)

```bash
python start_server.py
# 访问 http://localhost:8000/docs
```

### 场景 3: 聊天机器人 (飞书/Slack)

```python
@app.post("/webhook")
async def handle_message(data: dict):
    response = agent.chat(
        data["message"],
        user_id=data["user_id"]
    )
    return {"reply": response.content}
```

---

## 🔧 扩展点

### 1. 自定义消息格式化器

```python
def my_formatter(message, user_id, metadata):
    return f"[{user_id}] {message}"

agent = ClaudeAgent(message_formatter=my_formatter)
```

### 2. 自定义会话存储

```python
class MySessionStore(SessionStore):
    def save(self, session_id, data):
        # 保存到数据库
        pass

agent = ClaudeAgent(session_store=MySessionStore())
```

### 3. 自定义配置

```python
config = ClaudeConfig(
    model="claude-sonnet-4-5",
    permission_mode="acceptEdits",
    allowed_tools=["Read", "Write"],
    working_directory="/my/project"
)

agent = ClaudeAgent(config=config)
```

---

## 📊 数据流图

```
┌─────────────────────────────────────────────────────────┐
│                      用户应用                             │
│  (Web App / Bot / CLI / API Client)                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              ClaudeAgent (高级接口)                       │
│  • 自动会话管理                                           │
│  • 对话历史                                              │
│  • 消息格式化                                            │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│            ClaudeClient (底层接口)                        │
│  • 调用 claude-agent-sdk                                │
│  • 异步转同步                                            │
│  • 响应解析                                              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│           claude-agent-sdk (官方 SDK)                    │
│  • 调用 Claude API                                       │
│  • 工具执行                                              │
│  • 会话管理                                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🎓 学习路径

推荐的代码阅读顺序：

1. **types.py** - 了解数据结构
   - ClaudeConfig
   - ClaudeResponse
   - ClaudeMessage

2. **client.py** - 理解底层实现
   - 如何调用 SDK
   - 如何解析响应
   - 如何处理异步

3. **session.py** - 理解会话管理
   - 会话的创建和存储
   - 历史记录的管理
   - 会话 ID 的映射

4. **agent.py** - 理解高级接口
   - 如何组合各个组件
   - 完整的对话流程
   - 会话的自动管理

5. **server.py** - 理解 Web 服务
   - 如何暴露 HTTP API
   - 如何处理并发请求
   - 如何配置服务器

---

## 💡 常见问题

### Q1: 为什么需要 ClaudeAgent 和 ClaudeClient 两层？

**A:** 分层设计，各司其职：
- `ClaudeClient` - 纯粹的 SDK 封装，无状态
- `ClaudeAgent` - 会话管理，有状态

### Q2: 会话 ID 如何工作？

**A:** 三层映射：
```
用户 ID → 会话 ID → Claude 会话 ID
alice → user_alice → uuid-xxxx-xxx
```

### Q3: 如何保持对话上下文？

**A:** 通过 `resume` 参数：
```python
# 第一次对话，SDK 返回 session_id
options = ClaudeAgentOptions(...)
response = query(..., options)
session_id = response.session_id

# 第二次对话，传入之前的 session_id
options = ClaudeAgentOptions(resume=session_id)
response = query(..., options)
```

### Q4: 如何自定义消息格式？

**A:** 使用消息格式化器：
```python
agent = ClaudeAgent(
    message_formatter=lambda msg, uid, meta: f"[{uid}] {msg}"
)
```

---

## 🔗 相关文件

- 核心代码：`claude_code_server/`
- API 服务：`claude_code_server_api/`
- 使用示例：`examples/`
- 配置文件：`config.yaml`

---

**Simple is better than complex. Readability counts.** 🐍

阅读愉快！

