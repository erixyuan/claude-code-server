# Claude Code Server 技术架构文档

## 1. 概述

Claude Code Server 是一个 Python 库，提供对 Claude Code CLI 的程序化封装，使其能够作为后端服务在多用户、多会话场景下使用。本文档详细描述了系统的技术架构、核心组件和数据流。

### 1.1 项目定位

- **核心功能**: 将 Claude Code CLI 封装为可编程 API
- **使用场景**: 聊天机器人、自动化工作流、AI Agent 系统
- **关键特性**: 多用户会话管理、对话上下文保持、灵活的存储后端

### 1.2 技术栈

- **核心语言**: Python 3.11+
- **主要框架**: FastAPI (可选的 Web 服务)
- **依赖工具**: Claude Code CLI
- **数据模型**: Pydantic
- **存储支持**: 内存、文件系统、Redis

## 2. 整体架构

### 2.1 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application Layer)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 飞书/Lark Bot │  │  Slack Bot   │  │  自定义应用   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API 层 (Optional)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            FastAPI Server (claude_code_server_api)   │   │
│  │  - RESTful API Endpoints                             │   │
│  │  - 三种响应模式: Sync / Stream / Async               │   │
│  │  - API Key 认证                                      │   │
│  │  - CORS 支持                                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  业务逻辑层 (Business Layer)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ClaudeAgent (High-level API)            │   │
│  │  - 自动会话管理                                      │   │
│  │  - 用户/会话映射                                     │   │
│  │  - 对话历史追踪                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌─────────────────────────────┐  ┌───────────────────────────┐
│    会话管理层                │  │     客户端层               │
│  ┌────────────────────────┐ │  │ ┌───────────────────────┐ │
│  │   SessionManager       │ │  │ │  ClaudeCodeClient     │ │
│  │  - 会话生命周期        │ │  │ │  - CLI 调用封装       │ │
│  │  - 历史记录管理        │ │  │ │  - 响应解析           │ │
│  │  - UUID 映射           │ │  │ │  - 超时/重试          │ │
│  └────────────────────────┘ │  │ └───────────────────────┘ │
└─────────────────────────────┘  └───────────────────────────┘
                │                              │
                ▼                              ▼
┌─────────────────────────────┐  ┌───────────────────────────┐
│      存储层                  │  │   Claude CLI 层            │
│  ┌────────────────────────┐ │  │ ┌───────────────────────┐ │
│  │ SessionStore Protocol  │ │  │ │  Claude Code CLI      │ │
│  │  - InMemoryStore       │ │  │ │  - 子代理 (Sub-agents)│ │
│  │  - FileStore           │ │  │ │  - MCP 工具           │ │
│  │  - RedisStore          │ │  │ │  - 文件操作           │ │
│  └────────────────────────┘ │  │ └───────────────────────┘ │
└─────────────────────────────┘  └───────────────────────────┘
```

### 2.2 核心设计原则

1. **关注点分离**: 客户端、会话管理、存储各司其职
2. **可扩展性**: 基于协议的存储后端，易于扩展
3. **高可用性**: 支持分布式存储 (Redis)
4. **用户友好**: 提供高层 API (ClaudeAgent) 和低层 API (ClaudeCodeClient)

## 3. 核心组件详解

### 3.1 ClaudeCodeClient (客户端层)

**文件位置**: `claude_code_server/client.py`

**职责**:
- Claude CLI 的直接封装
- 构建和执行 CLI 命令
- 解析 CLI 输出
- 处理超时和错误

**关键接口**:
```python
class ClaudeCodeClient:
    def __init__(self, config: ClaudeConfig = None)
    def chat(self, message: str, claude_session_id: str = None) -> ClaudeResponse
    def get_version(self) -> str
    def _execute_command(self, cmd: list[str]) -> ClaudeResponse
```

**CLI 命令构建**:
```bash
claude -p "用户消息" \
  --output-format json \
  --resume {uuid} \
  --permission-mode acceptEdits \
  --allowedTools Read,Write,Bash \
  --working-directory /path/to/project
```

**关键特性**:
- 自动验证 Claude CLI 安装
- 支持自定义工作目录 (CWD)
- 工具白名单限制
- JSON 输出格式解析
- 环境变量注入

### 3.2 SessionManager (会话管理层)

**文件位置**: `claude_code_server/session.py`

**职责**:
- 管理用户会话生命周期
- 维护对话历史
- 映射用户 Session ID 到 Claude UUID
- 提供会话持久化接口

**数据模型**:
```python
class SessionData(BaseModel):
    session_id: str                           # 用户会话 ID
    user_id: Optional[str]                    # 用户 ID
    conversation_history: list[ClaudeMessage] # 对话历史
    metadata: dict[str, Any]                  # 元数据
    created_at: datetime                      # 创建时间
    last_activity: datetime                   # 最后活动
    claude_session_id: Optional[str]          # Claude UUID (关键!)
```

**Session ID 双层架构**:

| 层级 | ID 类型 | 示例 | 用途 |
|------|---------|------|------|
| 应用层 | User Session ID | `"user_alice"`, `"session_123"` | 应用识别用户/会话 |
| Claude 层 | Claude UUID | `"550e8400-e29b-41d4-a716-446655440000"` | Claude CLI 内部会话 |

**映射流程**:
```
用户首次消息 → 创建 User Session
                ↓
           调用 Claude CLI
                ↓
      返回 Claude UUID (metadata)
                ↓
     存储到 SessionData.claude_session_id
                ↓
用户后续消息 → 读取 Claude UUID → 传递给 CLI (--resume flag)
```

**关键方法**:
```python
class SessionManager:
    def create_session(self, session_id: str, user_id: str = None) -> SessionData
    def get_session(self, session_id: str) -> Optional[SessionData]
    def add_message(self, session_id: str, role: str, content: str)
    def update_claude_session_id(self, session_id: str, claude_session_id: str)
    def get_conversation_history(self, session_id: str) -> list[ClaudeMessage]
    def delete_session(self, session_id: str)
```

### 3.3 ClaudeAgent (业务逻辑层)

**文件位置**: `claude_code_server/agent.py`

**职责**:
- 提供高层业务 API
- 自动管理会话生命周期
- 简化用户调用流程
- 集成 Client 和 SessionManager

**核心工作流**:
```python
# 用户视角 (简单)
agent = ClaudeAgent()
response = agent.chat("Hello", user_id="alice")

# 内部流程
1. 根据 user_id 派生 session_id (默认: "user_{user_id}")
2. 检查会话是否存在，不存在则创建
3. 从 SessionData 读取 claude_session_id
4. 调用 client.chat(message, claude_session_id)
5. 解析响应，提取新的 claude_session_id (如果有)
6. 更新 SessionData.claude_session_id
7. 添加消息到会话历史
8. 返回响应
```

**关键特性**:
- 自动 Session ID 派生 (`user_{user_id}` 或自定义)
- 透明的 Claude UUID 管理
- 对话历史自动记录
- 支持自定义 SessionStore 后端

**适用场景**:
- 多用户聊天机器人
- 需要保持上下文的 AI 服务
- 不关心底层细节的快速开发

### 3.4 存储后端 (SessionStore Protocol)

**文件位置**: `claude_code_server/session.py`, `claude_code_server/file_session_store.py`

**设计模式**: Protocol-based (Duck Typing)

**接口定义**:
```python
class SessionStore(Protocol):
    def get(self, session_id: str) -> Optional[SessionData]
    def save(self, session: SessionData) -> None
    def delete(self, session_id: str) -> None
    def exists(self, session_id: str) -> bool
```

**实现对比**:

| 后端 | 特性 | 适用场景 | 持久化 | 分布式 |
|------|------|----------|--------|--------|
| **InMemorySessionStore** | 字典存储，进程内 | 开发/测试 | ❌ | ❌ |
| **FileSessionStore** | JSON 文件持久化 | 单实例生产 | ✅ | ❌ |
| **RedisSessionStore** | Redis + TTL | 多实例生产 | ✅ | ✅ |

**RedisSessionStore 特性**:
```python
class RedisSessionStore:
    def __init__(self, redis_client: redis.Redis, ttl: int = 3600)
    # 自动过期 (TTL)
    # 分布式共享
    # 高性能读写
```

### 3.5 配置系统

**ClaudeConfig** (`claude_code_server/types.py:46`):
```python
class ClaudeConfig(BaseModel):
    output_format: OutputFormat = OutputFormat.JSON
    permission_mode: PermissionMode = PermissionMode.ACCEPT_EDITS
    allowed_tools: Optional[list[str]] = None
    timeout: int = 300
    max_retries: int = 3
    working_directory: Optional[str] = None
    append_system_prompt: Optional[str] = None
    model: Optional[str] = None
    env: Optional[dict[str, str]] = None
    disable_prompt_caching: bool = True
```

**ServerConfig** (`claude_code_server_api/config.py`):
- YAML 配置文件支持
- 工作目录设置
- 存储后端选择
- API 认证配置
- CORS 策略

## 4. FastAPI Server 架构

### 4.1 服务端组件

**文件位置**: `claude_code_server_api/server.py`

**核心架构**:
```
FastAPI Application
├── Middleware (CORS)
├── Dependencies (API Key 验证)
├── Lifespan (启动/关闭钩子)
├── TaskManager (异步任务管理)
└── Routes
    ├── /health (健康检查)
    ├── /chat (同步聊天)
    ├── /chat/stream (SSE 流式)
    ├── /chat/async (异步任务)
    ├── /task/{task_id} (任务状态)
    ├── /session/{session_id}/history (历史记录)
    └── /session/{session_id} (删除会话)
```

### 4.2 三种响应模式

#### 模式 1: Sync (同步)
**端点**: `POST /chat`

**特点**:
- 阻塞式等待完整响应
- 简单易用
- 适合快速响应场景

**流程**:
```
请求 → 执行 agent.chat() → 等待完成 → 返回完整响应
```

**响应格式**:
```json
{
  "content": "Claude 的回复内容",
  "session_id": "user_alice",
  "claude_session_id": "550e8400-...",
  "success": true,
  "metadata": {...}
}
```

#### 模式 2: Stream (流式)
**端点**: `POST /chat/stream`

**特点**:
- Server-Sent Events (SSE) 协议
- 实时推送响应片段
- 适合 UI 实时反馈

**流程**:
```
请求 → 返回 SSE 流 → 逐步推送内容 → 发送 done 事件
```

**事件流**:
```
event: message
data: Claude 的回复内容

event: done
data: {"session_id": "user_alice", "claude_session_id": "550e8400-..."}
```

**注意**: 当前实现为"模拟流式"（一次性推送），因为 Claude CLI 尚不支持真正的流式输出。

#### 模式 3: Async (异步)
**端点**: `POST /chat/async` + `GET /task/{task_id}`

**特点**:
- 立即返回任务 ID
- 后台处理
- 轮询或 Webhook 通知

**流程**:
```
1. 提交任务 → 返回 task_id
2. 后台线程池执行
3. 轮询 /task/{task_id} 获取状态
```

**任务状态**:
```json
{
  "task_id": "abc123",
  "status": "completed",  // processing/completed/failed
  "result": {
    "content": "...",
    "success": true
  },
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:00:30Z"
}
```

### 4.3 TaskManager (任务管理)

**文件位置**: `claude_code_server_api/tasks.py`

**职责**:
- 异步任务调度
- 任务状态追踪
- 结果缓存
- 过期任务清理

**核心结构**:
```python
class BackgroundTask(BaseModel):
    task_id: str
    status: str  # "processing", "completed", "failed"
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class TaskManager:
    def __init__(self, max_workers: int = 5)
    def create_task(self, agent, message, user_id, session_id) -> str
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]
    async def cleanup_old_tasks(self, max_age_seconds: int = 3600)
```

**执行流程**:
```
1. create_task() → 生成 UUID task_id
2. 提交到 ThreadPoolExecutor
3. 执行 agent.chat() (在独立线程)
4. 完成后更新 _tasks 字典
5. 定时清理任务 (每 5 分钟)
```

## 5. 数据流详解

### 5.1 完整请求流程

```
[用户] "What's my name?"
   │
   ▼
[FastAPI] /chat endpoint
   │
   ▼
[ClaudeAgent] agent.chat(message, user_id="alice")
   │
   ├─→ [SessionManager] get_session("user_alice")
   │   └─→ [SessionStore] get("user_alice")
   │       └─→ 返回 SessionData {
   │             session_id: "user_alice",
   │             claude_session_id: "550e8400-...",
   │             conversation_history: [...]
   │           }
   │
   ├─→ [ClaudeCodeClient] chat(message, claude_session_id="550e8400-...")
   │   │
   │   ├─→ 构建命令:
   │   │   ["claude", "-p", "What's my name?",
   │   │    "--output-format", "json",
   │   │    "--resume", "550e8400-..."]
   │   │
   │   ├─→ subprocess.run(cmd, cwd=working_directory, timeout=300)
   │   │
   │   └─→ 解析输出:
   │       {
   │         "content": "Your name is Alice",
   │         "metadata": {"claude_session_id": "550e8400-..."}
   │       }
   │
   ├─→ [SessionManager] add_message("user_alice", "user", "What's my name?")
   │                     add_message("user_alice", "assistant", "Your name is Alice")
   │                     update_claude_session_id("user_alice", "550e8400-...")
   │   └─→ [SessionStore] save(session_data)
   │
   └─→ 返回 ClaudeResponse
       └─→ [FastAPI] 序列化为 JSON 响应
           └─→ [用户] 收到回复
```

### 5.2 Session ID 映射流程

**场景**: 用户 Alice 首次对话

```
Step 1: 用户发送第一条消息
  user_id: "alice"
  message: "Hello, my name is Alice"

Step 2: ClaudeAgent 创建会话
  session_id = f"user_{user_id}" = "user_alice"
  SessionManager.create_session("user_alice", user_id="alice")
  → SessionData {
      session_id: "user_alice",
      claude_session_id: None,  ← 还没有 Claude UUID
      conversation_history: []
    }

Step 3: 调用 Claude CLI (无 --resume)
  claude -p "Hello, my name is Alice" --output-format json

Step 4: Claude 返回响应 + UUID
  {
    "content": "Hello Alice! How can I help you?",
    "metadata": {
      "claude_session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }

Step 5: 更新会话数据
  SessionData {
    session_id: "user_alice",
    claude_session_id: "550e8400-...",  ← 已更新
    conversation_history: [
      {role: "user", content: "Hello, my name is Alice"},
      {role: "assistant", content: "Hello Alice! ..."}
    ]
  }

Step 6: 用户发送第二条消息
  message: "What's my name?"

Step 7: 从会话读取 Claude UUID
  session = SessionManager.get_session("user_alice")
  claude_session_id = session.claude_session_id  # "550e8400-..."

Step 8: 调用 Claude CLI (带 --resume)
  claude -p "What's my name?" \
    --output-format json \
    --resume "550e8400-e29b-41d4-a716-446655440000"

Step 9: Claude 返回 (有上下文)
  {
    "content": "Your name is Alice",
    "metadata": {...}
  }
```

### 5.3 存储层交互

**写入流程** (SessionManager → SessionStore):
```python
# 1. 创建会话
session_data = SessionData(
    session_id="user_alice",
    user_id="alice",
    ...
)
store.save(session_data)

# 2. 添加消息
session = store.get("user_alice")
session.conversation_history.append(message)
session.last_activity = datetime.now()
store.save(session)  # 覆盖保存

# 3. 更新 Claude UUID
session.claude_session_id = "550e8400-..."
store.save(session)
```

**读取流程**:
```python
# 1. 检查会话存在
if store.exists("user_alice"):
    session = store.get("user_alice")

# 2. 获取历史
history = session.conversation_history

# 3. 获取 Claude UUID
claude_uuid = session.claude_session_id
```

**Redis 存储细节**:
```python
# 键名: "session:{session_id}"
# 值: JSON 序列化的 SessionData
# TTL: 可配置 (默认 3600 秒)

redis.setex(
    f"session:user_alice",
    ttl=3600,
    value=session_data.model_dump_json()
)
```

## 6. 错误处理与容错

### 6.1 异常层次

```
ClaudeCodeError (基础异常)
├── ClaudeExecutionError (CLI 执行失败)
│   ├── return_code: int
│   ├── stderr: str
│   └── cmd: list[str]
├── SessionNotFoundError (会话不存在)
├── InvalidConfigError (配置无效)
└── TimeoutError (执行超时)
```

### 6.2 重试机制

**客户端层**:
```python
config = ClaudeConfig(
    max_retries=3,      # 最大重试次数
    timeout=300         # 单次超时 (秒)
)
```

**重试逻辑**:
- CLI 非零退出码 → 重试
- 超时 → 重试
- 网络错误 → 重试
- 解析错误 → 不重试 (立即失败)

### 6.3 优雅降级

**服务端**:
- Claude CLI 不可用 → 返回 503 Service Unavailable
- 存储后端故障 → 降级到 InMemoryStore (如果可能)
- 任务队列满 → 返回 429 Too Many Requests

## 7. 安全与权限

### 7.1 工具限制

```python
config = ClaudeConfig(
    allowed_tools=["Read", "Grep"]  # 只允许读操作
)
```

**常见场景**:
- 代码审查: `["Read", "Grep"]`
- 代码生成: `["Read", "Write", "Edit"]`
- 完整权限: `None` (默认)

### 7.2 API 认证

**配置**:
```yaml
api_key: "your-secret-key-here"
allowed_users: ["alice", "bob"]  # 用户白名单
```

**请求头**:
```
X-API-Key: your-secret-key-here
```

### 7.3 工作目录隔离

```python
config = ClaudeConfig(
    working_directory="/path/to/sandbox"
)
```

**推荐做法**:
- 每个租户独立工作目录
- 使用 Docker 容器隔离
- 定期清理临时文件

## 8. 性能优化

### 8.1 并发控制

**TaskManager**:
```python
task_manager = TaskManager(
    max_workers=5  # 最大并发任务数
)
```

**建议配置**:
- 单核: `max_workers=2`
- 多核: `max_workers=CPU核心数`
- 生产: 根据负载测试调整

### 8.2 会话 TTL

**Redis 存储**:
```python
store = RedisSessionStore(
    redis_client,
    ttl=3600  # 1 小时后自动过期
)
```

**清理策略**:
- InMemoryStore: 无自动清理 (需手动调用)
- FileStore: 定期扫描过期文件
- RedisStore: 利用 Redis TTL 自动清理

### 8.3 缓存策略

**Prompt Caching**:
```python
config = ClaudeConfig(
    disable_prompt_caching=True  # 避免 cache_control 限制
)
```

**注意**: 当前建议禁用，避免触发 Claude API 限制。

## 9. 部署架构

### 9.1 单实例部署

```
┌─────────────────────────┐
│   FastAPI Server        │
│   ├─ ClaudeAgent        │
│   ├─ FileSessionStore   │
│   └─ TaskManager        │
└─────────────────────────┘
         │
         ▼
    Claude CLI
```

**适用场景**: 小型应用、开发测试

**限制**:
- 单点故障
- 无法水平扩展
- 会话不共享

### 9.2 多实例部署 (推荐生产)

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│  Instance1 │    │ Instance 2 │    │ Instance N │
│  FastAPI   │    │  FastAPI   │    │  FastAPI   │
└──────┬─────┘    └──────┬─────┘    └──────┬─────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Redis       │
                  │ (Session)    │
                  └──────────────┘
```

**优势**:
- 高可用性
- 负载均衡
- 会话共享 (Redis)
- 水平扩展

**配置要点**:
```yaml
session_store_type: redis
redis_url: redis://redis:6379/0
session_ttl: 3600
```

### 9.3 容器化部署

**Dockerfile 示例**:
```dockerfile
FROM python:3.11-slim

# 安装 Claude CLI
RUN curl -sSL https://code.claude.com/install.sh | sh

# 安装应用
COPY . /app
WORKDIR /app
RUN pip install -e ".[all]"

# 启动服务
CMD ["python", "start_server.py"]
```

**Docker Compose**:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 10. 监控与日志

### 10.1 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "claude_version": "1.2.3"
}
```

### 10.2 日志记录

**关键日志点**:
- CLI 命令执行
- 会话创建/销毁
- 错误和异常
- 任务状态变更

**日志级别**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 10.3 性能指标

**建议监控**:
- 请求 QPS
- 平均响应时间
- P95/P99 延迟
- 错误率
- 活跃会话数
- 任务队列长度

## 11. 常见问题与最佳实践

### 11.1 不要在 Claude Code 内运行

**问题**: 库会启动 Claude CLI 子进程，在 Claude Code 内运行会冲突。

**检测**:
```python
import os
if os.getenv("CLAUDECODE") or os.getenv("CLAUDE_CODE_ENTRYPOINT"):
    raise RuntimeError("不能在 Claude Code 内运行!")
```

### 11.2 正确设置工作目录

**问题**: Claude CLI 的文件操作基于 CWD，设置错误会找不到文件。

**解决**:
```python
config = ClaudeConfig(
    working_directory="/absolute/path/to/project"
)
```

### 11.3 会话 ID 管理

**问题**: 混淆 User Session ID 和 Claude UUID。

**最佳实践**:
- 使用 ClaudeAgent (自动管理)
- 或明确区分两种 ID
- 不要手动操作 Claude UUID

### 11.4 长时间任务

**问题**: 默认超时 300 秒，复杂任务可能超时。

**解决**:
```python
config = ClaudeConfig(
    timeout=600  # 增加到 10 分钟
)
# 或使用异步模式
response = await agent.chat_async(message, user_id)
```

### 11.5 生产环境存储

**问题**: InMemoryStore 重启丢失数据。

**解决**:
- 单实例: 使用 FileStore
- 多实例: 使用 RedisStore

## 12. 扩展开发

### 12.1 自定义 SessionStore

**实现接口**:
```python
from claude_code_server.session import SessionStore, SessionData

class PostgreSQLStore:
    def get(self, session_id: str) -> Optional[SessionData]:
        # 查询数据库
        pass

    def save(self, session: SessionData) -> None:
        # 写入数据库
        pass

    def delete(self, session_id: str) -> None:
        # 删除记录
        pass

    def exists(self, session_id: str) -> bool:
        # 检查存在
        pass
```

**使用**:
```python
store = PostgreSQLStore(connection_string)
agent = ClaudeAgent(session_store=store)
```

### 12.2 自定义中间件

**FastAPI 中间件**:
```python
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 记录请求
    response = await call_next(request)
    # 记录响应
    return response
```

### 12.3 Webhook 回调

**异步任务完成通知**:
```python
async def notify_webhook(task_id: str, result: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            webhook_url,
            json={"task_id": task_id, "result": result}
        )
```

## 13. 总结

### 13.1 核心设计亮点

1. **双层会话架构**: 优雅映射应用 Session ID 到 Claude UUID
2. **协议化存储**: 灵活扩展存储后端
3. **多层次 API**: 满足不同复杂度需求
4. **三种响应模式**: 适配各种应用场景

### 13.2 适用场景

- ✅ 企业聊天机器人集成 (飞书/Slack/钉钉)
- ✅ 自动化代码审查系统
- ✅ AI 辅助编程服务
- ✅ 多租户 SaaS 平台
- ✅ 工作流自动化引擎

### 13.3 技术栈要求

- Python 3.11+
- Claude Code CLI 已安装并认证
- Redis (可选，生产推荐)
- FastAPI (可选，如需 Web 服务)

---

**文档版本**: v1.0
**最后更新**: 2024-01
**维护者**: Viralt Team
