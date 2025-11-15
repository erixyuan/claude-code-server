"""
Claude Code Server - A Python library to interact with Claude Code CLI programmatically.
"""

from .client import ClaudeCodeClient
from .session import SessionManager, InMemorySessionStore
from .file_session_store import FileSessionStore
from .agent import ClaudeAgent
from .simple_agent import SimpleAgent
from .types import (
    ClaudeResponse,
    ClaudeMessage,
    OutputFormat,
    PermissionMode,
    ClaudeConfig,
)
from .exceptions import (
    ClaudeCodeError,
    ClaudeExecutionError,
    SessionNotFoundError,
    InvalidConfigError,
)
from .formatters import (
    simple_formatter,
    imessage_formatter,
    platform_formatter,
    detailed_formatter,
    create_custom_formatter,
    get_formatter,
)

__version__ = "0.1.1"
__all__ = [
    "ClaudeCodeClient",
    "SessionManager",
    "InMemorySessionStore",
    "FileSessionStore",
    "ClaudeAgent",
    "SimpleAgent",
    "ClaudeResponse",
    "ClaudeMessage",
    "OutputFormat",
    "PermissionMode",
    "ClaudeConfig",
    "ClaudeCodeError",
    "ClaudeExecutionError",
    "SessionNotFoundError",
    "InvalidConfigError",
    # Formatters
    "simple_formatter",
    "imessage_formatter",
    "platform_formatter",
    "detailed_formatter",
    "create_custom_formatter",
    "get_formatter",
]
