# Session TTL 配置更新说明

## 📋 更新概述

将会话过期时间（session_ttl）的默认值从 **3600 秒（1小时）** 改为 **null（永不过期）**。

## 🎯 更新原因

对于聊天机器人和长期对话场景，用户希望会话能够持久保存，不自动过期。默认设置为永不过期更符合大多数使用场景。

## 📝 修改内容

### 1. 配置文件 (config.yaml)

**修改前：**
```yaml
session_ttl: 3600  # 1 hour
```

**修改后：**
```yaml
session_ttl: null  # Never expire (default)
```

**新的配置说明：**
- `null`: 会话永不过期（默认，推荐用于聊天机器人和长期对话）
- `数字`: 会话在指定秒数后自动过期（如 3600 = 1小时）

### 2. 代码修改

#### a. `claude_code_server/session.py`

**RedisSessionStore 构造函数：**
```python
# 修改前
def __init__(self, redis_client, prefix: str = "claude_session:", ttl: int = 3600):

# 修改后
def __init__(self, redis_client, prefix: str = "claude_session:", ttl: Optional[int] = None):
```

**RedisSessionStore.save() 方法：**
```python
# 修改前
def save(self, session: SessionData) -> None:
    session.last_activity = datetime.now()
    key = self._make_key(session.session_id)
    self.redis.setex(key, self.ttl, session.model_dump_json())

# 修改后
def save(self, session: SessionData) -> None:
    session.last_activity = datetime.now()
    key = self._make_key(session.session_id)
    data = session.model_dump_json()

    if self.ttl is None:
        # No expiration - session never expires
        self.redis.set(key, data)
    else:
        # Set expiration time
        self.redis.setex(key, self.ttl, data)
```

**关键变化：**
- 当 `ttl=None` 时，使用 `redis.set()` 而不是 `redis.setex()`
- 这样 Redis 中的 key 就不会设置过期时间（TTL = -1）

#### b. `claude_code_server_api/config.py`

```python
# 修改前
session_ttl: int = 3600

# 修改后
session_ttl: Optional[int] = None
```

## 🔍 使用示例

### 示例 1: 永不过期（默认）

**配置：**
```yaml
session_ttl: null
```

**Python 代码：**
```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()  # 使用默认配置
response = agent.chat("Hello", user_id="alice")
# 会话永远不会过期
```

**Redis 中的 TTL：**
```bash
redis> TTL claude_session:user_alice
(integer) -1  # -1 表示永不过期
```

### 示例 2: 1小时后过期

**配置：**
```yaml
session_ttl: 3600  # 3600 seconds = 1 hour
```

**Python 代码：**
```python
import redis
from claude_code_server import SessionManager, RedisSessionStore

redis_client = redis.Redis(host='localhost', port=6379)
store = RedisSessionStore(redis_client, ttl=3600)
manager = SessionManager(store=store)

session = manager.create_session("test", user_id="bob")
# 会话将在 1 小时后自动过期
```

**Redis 中的 TTL：**
```bash
redis> TTL claude_session:test
(integer) 3598  # 剩余秒数（约1小时）
```

### 示例 3: 自定义过期时间

```python
import redis
from claude_code_server import RedisSessionStore

redis_client = redis.Redis()

# 30分钟过期
store = RedisSessionStore(redis_client, ttl=1800)

# 24小时过期
store = RedisSessionStore(redis_client, ttl=86400)

# 永不过期
store = RedisSessionStore(redis_client, ttl=None)
```

## ⚙️ 不同存储后端的 TTL 行为

| 存储类型 | TTL 支持 | 行为 |
|---------|---------|------|
| **InMemorySessionStore** | ❌ 不支持 | 会话永久保存在内存中，进程重启后丢失 |
| **FileSessionStore** | ❌ 不支持 | 会话永久保存在文件中，除非手动删除 |
| **RedisSessionStore** | ✅ 支持 | • `ttl=None`: 永不过期<br>• `ttl=数字`: 自动过期 |

## 🧪 测试

运行测试脚本验证功能：

```bash
python test_session_ttl.py
```

**测试内容：**
1. InMemorySessionStore 基本功能
2. RedisSessionStore with ttl=None（永不过期）
3. RedisSessionStore with ttl=60（60秒后过期）

## 📊 迁移指南

### 从旧版本升级

如果你之前依赖默认的 1 小时过期时间，升级后需要显式设置：

**config.yaml：**
```yaml
# 保持原来的 1 小时过期行为
session_ttl: 3600
```

**或在代码中：**
```python
import redis
from claude_code_server import RedisSessionStore

redis_client = redis.Redis()
store = RedisSessionStore(redis_client, ttl=3600)  # 显式设置 1 小时
```

### 推荐配置

**聊天机器人 / 长期对话：**
```yaml
session_ttl: null  # 永不过期
```

**临时会话 / 安全敏感应用：**
```yaml
session_ttl: 1800  # 30分钟过期
```

**API 限流 / 短期缓存：**
```yaml
session_ttl: 300  # 5分钟过期
```

## 🎉 优势

1. **更好的默认值**：大多数场景需要持久会话，不应该默认过期
2. **向后兼容**：仍然支持设置 TTL，只是默认值改变
3. **灵活性**：可以在配置文件或代码中轻松切换
4. **清晰的语义**：`null` 明确表示"永不过期"

## ⚠️ 注意事项

1. **Redis 内存管理**：
   - `ttl=null` 时会话永久保存在 Redis 中
   - 需要手动调用 `delete_session()` 清理不需要的会话
   - 或设置 Redis 的 `maxmemory-policy` 策略

2. **生产环境建议**：
   - 监控 Redis 内存使用
   - 实现定期清理机制（清理长期不活跃的会话）
   - 或根据业务需求设置合理的 TTL

3. **文件存储**：
   - File/Memory 存储不支持自动过期
   - `.sessions/` 目录中的文件需要手动清理

## 📚 相关文件

- `config.yaml` - 配置文件更新
- `claude_code_server/session.py` - RedisSessionStore 实现
- `claude_code_server_api/config.py` - ServerConfig 定义
- `test_session_ttl.py` - 测试脚本

## 🔗 参考资料

- [Redis TTL 命令文档](https://redis.io/commands/ttl/)
- [Redis SET vs SETEX](https://redis.io/commands/set/)

---

**更新日期**: 2025-11-14
**版本**: 0.1.1+
