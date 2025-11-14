# Claude Code Server API Guide

完整的 FastAPI 服务，包装 Claude Code CLI 为 RESTful API。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/eric/Project/viralt/claude-code-server

# 安装 server 依赖
pip install -e ".[server]"

# 或安装所有依赖
pip install -e ".[all]"
```

### 2. 配置

创建配置文件：

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`：

```yaml
# 关键配置
working_directory: "/Users/eric/Project/viralt/claude-code-server-test-folder"
claude_bin: "claude"
default_response_mode: "sync"  # sync/stream/async
```

### 3. 启动服务

```bash
python start_server.py

# 或指定配置
python start_server.py --config config.yaml

# 或指定端口
python start_server.py --port 8080

# 开发模式（auto-reload）
python start_server.py --reload
```

### 4. 访问 API

- **API 文档**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📡 API 端点

### 1. 同步聊天 (Sync)

**立即返回完整响应**

```bash
POST /chat

# Request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Claude!",
    "user_id": "alice"
  }'

# Response
{
  "content": "Hello! How can I help you?",
  "session_id": "user_alice",
  "claude_session_id": "uuid-here",
  "success": true,
  "metadata": {}
}
```

### 2. 流式聊天 (Stream)

**SSE 流式返回**

```bash
POST /chat/stream

# Request
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me a story",
    "user_id": "bob"
  }'

# Response (SSE stream)
event: message
data: Once upon a time...

event: done
data: {"session_id": "user_bob", "claude_session_id": "uuid"}
```

### 3. 异步聊天 (Async)

**立即返回 task_id，后台处理**

```bash
POST /chat/async

# Request
curl -X POST http://localhost:8000/chat/async \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Complex task",
    "user_id": "charlie"
  }'

# Response (immediate)
{
  "task_id": "task-uuid",
  "status": "processing",
  "message": "Task submitted successfully"
}

# Check status
GET /task/{task_id}

# Response
{
  "task_id": "task-uuid",
  "status": "completed",
  "result": {
    "content": "Task result here",
    "session_id": "user_charlie",
    ...
  },
  "created_at": "2025-11-14T12:00:00",
  "completed_at": "2025-11-14T12:01:30"
}
```

### 4. 获取对话历史

```bash
GET /session/{session_id}/history

# Request
curl http://localhost:8000/session/user_alice/history

# Response
{
  "session_id": "user_alice",
  "user_id": "alice",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-11-14T12:00:00"
    },
    {
      "role": "assistant",
      "content": "Hi!",
      "timestamp": "2025-11-14T12:00:05"
    }
  ],
  "total_messages": 2
}
```

### 5. 清除会话

```bash
DELETE /session/{session_id}

# Request
curl -X DELETE http://localhost:8000/session/user_alice
```

### 6. Health Check

```bash
GET /health

# Response
{
  "status": "healthy",
  "version": "0.1.0",
  "claude_version": "2.0.14 (Claude Code)"
}
```

## 🔧 配置选项

### 工作目录

指定 Claude CLI 的工作目录（重要！）：

```yaml
working_directory: "/path/to/your/project"
```

这样 Claude Code 会在指定目录运行，可以：
- 访问该目录的文件
- 使用该目录的 `.claude` 配置
- 隔离不同项目的环境

### 响应模式

三种模式，适用不同场景：

| 模式 | 返回方式 | 适用场景 |
|------|---------|---------|
| `sync` | 等待完成，一次返回 | 简单对话、同步调用 |
| `stream` | SSE 流式返回 | 需要实时反馈的 UI |
| `async` | 立即返回 task_id | 长时间任务、后台处理 |

**指定模式**：

```json
{
  "message": "Hello",
  "user_id": "alice",
  "response_mode": "async"  // 覆盖默认模式
}
```

### Session 存储

**InMemory（默认）**：
```yaml
session_store_type: "memory"
```
- 优点：简单，无需额外依赖
- 缺点：重启丢失，单机

**Redis（推荐生产）**：
```yaml
session_store_type: "redis"
redis_url: "redis://localhost:6379"
session_ttl: 3600  # 1 hour
```
- 优点：持久化，多实例共享
- 缺点：需要 Redis 服务

### 安全

**API Key 认证**：

```yaml
api_key: "your-secret-key-here"
```

客户端请求时需要带 header：

```bash
curl -H "X-API-Key: your-secret-key-here" \
  http://localhost:8000/chat
```

**限制用户**：

```yaml
allowed_users:
  - "alice"
  - "bob"
```

只允许指定 `user_id` 访问。

## 🎨 使用示例

### Python 客户端

```python
import requests

API_URL = "http://localhost:8000"

# 同步聊天
def chat_sync(message, user_id):
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": message, "user_id": user_id}
    )
    return response.json()["content"]

# 异步聊天
def chat_async(message, user_id):
    # 提交任务
    response = requests.post(
        f"{API_URL}/chat/async",
        json={"message": message, "user_id": user_id}
    )
    task_id = response.json()["task_id"]

    # 轮询状态
    import time
    while True:
        status = requests.get(f"{API_URL}/task/{task_id}").json()
        if status["status"] == "completed":
            return status["result"]["content"]
        elif status["status"] == "failed":
            raise Exception(status["error"])
        time.sleep(1)

# 使用
print(chat_sync("Hello!", "alice"))
```

### JavaScript/TypeScript 客户端

```typescript
// Sync chat
async function chatSync(message: string, userId: string) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId })
  });
  const data = await response.json();
  return data.content;
}

// Stream chat
async function chatStream(message: string, userId: string) {
  const response = await fetch('http://localhost:8000/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    console.log('Chunk:', chunk);
  }
}
```

## 🐳 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11

WORKDIR /app

# Install Claude CLI
RUN npm install -g @anthropic/claude-code

# Install app
COPY . .
RUN pip install -e ".[all]"

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "start_server.py", "--config", "config.yaml"]
```

```bash
# Build
docker build -t claude-code-server-api .

# Run
docker run -p 8000:8000 \
  -v /path/to/working/dir:/workspace \
  -e CLAUDE_WORKING_DIR=/workspace \
  claude-code-server-api
```

## 📊 监控

### Prometheus Metrics (TODO)

计划添加：
- 请求计数
- 响应时间
- 错误率
- Active sessions

### Logging

日志自动输出到 stdout，包含：
- 请求详情
- Claude CLI 调用
- 错误堆栈

## 🔍 故障排除

### 1. Claude CLI not found

**错误**: `Claude CLI not found`

**解决**: 设置正确的 `claude_bin` 路径

```yaml
claude_bin: "/opt/homebrew/bin/claude"
```

### 2. Session not persisting

**问题**: 重启后 session 丢失

**解决**: 使用 Redis 存储

```yaml
session_store_type: "redis"
redis_url: "redis://localhost:6379"
```

### 3. Timeout errors

**问题**: 复杂任务超时

**解决**: 增加 timeout，或使用 async 模式

```yaml
default_timeout: 600  # 10 minutes
```

---

**🎉 现在你有一个完整的 Claude Code Web 服务了！**
