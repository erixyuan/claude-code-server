# Claude Code Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Python library to interact with Claude using the official Agent SDK. Turn Claude into a powerful backend service for chatbots, automation workflows, and AI agent systems.

English | [简体中文](README_zh.md)

## 🎯 What is This?

**Claude Code Server** uses the official Claude Agent SDK to provide a clean Python API, enabling you to:

- ✅ Build chatbots powered by Claude (Slack, Discord, Feishu/Lark, WeChat, etc.)
- ✅ Create multi-user AI agent services with session management
- ✅ Automate code reviews, analysis, and generation workflows
- ✅ Leverage Claude's capabilities programmatically
- ✅ Maintain conversation context across multiple turns

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Claude Agent SDK

### Installation

```bash
# Install from source
git clone https://github.com/viralt/claude-code-server.git
cd claude-code-server
pip install -e .
```

### Basic Usage

```python
from claude_code_server import ClaudeAgent

# Create agent (automatically handles sessions)
agent = ClaudeAgent()

# Send messages - session managed automatically by user_id
response1 = agent.chat("My name is Alice", user_id="alice_123")
response2 = agent.chat("What's my name?", user_id="alice_123")

print(response2.content)  # "Your name is Alice"
```

### Advanced Usage

```python
from claude_code_server import ClaudeClient, ClaudeConfig

# Create client with custom config
client = ClaudeClient(
    config=ClaudeConfig(output_format="json", timeout=60)
)

# Send a message
response = client.chat("Hello, Claude!")
print(response.content)
```

## 📚 Core Concepts

### ClaudeAgent (Recommended)⭐

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
- ✅ Uses official Claude Agent SDK
- ✅ Automatic Claude session ID management
- ✅ Per-user conversation tracking
- ✅ Built-in message history
- ✅ Simple API - just provide user_id

### ClaudeClient (Low-level)

Direct access to Claude SDK for advanced use cases.

```python
from claude_code_server import ClaudeClient, ClaudeConfig

client = ClaudeClient(
    config=ClaudeConfig(
        output_format="json",
        timeout=120,
        allowed_tools=["Read", "Grep"],
    )
)

response = client.chat("Hello")
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
    working_directory="/path/to/project",         # Working directory for Claude
    append_system_prompt="Custom instructions",   # Additional system prompt
    model="claude-sonnet-4-5",                    # Model selection
)
```

## 🎯 Use Cases

### 1. Feishu/Lark Chatbot

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
    client = ClaudeClient(
        config=ClaudeConfig(
            allowed_tools=["Read", "Grep"],
            permission_mode=PermissionMode.ACCEPT_EDITS,
        )
    )

    prompt = f"Review the code in {file_path} for best practices, bugs, and improvements."
    response = client.chat(prompt)
    return response.content
```

### 3. Multi-User AI Service

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
- **agent_example.py** - Complete ClaudeAgent example

Run examples:

```bash
python examples/simple_chat.py
python examples/agent_example.py
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
│  - ClaudeClient     │
│  - ClaudeAgent      │
│  - SessionManager   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Claude Agent SDK    │
│  (Official SDK)     │
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

# Run basic test script
python test_simple.py
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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of Anthropic's official Claude Agent SDK

## 📞 Support

- 🐛 [Report Issues](https://github.com/viralt/claude-code-server/issues)
- 💬 [Discussions](https://github.com/viralt/claude-code-server/discussions)

---

Made with ❤️ by the Viralt team
