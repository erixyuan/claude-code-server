# Claude Code Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Python library to interact with Claude Code CLI programmatically. Turn Claude Code into a powerful backend service for chatbots, automation workflows, and AI agent systems.

## 🎯 What is This?

Claude Code is an amazing CLI tool, but it's designed for interactive terminal use. **Claude Code Server** wraps the Claude CLI in a clean Python API, enabling you to:

- ✅ Build chatbots powered by Claude Code (Slack, Discord, Feishu/Lark, WeChat, etc.)
- ✅ Create multi-user AI agent services with session management
- ✅ Automate code reviews, analysis, and generation workflows
- ✅ Leverage Claude Code's sub-agents and MCP tools programmatically
- ✅ Maintain conversation context across multiple turns

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Claude Code CLI](https://code.claude.com) installed and authenticated

### ⚠️ Important: Run Outside Claude Code

**This library is designed to be used in standalone Python applications**, not inside Claude Code itself. Running it within Claude Code will cause conflicts.

**Correct usage:**
```bash
# In a regular terminal (not Claude Code)
python3 your_chatbot.py
```

**Incorrect usage:**
```bash
# ❌ Don't do this - running inside Claude Code
claude    # This starts Claude Code
# Then trying to use claude-code-server here will hang
```

### Installation

```bash
# Install from source (PyPI package coming soon)
git clone https://github.com/viralt/claude-code-server.git
cd claude-code-server
pip install -e .
```

### Basic Usage (Simple API)

```python
from claude_code_server import ClaudeAgent

# Create agent (automatically handles sessions)
agent = ClaudeAgent()

# Send messages - session managed automatically by user_id
response1 = agent.chat("My name is Alice", user_id="alice_123")
response2 = agent.chat("What's my name?", user_id="alice_123")

print(response2.content)  # "Your name is Alice"
```

### Advanced Usage (Low-level API)

```python
from claude_code_server import ClaudeCodeClient, ClaudeConfig

# Create client with custom config
client = ClaudeCodeClient(
    config=ClaudeConfig(output_format="json", timeout=60)
)

# Send a message (no session)
response = client.chat("Hello, Claude!")
print(response.content)

# Use Claude's UUID session for multi-turn
claude_session_id = response.metadata.get("claude_session_id")
response2 = client.chat(
    "Continue our conversation",
    claude_session_id=claude_session_id
)
```

## 📚 Core Concepts

### ClaudeAgent (Recommended)

**High-level API with automatic session management.** Perfect for chatbots and multi-user applications.

```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()

# Automatically handles sessions per user
response = agent.chat("Hello!", user_id="user_123")
response = agent.chat("Continue...", user_id="user_123")  # Remembers context

# Get conversation history
history = agent.get_conversation_history("user_123")

# Clear session
agent.clear_session("user_123")
```

**Key Features:**
- ✅ Automatic Claude UUID session ID management
- ✅ Per-user conversation tracking
- ✅ Built-in message history
- ✅ Simple API - just provide user_id

### ClaudeCodeClient (Low-level)

Direct access to Claude CLI for advanced use cases.

```python
from claude_code_server import ClaudeCodeClient, ClaudeConfig

client = ClaudeCodeClient(
    config=ClaudeConfig(
        output_format="json",
        timeout=120,
        allowed_tools=["Read", "Grep"],
    )
)

response = client.chat("Hello")
# Extract Claude's session ID for next call
claude_session_id = response.metadata["claude_session_id"]
response2 = client.chat("Continue", claude_session_id=claude_session_id)
```

### SessionManager

Manages conversation sessions for multiple users.

```python
from claude_code_server import SessionManager, InMemorySessionStore

# In-memory storage (for development)
manager = SessionManager(store=InMemorySessionStore())

# Create session
session = manager.create_session("session_id", user_id="user_123")

# Add messages
manager.add_message("session_id", "user", "Hello")
manager.add_message("session_id", "assistant", "Hi there!")

# Get history
history = manager.get_conversation_history("session_id")
```

**Storage Backends:**
- `InMemorySessionStore` - For development/testing
- `RedisSessionStore` - For production (requires redis)

### Configuration Options

```python
from claude_code_server import ClaudeConfig, OutputFormat, PermissionMode

config = ClaudeConfig(
    output_format=OutputFormat.JSON,              # text, json, streaming-json
    permission_mode=PermissionMode.ACCEPT_EDITS,  # default, acceptEdits, bypassPermissions, plan
    allowed_tools=["Read", "Write", "Bash"],      # Limit tools Claude can use
    timeout=300,                                  # Timeout in seconds
    working_directory="/path/to/project",          # Working directory for Claude
    append_system_prompt="Custom instructions",    # Additional system prompt
    model="sonnet",                               # Model selection
)
```

## 🎯 Use Cases

### 1. Feishu/Lark Chatbot (Recommended: ClaudeAgent)

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

    # Simple! Session managed automatically
    response = agent.chat(message, user_id=user_id)

    # Send back to Feishu
    return {"text": response.content}
```

### 2. Automated Code Review

```python
def review_code(file_path: str) -> str:
    client = ClaudeCodeClient(
        config=ClaudeConfig(
            allowed_tools=["Read", "Grep"],
            permission_mode=PermissionMode.ACCEPT_EDITS,
        )
    )

    prompt = f"Review the code in {file_path} for best practices, bugs, and improvements."
    response = client.chat(prompt)
    return response.content
```

### 3. Multi-User AI Service (Using ClaudeAgent)

```python
from claude_code_server import ClaudeAgent

class AIService:
    def __init__(self):
        self.agent = ClaudeAgent()

    def handle_user_message(self, user_id: str, message: str) -> str:
        response = self.agent.chat(message, user_id=user_id)
        return response.content

# Usage - Session automatically managed per user!
service = AIService()
response = service.handle_user_message("alice", "Help me with Python")
```

## 📖 Examples

Check out the [`examples/`](./examples) directory for complete working examples:

- **simple_chat.py** - Basic chat interaction
- **multi_turn_chat.py** - Conversation with memory
- **webhook_bot.py** - Chatbot pattern for webhooks

Run examples:

```bash
python examples/simple_chat.py
python examples/multi_turn_chat.py
python examples/webhook_bot.py
```

## 🏗️ Architecture

```
┌─────────────────────┐
│  Your Application   │
│  (Chatbot/Service)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Claude Code Server  │
│  - ClaudeCodeClient │
│  - SessionManager   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Claude CLI        │
│  (Headless Mode)    │
│  - Sub-agents       │
│  - MCP Tools        │
└─────────────────────┘
```

## 🔧 Development

### Setup

```bash
# Clone the repository
git clone https://github.com/viralt/claude-code-server.git
cd claude-code-server

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_code_server

# Run basic test script
python test_basic.py
```

## ⚙️ Configuration

### Session Storage

**In-Memory (Development):**
```python
from claude_code_server import SessionManager, InMemorySessionStore

manager = SessionManager(store=InMemorySessionStore())
```

**Redis (Production):**
```python
import redis
from claude_code_server import SessionManager, RedisSessionStore

redis_client = redis.Redis(host='localhost', port=6379, db=0)
manager = SessionManager(
    store=RedisSessionStore(redis_client, ttl=3600)
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of [Claude Code](https://code.claude.com) by Anthropic
- Inspired by the need to make Claude Code accessible in server environments

## 📞 Support

- 🐛 [Report Issues](https://github.com/viralt/claude-code-server/issues)
- 💬 [Discussions](https://github.com/viralt/claude-code-server/discussions)
- 📧 Email: your-email@example.com

## 🌐 FastAPI Server (NEW!)

**Turn Claude Code into a web service!**

```bash
# Install with server support
pip install -e ".[server]"

# Create config
cp config.yaml.example config.yaml

# Start server
python start_server.py

# Access API at http://localhost:8000/docs
```

**Features:**
- ✅ **3 Response Modes**: Sync, Stream (SSE), Async
- ✅ **Configurable**: YAML configuration, working directory, etc.
- ✅ **Session Management**: InMemory or Redis storage
- ✅ **API Authentication**: Optional API key protection
- ✅ **Background Tasks**: Async task queue for long operations

**See [API_GUIDE.md](API_GUIDE.md) for complete documentation.**

## 🗺️ Roadmap

- [x] PyPI package release structure
- [x] FastAPI server wrapper ✨
- [x] Session management (InMemory + Redis)
- [ ] WebSocket streaming support
- [ ] More session storage backends (PostgreSQL, SQLite)
- [ ] Prometheus metrics
- [ ] Docker container support

---

Made with ❤️ by the Viralt team
