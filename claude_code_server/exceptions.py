"""
Custom exceptions for Claude Code Server.
"""


class ClaudeCodeError(Exception):
    """Base exception for all Claude Code Server errors."""

    pass


class ClaudeExecutionError(ClaudeCodeError):
    """Raised when Claude CLI execution fails."""

    def __init__(self, message: str, return_code: int, stderr: str = ""):
        super().__init__(message)
        self.return_code = return_code
        self.stderr = stderr


class SessionNotFoundError(ClaudeCodeError):
    """Raised when a session is not found."""

    pass


class InvalidConfigError(ClaudeCodeError):
    """Raised when configuration is invalid."""

    pass


class TimeoutError(ClaudeCodeError):
    """Raised when Claude CLI execution times out."""

    pass
