# 消息防抖功能使用指南

## 概述

消息防抖（Message Debouncing）功能可以自动合并用户在短时间内发送的多条消息，避免重复调用 AI，提高效率并改善用户体验。

### 使用场景

- 用户有分多次发送消息的习惯（例如先发"你好"，再发"你是谁"）
- 移动端用户快速连续发送多条短消息
- 需要等待用户完整表达后再处理的场景

## 工作原理

```
时间轴示例（debounce_window = 2.0秒）：

T+0.0s: 用户发送 "你好"
        ↓ 启动 2秒 计时器

T+0.5s: 用户发送 "你是谁"
        ↓ 取消旧计时器，重新启动 2秒 计时器

T+2.5s: 计时器到期
        ↓ 合并消息："你好\n你是谁"
        ↓ 创建任务发送给 Claude
```

## 配置

### 服务端配置

在 `config.yaml` 中添加以下配置：

```yaml
# 消息防抖设置
enable_message_debouncing: true    # 启用防抖（默认: true）
debounce_window: 2.0               # 等待窗口（秒）（默认: 2.0）
max_debounce_window: 10.0          # 最大窗口限制（默认: 10.0）
message_separator: "\n"            # 消息分隔符（默认: "\n"）
```

**参数说明：**

- `enable_message_debouncing`: 全局开关，是否启用防抖
- `debounce_window`: 等待新消息的时间窗口（秒）
  - 推荐值：2-3秒（适合大多数场景）
  - 过小：可能无法合并用户的连续消息
  - 过大：增加响应延迟
- `max_debounce_window`: 安全限制，防止客户端设置过长的等待时间
- `message_separator`: 合并消息时的分隔符
  - `"\n"`: 换行（默认）
  - `" "`: 空格
  - `"\n\n"`: 双换行

### 客户端配置

客户端可以在每个请求中覆盖服务端的默认配置：

```python
import httpx

# 启用防抖（使用服务端默认窗口）
payload = {
    "message": "Hello",
    "user_id": "user123",
    "enable_debounce": True
}

# 自定义防抖窗口
payload = {
    "message": "Hello",
    "user_id": "user123",
    "enable_debounce": True,
    "debounce_window": 3.0  # 3秒窗口
}

# 禁用防抖（立即处理）
payload = {
    "message": "Hello",
    "user_id": "user123",
    "enable_debounce": False
}

response = httpx.post("http://localhost:8000/chat/async", json=payload)
```

## API 响应

### 防抖模式下的响应

当消息被缓冲时，API 会返回特殊的响应：

```json
{
  "task_id": "pending",
  "status": "buffering",
  "message": "Message buffered (2 pending, will process in 2.0s)"
}
```

**字段说明：**
- `task_id`: `"pending"` 表示消息正在缓冲中
- `status`: `"buffering"` 表示等待更多消息
- `message`: 当前缓冲的消息数量和剩余等待时间

### 正常处理响应

当防抖禁用或计时器到期后，返回正常的任务响应：

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Task submitted successfully"
}
```

## 使用示例

### 示例 1: Python 客户端

```python
import asyncio
import httpx

async def send_messages():
    async with httpx.AsyncClient() as client:
        # 快速发送3条消息
        messages = ["你好", "我想问一下", "如何使用这个功能？"]

        for msg in messages:
            response = await client.post(
                "http://localhost:8000/chat/async",
                json={
                    "message": msg,
                    "user_id": "user123",
                    "enable_debounce": True,
                    "debounce_window": 2.0
                }
            )
            print(response.json())
            await asyncio.sleep(0.5)  # 0.5秒间隔

        # 等待消息处理
        await asyncio.sleep(3)
        print("消息已合并处理!")

asyncio.run(send_messages())
```

**输出：**
```
{'task_id': 'pending', 'status': 'buffering', 'message': 'Message buffered (1 pending, will process in 2.0s)'}
{'task_id': 'pending', 'status': 'buffering', 'message': 'Message buffered (2 pending, will process in 2.0s)'}
{'task_id': 'pending', 'status': 'buffering', 'message': 'Message buffered (3 pending, will process in 2.0s)'}
消息已合并处理!
```

**服务端日志：**
```
📝 Message buffered for session user_user123: '你好' (total: 1 messages)
📝 Message buffered for session user_user123: '我想问一下' (total: 2 messages)
📝 Message buffered for session user_user123: '如何使用这个功能？' (total: 3 messages)
🔄 Flushing 3 message(s) for session user_user123
   Combined message: '你好\n我想问一下\n如何使用这个功能？'
🚀 Created task abc123... with combined message
```

### 示例 2: JavaScript/TypeScript 客户端

```typescript
async function sendMessage(message: string) {
  const response = await fetch('http://localhost:8000/chat/async', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      user_id: 'user123',
      enable_debounce: true,
      debounce_window: 2.0
    })
  });
  return response.json();
}

// 用户快速连发
await sendMessage("Hello");
await new Promise(r => setTimeout(r, 300));
await sendMessage("How are you?");
// 这两条消息会被合并
```

### 示例 3: cURL

```bash
# 第一条消息
curl -X POST http://localhost:8000/chat/async \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "user_id": "user123",
    "enable_debounce": true,
    "debounce_window": 3.0
  }'

# 0.5秒后发送第二条
sleep 0.5

curl -X POST http://localhost:8000/chat/async \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How are you?",
    "user_id": "user123",
    "enable_debounce": true,
    "debounce_window": 3.0
  }'
```

## 测试

使用提供的测试脚本验证防抖功能：

```bash
# 确保服务器正在运行
claude-code-server --config config.debounce.yaml

# 在另一个终端运行测试
python test_debounce.py
```

测试脚本会运行以下测试用例：

1. **快速连发测试**: 验证多条快速消息被合并
2. **延迟消息测试**: 验证延迟超过窗口的消息不被合并
3. **禁用防抖测试**: 验证显式禁用防抖时立即处理
4. **计时器重置测试**: 验证新消息到达时计时器重置

## 最佳实践

### 1. 选择合适的窗口时长

```yaml
# 聊天场景（用户打字速度较快）
debounce_window: 2.0

# 语音输入场景（需要等待语音识别完成）
debounce_window: 3.0

# 代码编辑场景（用户可能分多次编辑）
debounce_window: 1.5
```

### 2. 客户端优化

**方案A: 智能检测**
```python
def should_enable_debounce(message: str) -> bool:
    """判断是否应该启用防抖"""
    # 短消息可能是分段发送
    if len(message) < 20:
        return True

    # 没有句号的消息可能不完整
    if not message.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
        return True

    # 默认不启用
    return False
```

**方案B: 用户控制**
```python
# 提供UI开关让用户选择
enable_debounce = user_preferences.get("auto_combine_messages", True)
```

### 3. 监控和日志

启用 DEBUG 级别日志查看详细的防抖行为：

```yaml
logging:
  level: "DEBUG"  # 查看详细的缓冲和合并日志
```

## 故障排查

### 问题 1: 消息没有被合并

**原因：**
- 防抖被禁用
- 消息间隔超过 `debounce_window`
- 不同的 `session_id`

**解决：**
```python
# 检查配置
response = httpx.get("http://localhost:8000/health")
# 确保使用相同的 session_id
# 减小消息间隔或增加 debounce_window
```

### 问题 2: 响应延迟太长

**原因：**
- `debounce_window` 设置过大

**解决：**
```yaml
# 调小窗口
debounce_window: 1.5  # 从 3.0 减小到 1.5
```

### 问题 3: 消息被错误合并

**原因：**
- `debounce_window` 设置过大
- 用户确实想分开发送两条消息

**解决：**
```python
# 方案1: 调小窗口
debounce_window: 1.0

# 方案2: 让用户选择何时禁用防抖
enable_debounce = False  # 对于重要消息禁用
```

## 性能影响

### 优势

- ✅ 减少 API 调用次数（多条消息 -> 1次调用）
- ✅ 降低服务器负载
- ✅ 减少 Token 消耗（系统提示只发送一次）
- ✅ 提供更完整的上下文给 AI

### 权衡

- ⚠️ 增加首次响应延迟（等待 `debounce_window`）
- ⚠️ 增加内存占用（缓冲消息）

### 性能建议

```yaml
# 高并发场景
max_concurrent_tasks: 20        # 增加并发数
debounce_window: 1.5            # 减小延迟

# 低流量场景
max_concurrent_tasks: 5
debounce_window: 3.0            # 更积极合并
```

## 架构说明

### 组件

```
ChatRequest (models.py)
    ↓
MessageBuffer (message_buffer.py)
    ↓ (debounce timer)
TaskManager (tasks.py)
    ↓
ClaudeAgent
```

### 流程图

```
┌─────────────────┐
│  User sends     │
│  message 1      │
└────────┬────────┘
         ↓
┌─────────────────────────────┐
│ MessageBuffer.add_message() │
│ - Add to buffer             │
│ - Start 2s timer            │
└─────────────────────────────┘
         ↓
┌─────────────────┐
│  User sends     │
│  message 2      │  (within 2s)
└────────┬────────┘
         ↓
┌─────────────────────────────┐
│ MessageBuffer.add_message() │
│ - Cancel old timer          │
│ - Add to buffer             │
│ - Start new 2s timer        │
└─────────────────────────────┘
         ↓ (2s expires)
┌─────────────────────────────┐
│ MessageBuffer._flush()      │
│ - Combine: "msg1\nmsg2"     │
│ - Call callback()           │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│ TaskManager.create_task()   │
│ - Create background task    │
│ - Send to Claude            │
└─────────────────────────────┘
```

## 更新日志

### v1.0 (2024)
- ✨ 新增消息防抖功能
- ✨ 支持客户端自定义防抖窗口
- ✨ 支持动态启用/禁用防抖
- 📝 添加详细日志记录
- 🧪 添加测试脚本

## 许可证

与 Claude Code Server 主项目相同。
