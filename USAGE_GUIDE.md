# Usage Guide - claude-code-server

## 核心理念

`claude-code-server` 是一个 Python 库，让你能够在**独立的 Python 应用**中程序化地使用 Claude Code CLI 的强大功能。

## ⚠️ 重要限制

### 不能在 Claude Code 内部使用

**claude-code-server 不能在 Claude Code 内部运行！** 这会导致递归调用和死锁。

**为什么？**
- Claude Code 本身是一个运行中的进程
- 当你尝试从 Claude Code 内部调用 `claude` CLI 时，会产生冲突
- 环境变量 `CLAUDECODE=1` 表明你正在 Claude Code 内部

**检测方法：**
```python
import os

if os.environ.get("CLAUDECODE") == "1":
    print("⚠️ Running inside Claude Code - this won't work!")
```

## ✅ 正确的使用场景

### 1. 飞书/Lark 聊天机器人

```python
# feishu_bot.py - 在独立终端运行
from fastapi import FastAPI
from claude_code_server import ClaudeCodeClient, SessionManager

app = FastAPI()
client = ClaudeCodeClient()
session_manager = SessionManager()

@app.post("/webhook")
async def handle_message(request: Request):
    # 处理飞书消息
    # 调用 Claude Code
    # 返回回复
    pass

# 运行方式：
# $ python3 feishu_bot.py
```

### 2. Slack 机器人

```python
# slack_bot.py
from slack_bolt import App
from claude_code_server import ClaudeCodeClient

app = App(token=os.environ["SLACK_BOT_TOKEN"])
client = ClaudeCodeClient()

@app.message(".*")
def handle_message(message, say):
    response = client.chat(message["text"], session_id=message["user"])
    say(response.content)

# $ python3 slack_bot.py
```

### 3. Discord Bot

```python
# discord_bot.py
import discord
from claude_code_server import ClaudeCodeClient

client = ClaudeCodeClient()
bot = discord.Client()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    response = client.chat(message.content, session_id=str(message.author.id))
    await message.channel.send(response.content)

# $ python3 discord_bot.py
```

### 4. Web API 服务

```python
# api_server.py
from fastapi import FastAPI
from claude_code_server import ClaudeCodeClient

app = FastAPI()
client = ClaudeCodeClient()

@app.post("/chat")
async def chat(request: ChatRequest):
    response = client.chat(
        request.message,
        session_id=request.session_id
    )
    return {"response": response.content}

# $ uvicorn api_server:app --port 8000
```

### 5. 自动化脚本

```python
# code_reviewer.py
from claude_code_server import ClaudeCodeClient

def review_pr(pr_number):
    client = ClaudeCodeClient()
    response = client.chat(f"Review PR #{pr_number}")
    return response.content

# $ python3 code_reviewer.py
```

## 🔧 开发和测试

### 测试你的应用

1. **在 Claude Code 中开发代码** ✅
   ```bash
   # 在 Claude Code 中编写你的 chatbot 代码
   claude
   # Write your code here
   ```

2. **在独立终端测试** ✅
   ```bash
   # 新开一个普通终端窗口
   cd your-project
   python3 your_bot.py
   ```

### 示例工作流

```bash
# Terminal 1: Claude Code - 开发
$ claude
> 帮我写一个飞书机器人...

# Terminal 2: 普通终端 - 测试
$ cd feishu-bot
$ python3 bot.py
Starting bot...
```

## 📋 检查清单

在部署前确认：

- [ ] 你的应用在**独立的 Python 环境**中运行
- [ ] 不是在 Claude Code 内部运行
- [ ] Claude CLI 已安装并认证（`claude --version`）
- [ ] 环境变量正确配置
- [ ] Session 管理配置正确（InMemory/Redis）
- [ ] 错误处理已实现

## 🐛 常见问题

### Q: 命令一直 hang 住 / 超时

**A:** 你可能在 Claude Code 内部运行。检查：
```bash
echo $CLAUDECODE
# 如果输出 "1"，你在 Claude Code 内部
```

**解决方案：** 在新的终端窗口运行你的应用。

### Q: 如何调试？

**A:** 启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = ClaudeCodeClient()
# 现在会看到详细的命令执行信息
```

### Q: 生产环境部署？

**A:** 使用 systemd/supervisor/docker：

```dockerfile
# Dockerfile
FROM python:3.11
RUN pip install claude-code-server
# Install Claude CLI
COPY your_bot.py /app/
CMD ["python3", "/app/your_bot.py"]
```

## 💡 最佳实践

1. **Session 管理**
   - 开发：使用 `InMemorySessionStore`
   - 生产：使用 `RedisSessionStore`

2. **错误处理**
   ```python
   from claude_code_server import ClaudeCodeClient
   from claude_code_server.exceptions import ClaudeExecutionError, TimeoutError

   try:
       response = client.chat(message)
   except TimeoutError:
       # Handle timeout
   except ClaudeExecutionError as e:
       # Handle execution error
       print(e.stderr)
   ```

3. **超时配置**
   ```python
   config = ClaudeConfig(
       timeout=120,  # 复杂任务需要更长时间
   )
   ```

4. **工具限制**
   ```python
   config = ClaudeConfig(
       allowed_tools=["Read", "Grep"],  # 限制可用工具
   )
   ```

## 📚 更多资源

- [README.md](README.md) - 完整文档
- [examples/](examples/) - 示例代码
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南

---

**记住：claude-code-server 是用来构建服务的工具，不是在 Claude Code 内部使用的工具。** 🎯
