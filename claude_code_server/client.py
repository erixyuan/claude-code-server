"""
Core Claude Code client implementation.
"""

import json
import subprocess
import os
from typing import Optional
from pathlib import Path

from .types import ClaudeConfig, ClaudeResponse, OutputFormat, PermissionMode
from .exceptions import ClaudeExecutionError, TimeoutError, InvalidConfigError


class ClaudeCodeClient:
    """
    A Python client to interact with Claude Code CLI programmatically.

    Example:
        >>> client = ClaudeCodeClient()
        >>> response = client.chat("Hello, Claude!")
        >>> print(response.content)
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        claude_bin: str = "claude",
    ):
        """
        Initialize Claude Code client.

        Args:
            config: Configuration for Claude CLI behavior
            claude_bin: Path to claude CLI binary (default: "claude" from PATH)
        """
        self.config = config or ClaudeConfig()
        self.claude_bin = claude_bin
        self._validate_installation()

    def _validate_installation(self) -> None:
        """Validate that Claude CLI is installed and accessible."""
        # Check if we're running inside Claude Code
        if os.environ.get("CLAUDECODE") == "1" or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
            import warnings
            warnings.warn(
                "⚠️  You are running claude-code-server inside Claude Code itself. "
                "This may cause conflicts. claude-code-server is designed to be used "
                "in standalone Python applications (e.g., chatbots, web services). "
                "To use it, run your Python script outside of Claude Code.",
                RuntimeWarning,
                stacklevel=2
            )

        try:
            result = subprocess.run(
                [self.claude_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise InvalidConfigError(
                    f"Claude CLI not found or not executable: {self.claude_bin}"
                )
        except FileNotFoundError:
            raise InvalidConfigError(
                f"Claude CLI not found at: {self.claude_bin}. "
                "Please install Claude Code first."
            )
        except subprocess.TimeoutExpired:
            raise InvalidConfigError("Claude CLI version check timed out")

    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        config_override: Optional[ClaudeConfig] = None,
        claude_session_id: Optional[str] = None,
    ) -> ClaudeResponse:
        """
        Send a message to Claude and get response.

        Args:
            message: The message to send to Claude
            session_id: Optional user session ID (for reference only)
            config_override: Override default config for this request
            claude_session_id: Optional Claude CLI's UUID session ID (from previous response)

        Returns:
            ClaudeResponse containing the response content and metadata

        Raises:
            ClaudeExecutionError: If Claude CLI execution fails
            TimeoutError: If execution times out
        """
        config = config_override or self.config
        cmd = self._build_command(message, claude_session_id, config)

        try:
            # Prepare environment: inherit current env and add custom vars
            env = os.environ.copy()

            # Disable prompt caching to avoid cache_control block limit
            if config.disable_prompt_caching:
                env["DISABLE_PROMPT_CACHING"] = "1"

            if config.env:
                env.update(config.env)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.timeout,
                cwd=config.working_directory,
                env=env,  # Pass environment variables
            )

            if result.returncode != 0:
                error_msg = f"Claude CLI failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nStdout: {result.stdout}"
                raise ClaudeExecutionError(
                    message=error_msg,
                    return_code=result.returncode,
                    stderr=result.stderr,
                )

            return self._parse_response(result.stdout, result.stderr, config)

        except subprocess.TimeoutExpired:
            raise TimeoutError(
                f"Claude CLI execution timed out after {config.timeout} seconds"
            )
        except Exception as e:
            if isinstance(e, (ClaudeExecutionError, TimeoutError)):
                raise
            raise ClaudeExecutionError(
                message=f"Unexpected error executing Claude CLI: {str(e)}",
                return_code=-1,
            )

    def _build_command(
        self,
        message: str,
        session_id: Optional[str],
        config: ClaudeConfig,
    ) -> list[str]:
        """Build the Claude CLI command with all options."""
        cmd = [self.claude_bin]

        # Non-interactive mode
        cmd.extend(["-p", message])

        # Output format
        if config.output_format != OutputFormat.TEXT.value:
            cmd.extend(["--output-format", config.output_format])

        # Session management
        if session_id:
            cmd.extend(["--resume", session_id])

        # Permission mode
        if config.permission_mode != PermissionMode.DEFAULT.value:
            cmd.extend(["--permission-mode", config.permission_mode])

        # Allowed tools
        if config.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(config.allowed_tools)])

        # System prompt
        if config.append_system_prompt:
            cmd.extend(["--append-system-prompt", config.append_system_prompt])

        # Model selection
        if config.model:
            cmd.extend(["--model", config.model])

        return cmd

    def _parse_response(
        self, stdout: str, stderr: str, config: ClaudeConfig
    ) -> ClaudeResponse:
        """Parse Claude CLI output into ClaudeResponse."""
        if config.output_format == OutputFormat.JSON:
            try:
                data = json.loads(stdout)

                # Extract Claude's session_id if present
                claude_session_id = data.get("session_id")

                return ClaudeResponse(
                    content=self._extract_content_from_json(data),
                    raw_output=stdout,
                    success=True,
                    metadata={
                        **data,
                        "claude_session_id": claude_session_id,  # Save for future use
                    },
                )
            except json.JSONDecodeError as e:
                # Fallback to text if JSON parsing fails
                return ClaudeResponse(
                    content=stdout,
                    raw_output=stdout,
                    success=True,
                    error=f"Failed to parse JSON: {str(e)}",
                )
        elif config.output_format == OutputFormat.STREAMING_JSON:
            # For streaming JSON, concatenate all content
            lines = stdout.strip().split("\n")
            content_parts = []
            metadata_list = []

            for line in lines:
                try:
                    data = json.loads(line)
                    content_parts.append(self._extract_content_from_json(data))
                    metadata_list.append(data)
                except json.JSONDecodeError:
                    continue

            return ClaudeResponse(
                content="".join(content_parts),
                raw_output=stdout,
                success=True,
                metadata={"messages": metadata_list},
            )
        else:
            # Text format
            return ClaudeResponse(
                content=stdout,
                raw_output=stdout,
                success=True,
            )

    def _extract_content_from_json(self, data: dict) -> str:
        """Extract text content from Claude JSON response."""
        # Handle different JSON response structures
        if "content" in data:
            content = data["content"]
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                return "".join(text_parts)

        # Fallback: try to find any text field
        if "result" in data:  # Claude CLI uses "result" field
            return data["result"]
        if "text" in data:
            return data["text"]
        if "message" in data:
            return data["message"]

        # Last resort: return the whole data as string
        return str(data)

    def get_version(self) -> str:
        """Get Claude Code CLI version."""
        try:
            result = subprocess.run(
                [self.claude_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception as e:
            raise ClaudeExecutionError(
                message=f"Failed to get Claude version: {str(e)}",
                return_code=-1,
            )
