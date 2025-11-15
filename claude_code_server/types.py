"""
Type definitions for Claude Code Server.
"""

from enum import Enum
from typing import Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Claude CLI output format options."""

    TEXT = "text"
    JSON = "json"
    STREAMING_JSON = "streaming-json"


class PermissionMode(str, Enum):
    """Claude CLI permission modes."""

    DEFAULT = "default"
    ACCEPT_EDITS = "acceptEdits"
    BYPASS_PERMISSIONS = "bypassPermissions"
    PLAN = "plan"


class ClaudeMessage(BaseModel):
    """A single message in Claude conversation."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ClaudeResponse(BaseModel):
    """Response from Claude CLI."""

    content: str
    raw_output: str
    success: bool
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaudeConfig(BaseModel):
    """Configuration for Claude Code client."""

    output_format: OutputFormat = OutputFormat.JSON
    permission_mode: PermissionMode = PermissionMode.ACCEPT_EDITS
    allowed_tools: Optional[list[str]] = None
    timeout: int = 300  # seconds
    max_retries: int = 3
    working_directory: Optional[str] = None
    append_system_prompt: Optional[str] = None
    model: Optional[str] = None
    env: Optional[dict[str, str]] = None  # Additional environment variables
    disable_prompt_caching: bool = True  # Disable caching to avoid cache_control limit
    debug_print_command: bool = True  # Print Claude CLI command to stdout
    debug_print_full_prompt: bool = False  # Print full system prompt (including CLAUDE.md)

    class Config:
        use_enum_values = True


class SessionData(BaseModel):
    """Session data structure."""

    session_id: str
    user_id: Optional[str] = None
    conversation_history: list[ClaudeMessage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    claude_session_id: Optional[str] = None  # Claude CLI's internal session ID
