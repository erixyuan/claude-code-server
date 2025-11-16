# 消息防抖功能 - 快速开始

## 什么是消息防抖？

当用户分多次发送消息时（例如先发"你好"，再发"你是谁"），防抖功能会自动将这些消息合并成一条，避免多次调用 AI。

**示例：**
```
用户操作：
  T+0.0s: 发送 "你好"
  T+0.5s: 发送 "你是谁"

无防抖：
  → 两次 AI 调用（浪费资源）

有防抖：
  → 等待 2 秒后，一次 AI 调用：
     "你好\n你是谁"
```

## 快速启用

### 1. 配置文件（推荐）

创建或修改 `config.yaml`：

```yaml
# 启用消息防抖
enable_message_debouncing: true  # 默认: true
debounce_window: 2.0             # 等待窗口（秒）
message_separator: "\n"          # 消息分隔符
```

### 2. 启动服务器

```bash
claude-code-server --config config.yaml
```

就这么简单！防抖已经生效了。

## 客户端使用

### Python 示例

```python
import httpx

# 发送消息（自动使用服务端配置）
response = httpx.post(
    "http://localhost:8000/chat/async",
    json={
        "message": "你好",
        "user_id": "user123"
    }
)
```

### 自定义防抖窗口

```python
# 使用 3 秒窗口
response = httpx.post(
    "http://localhost:8000/chat/async",
    json={
        "message": "你好",
        "user_id": "user123",
        "enable_debounce": True,
        "debounce_window": 3.0  # 覆盖服务端默认值
    }
)
```

### 禁用防抖（立即处理）

```python
# 对于重要消息，立即处理不等待
response = httpx.post(
    "http://localhost:8000/chat/async",
    json={
        "message": "紧急问题",
        "user_id": "user123",
        "enable_debounce": False  # 禁用防抖
    }
)
```

## API 响应说明

### 消息正在缓冲

```json
{
  "task_id": "pending",
  "status": "buffering",
  "message": "Message buffered (2 pending, will process in 2.0s)"
}
```

这表示消息已添加到缓冲区，正在等待更多消息。

### 消息开始处理

当防抖窗口到期后，服务器会自动创建任务处理合并后的消息。
你可以通过日志看到任务创建的信息。

## 测试

运行测试脚本验证功能：

```bash
# 确保服务器正在运行
claude-code-server --config config.yaml

# 运行单元测试
python test_message_buffer_unit.py

# 运行集成测试
python test_debounce.py
```

## 常见场景配置

### 聊天应用（快速打字）

```yaml
enable_message_debouncing: true
debounce_window: 2.0  # 2秒足够捕获快速输入
```

### 语音输入

```yaml
enable_message_debouncing: true
debounce_window: 3.0  # 等待语音识别完成
```

### 代码编辑器

```yaml
enable_message_debouncing: true
debounce_window: 1.5  # 较短窗口，快速反馈
```

## 监控

查看防抖日志：

```bash
# 启用 DEBUG 日志
# config.yaml
logging:
  level: "DEBUG"
```

日志示例：
```
📝 Message buffered for session user_user123: '你好...' (total: 1 messages)
📝 Message buffered for session user_user123: '你是谁...' (total: 2 messages)
🔄 Flushing 2 message(s) for session user_user123
   Combined message: '你好\n你是谁'
🚀 Created task abc123... with combined message
```

## 完整文档

详细说明请参考：[DEBOUNCE_GUIDE.md](./DEBOUNCE_GUIDE.md)

## 总结

防抖功能让你的 API 更智能：
- ✅ 自动合并用户的连续消息
- ✅ 减少 API 调用次数
- ✅ 节省 Token 消耗
- ✅ 提供更完整的上下文

只需在配置文件中设置 `enable_message_debouncing: true`，一切就绪！
