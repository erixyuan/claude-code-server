# Quick Start Guide

## 🎯 Problem Solved

Claude CLI requires UUID session IDs for `--resume`, which is complex to manage manually. **ClaudeAgent** handles this automatically!

## ✅ Solution: ClaudeAgent

### The Simple Way (Recommended)

```python
from claude_code_server import ClaudeAgent

# Create agent
agent = ClaudeAgent()

# Chat with automatic session management
response1 = agent.chat("My name is Alice", user_id="alice_123")
response2 = agent.chat("What's my name?", user_id="alice_123")

print(response2.content)  # "Your name is Alice"
```

**That's it!** No manual session ID management needed.

## 🔧 How It Works

1. **User provides**: `user_id` (any string you want)
2. **ClaudeAgent handles**:
   - Maps your `user_id` to Claude's UUID `session_id`
   - Saves conversation history
   - Automatically resumes conversations

## 📝 Testing

### Test 1: In a regular terminal (outside Claude Code)

```bash
cd /Users/eric/Project/viralt/claude-code-server
python3 test_agent.py
```

Expected output:
```
✓ Claude remembered! Found number: 42
```

### Test 2: Quick interactive test

```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()

# First message
r1 = agent.chat("Tell me a number", user_id="test")
print(r1.content)

# Second message - should remember context
r2 = agent.chat("What number did you just say?", user_id="test")
print(r2.content)

# Show history
history = agent.get_conversation_history("test")
for msg in history:
    print(f"{msg.role}: {msg.content[:50]}...")
```

## 🎨 Use Cases

### Chatbot (Feishu/Slack/Discord)

```python
from claude_code_server import ClaudeAgent

agent = ClaudeAgent()

def handle_message(user_id: str, message: str) -> str:
    """Handle incoming message from any chat platform."""
    response = agent.chat(message, user_id=user_id)
    return response.content

# Usage
reply = handle_message("alice_123", "Hello!")
```

### Web API

```python
from fastapi import FastAPI
from claude_code_server import ClaudeAgent

app = FastAPI()
agent = ClaudeAgent()

@app.post("/chat")
async def chat(user_id: str, message: str):
    response = agent.chat(message, user_id=user_id)
    return {"reply": response.content}
```

## 🔍 Advanced: Low-Level API

If you need more control, use `ClaudeCodeClient` directly:

```python
from claude_code_server import ClaudeCodeClient

client = ClaudeCodeClient()

# First call
response1 = client.chat("Hello")
claude_session_id = response1.metadata["claude_session_id"]

# Second call - manually pass Claude's UUID
response2 = client.chat(
    "Continue",
    claude_session_id=claude_session_id
)
```

## 🐛 Troubleshooting

### Issue: Command hangs/timeout

**Cause**: Running inside Claude Code itself

**Solution**: Run in a regular terminal, not within Claude Code

```bash
# ❌ Wrong - Inside Claude Code
$ claude
> python3 test.py  # This will hang!

# ✅ Correct - Regular terminal
$ python3 test.py  # This works!
```

### Issue: "Session ID must be UUID format"

**Cause**: Using low-level API with custom session IDs

**Solution**: Use `ClaudeAgent` instead, or manage UUID mapping yourself

```python
# ✅ Use ClaudeAgent - handles UUIDs automatically
agent = ClaudeAgent()
agent.chat("Hello", user_id="any_string_you_want")
```

## 📚 Next Steps

1. ✅ Test `ClaudeAgent` in a standalone terminal
2. ✅ Build your chatbot using the simple API
3. ✅ Deploy to production (see USAGE_GUIDE.md)

---

**🎉 You're ready to build with claude-code-server!**
