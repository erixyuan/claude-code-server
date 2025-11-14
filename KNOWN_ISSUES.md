# Known Issues

## Claude API Cache Control Limit

### Issue
When resuming sessions with `--resume`, you may encounter:
```
API Error: 400 - A maximum of 4 blocks with cache_control may be provided. Found 5.
```

### Root Cause
Claude Code uses prompt caching internally. When resuming a session multiple times in quick succession, the number of cached blocks can exceed the API limit (4 blocks).

### Workaround
ClaudeAgent automatically handles this error:
- Detects the cache_control error
- Falls back to starting a new session
- Continues without interruption

However, **context from previous messages will be lost** when this fallback occurs.

### Alternative Solution
If you need to maintain context across many turns:

**Option 1: Manual History Management**
```python
from claude_code_server import ClaudeCodeClient

client = ClaudeCodeClient()

# Don't use --resume, instead include history in prompt
conversation_history = []

# First message
msg1 = "My name is Alice"
conversation_history.append(f"User: {msg1}")
response1 = client.chat(msg1)
conversation_history.append(f"Assistant: {response1.content}")

# Second message - include history in the prompt
msg2 = "What's my name?"
full_prompt = "\n".join(conversation_history) + f"\nUser: {msg2}"
response2 = client.chat(full_prompt)
```

**Option 2: Use Claude API Directly**
For production applications with many conversation turns, consider using the Claude API directly (via `anthropic` Python SDK) instead of Claude Code CLI.

### Status
This is a limitation of Claude Code's current session resume implementation. We've added automatic fallback handling in ClaudeAgent to prevent crashes.

---

## Running Inside Claude Code

### Issue
Running claude-code-server scripts inside Claude Code itself causes hangs and conflicts.

### Solution
**Always run your application in a standalone terminal**, not within Claude Code.

```bash
# ✅ Correct
$ python3 your_bot.py

# ❌ Wrong
$ claude  # Starts Claude Code
> python3 your_bot.py  # This will hang!
```

### Detection
The library automatically detects if running inside Claude Code and shows a warning.
