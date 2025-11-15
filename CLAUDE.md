# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code Server is a Python library that wraps the Claude Code CLI to provide a programmatic API for building chatbots, automation workflows, and AI agent systems. It enables multi-user session management and conversation context across multiple turns.

**Key constraint:** This library is designed to run **outside** Claude Code itself. Running it inside Claude Code will cause conflicts since it spawns Claude CLI processes.

## Development Commands

### Setup
```bash
# Install for development
pip install -e ".[dev]"

# Install with all features (server + Redis)
pip install -e ".[all]"

# Install server features only
pip install -e ".[server]"
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_code_server

# Run single test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::test_chat_basic

# Run basic integration test
python test_basic.py
```

### Code Quality
```bash
# Format code
black claude_code_server/ tests/

# Lint code
ruff check claude_code_server/ tests/

# Type checking
mypy claude_code_server/
```

### Server
```bash
# Start FastAPI server
python start_server.py

# Start with custom config
python start_server.py --config config.yaml

# Start on custom port
python start_server.py --port 8080

# Development mode (auto-reload)
python start_server.py --reload

# Access API docs
open http://localhost:8000/docs
```

## Architecture

### Core Components

1. **ClaudeCodeClient** (`claude_code_server/client.py`)
   - Low-level wrapper around Claude CLI subprocess calls
   - Handles command building, execution, and response parsing
   - Manages Claude's UUID session IDs via `--resume` flag
   - Validates Claude CLI installation on initialization

2. **SessionManager** (`claude_code_server/session.py`)
   - Tracks conversation history per user/session
   - Maps user session IDs to Claude's internal UUID session IDs
   - Supports pluggable storage backends (InMemory, Redis, File)
   - Protocol-based design allows custom storage implementations

3. **ClaudeAgent** (`claude_code_server/agent.py`)
   - High-level API combining ClaudeCodeClient + SessionManager
   - Automatically manages session lifecycle
   - Recommended for most use cases (chatbots, multi-user services)
   - Derives session_id from user_id if not provided

4. **FastAPI Server** (`claude_code_server_api/server.py`)
   - RESTful API wrapper around ClaudeAgent
   - Three response modes: sync, stream (SSE), async (background tasks)
   - Session storage via InMemory, File, or Redis
   - Optional API key authentication

### Session ID Architecture

**Critical distinction:** There are TWO types of session IDs:

- **User Session ID** (`session_id`): Your application's session identifier (e.g., "user_alice")
- **Claude Session ID** (`claude_session_id`): Claude CLI's internal UUID session ID

The library manages this mapping:
```
User Session "user_alice" → Claude UUID "550e8400-e29b-41d4-a716-446655440000"
```

When making multi-turn conversations:
1. User sends first message → library creates user session
2. Claude CLI returns UUID in response metadata
3. Library stores UUID in session data
4. Next message passes UUID via `--resume` flag to Claude CLI

### Storage Backends

**InMemorySessionStore**: Dictionary-based, ephemeral (for development)
**FileSessionStore**: JSON file persistence (for single-instance production)
**RedisSessionStore**: Distributed storage with TTL (for multi-instance production)

All implement the `SessionStore` protocol:
- `get(session_id) -> Optional[SessionData]`
- `save(session: SessionData) -> None`
- `delete(session_id) -> None`
- `exists(session_id) -> bool`

## Configuration System

### ClaudeConfig (claude_code_server/types.py:46)

Controls Claude CLI behavior:
- `output_format`: text/json/streaming-json (use JSON for parsing)
- `permission_mode`: default/acceptEdits/bypassPermissions/plan
- `allowed_tools`: List of tool names to restrict (e.g., ["Read", "Grep"])
- `timeout`: Subprocess timeout in seconds (default: 300)
- `working_directory`: CWD for Claude CLI execution
- `append_system_prompt`: Additional system instructions
- `model`: Model selection (sonnet/opus/haiku)
- `disable_prompt_caching`: Set to True to avoid cache_control limit errors

### ServerConfig (claude_code_server_api/config.py)

YAML-based server configuration:
- `working_directory`: Claude CLI working directory (must be set correctly)
- `session_store_type`: memory/file/redis
- `default_response_mode`: sync/stream/async
- `api_key`: Optional authentication token
- `allowed_users`: Optional whitelist of user_ids

## Working with Sessions

### Using ClaudeAgent (Recommended)
```python
agent = ClaudeAgent()

# First turn - creates session automatically
response = agent.chat("Hello", user_id="alice")
# Library extracts claude_session_id from response.metadata

# Second turn - automatically uses stored claude_session_id
response = agent.chat("What did I say?", user_id="alice")
# Library passes claude_session_id to client.chat()

# Get history
history = agent.get_conversation_history("alice")

# Clear session
agent.clear_session("alice")
```

### Using ClaudeCodeClient (Advanced)
```python
client = ClaudeCodeClient()

# First turn
response = client.chat("Hello")
claude_session_id = response.metadata["claude_session_id"]

# Second turn - manually pass UUID
response = client.chat("Continue", claude_session_id=claude_session_id)
```

## Error Handling

Custom exceptions in `claude_code_server/exceptions.py`:
- `ClaudeCodeError`: Base exception
- `ClaudeExecutionError`: CLI subprocess failed (includes return_code, stderr)
- `SessionNotFoundError`: Session doesn't exist
- `InvalidConfigError`: Configuration validation failed
- `TimeoutError`: Subprocess timeout exceeded

## Testing Considerations

**NEVER run tests inside Claude Code** - they spawn Claude CLI processes which will conflict.

Test files (`test_*.py` in root) are for manual integration testing:
- `test_basic.py`: Simple client test
- `test_agent.py`: Agent test
- `test_api.py`: FastAPI server test

Unit tests in `tests/` directory use mocking to avoid spawning processes.

## Claude CLI Integration Details

The library interacts with Claude CLI via subprocess:
1. Build command: `["claude", "-p", message, "--output-format", "json", "--resume", uuid]`
2. Execute with timeout and custom CWD
3. Parse stdout based on output_format
4. Extract session_id from JSON response if present
5. Return ClaudeResponse with content and metadata

**Key flags:**
- `-p MESSAGE`: Non-interactive prompt mode
- `--output-format json`: Structured output for parsing
- `--resume SESSION_ID`: Continue previous conversation
- `--permission-mode acceptEdits`: Auto-accept file edits
- `--allowedTools TOOL1,TOOL2`: Restrict available tools
- `--working-directory PATH`: Set CWD (via subprocess.run cwd param)

## FastAPI Server Architecture

Three response modes for different use cases:

**Sync (`/chat`)**: Block until complete, return full response
- Use for: Simple chatbots, synchronous calls
- Returns: ChatResponse immediately

**Stream (`/chat/stream`)**: SSE streaming
- Use for: Real-time UI feedback, progressive responses
- Returns: EventSourceResponse with message/done events

**Async (`/chat/async`)**: Background task queue
- Use for: Long-running operations, webhook callbacks
- Returns: task_id immediately, poll `/task/{task_id}` for status

Task lifecycle:
1. Submit → TaskManager creates BackgroundTask
2. Processing → Executor runs agent.chat() in thread pool
3. Completed/Failed → Result stored in TaskManager._tasks dict
4. Cleanup → Old tasks purged every 5 minutes

## Common Pitfalls

1. **Running inside Claude Code**: Check `CLAUDECODE=1` or `CLAUDE_CODE_ENTRYPOINT` env vars
2. **Wrong working_directory**: Claude CLI runs in specified CWD, affects file access
3. **Missing claude_session_id**: Multi-turn fails without passing UUID between calls
4. **Timeout on complex tasks**: Increase `timeout` or use async mode
5. **Session storage**: InMemory loses data on restart, use Redis for production
6. **JSON parsing**: Use `output_format=json` for reliable content extraction

## Package Structure

```
claude_code_server/          # Core library
  ├── client.py              # ClaudeCodeClient (subprocess wrapper)
  ├── session.py             # SessionManager + storage backends
  ├── agent.py               # ClaudeAgent (high-level API)
  ├── types.py               # Pydantic models and enums
  ├── exceptions.py          # Custom exceptions
  └── simple_agent.py        # SimpleAgent (alternative implementation)

claude_code_server_api/      # FastAPI server
  ├── server.py              # FastAPI app and endpoints
  ├── models.py              # API request/response models
  ├── config.py              # ServerConfig and YAML loading
  └── tasks.py               # TaskManager for async operations

tests/                       # Unit tests (mocked)
examples/                    # Example scripts
test_*.py                    # Integration tests (root level)
```

## Environment Variables

- `CLAUDECODE=1`: Indicates running inside Claude Code (library warns)
- `CLAUDE_CODE_ENTRYPOINT`: Alternative indicator for Claude Code
- `DISABLE_PROMPT_CACHING=1`: Disables prompt caching (set by library if config.disable_prompt_caching=True)

Custom env vars can be passed via `ClaudeConfig(env={"KEY": "value"})`.
