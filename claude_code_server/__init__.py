"""
Claude Code Server - A Python library to interact with Claude using the official Agent SDK.
"""

from .client import ClaudeClient
from .agent import ClaudeAgent
from .session import SessionManager, InMemorySessionStore
from .file_session_store import FileSessionStore
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

__version__ = "0.2.0"
__all__ = [
    # Core clients
    "ClaudeClient",
    "ClaudeAgent",
    # Session management
    "SessionManager",
    "InMemorySessionStore",
    "FileSessionStore",
    # Simple agent
    "SimpleAgent",
    # Types
    "ClaudeResponse",
    "ClaudeMessage",
    "OutputFormat",
    "PermissionMode",
    "ClaudeConfig",
    # Exceptions
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
