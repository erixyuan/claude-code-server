"""
Claude Agent SDK client implementation.

This module provides a client using the official claude-agent-sdk.
"""

from typing import Optional
from pathlib import Path
import asyncio

from .types import ClaudeConfig, ClaudeResponse
from .exceptions import ClaudeExecutionError, TimeoutError, InvalidConfigError

# Try to import Claude Agent SDK
try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    # Define placeholder to avoid NameError
    query = None
    ClaudeAgentOptions = None


class ClaudeClient:
    """
    A Python client to interact with Claude using the official Agent SDK.

    Example:
        >>> client = ClaudeClient()
        >>> response = client.chat("Hello, Claude!")
        >>> print(response.content)
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
    ):
        """
        Initialize Claude client.

        Args:
            config: Configuration for Claude SDK behavior
        """
        if not SDK_AVAILABLE:
            raise ImportError(
                "claude-agent-sdk is not installed. Please install it with: "
                "pip install claude-agent-sdk"
            )
        self.config = config or ClaudeConfig()

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
            claude_session_id: Optional Claude session ID (from previous response)

        Returns:
            ClaudeResponse containing the response content and metadata

        Raises:
            ClaudeExecutionError: If Claude SDK execution fails
            TimeoutError: If execution times out
        """
        config = config_override or self.config
        
        # Print command for debugging (if enabled)
        if config.debug_print_command:
            print("\n" + "="*80)
            print("🚀 Executing Claude Agent SDK:")
            print("="*80)
            print(f"Message: {message[:100]}{'...' if len(message) > 100 else ''}")
            print(f"Session ID: {claude_session_id or 'None'}")
            print(f"Working Directory: {config.working_directory or 'Current'}")
            print("="*80 + "\n")

        try:
            # Build options for Claude Agent SDK
            options = self._build_options(config, claude_session_id)
            
            # Call Claude Agent SDK (it's async, so we need to run it)
            result = self._run_query_sync(message, options)
            
            return self._parse_response(result, config)

        except Exception as e:
            raise ClaudeExecutionError(
                message=f"Claude Agent SDK execution failed: {str(e)}",
                return_code=-1,
            )
    
    def _run_query_sync(self, message: str, options):
        """Run the async query function synchronously."""
        async def _run():
            messages = []
            async for msg in query(prompt=message, options=options):
                messages.append(msg)
            return messages
        
        # Run the async function and get results
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_run())

    def _build_options(
        self,
        config: ClaudeConfig,
        session_id: Optional[str],
    ) -> ClaudeAgentOptions:
        """Build the Claude Agent SDK options."""
        # Load system prompt
        system_prompt = self._load_system_prompt(config)
        
        # Create options
        options_dict = {}
        
        # Model
        if config.model:
            options_dict["model"] = config.model
        
        # Permission mode
        if config.permission_mode:
            options_dict["permission_mode"] = config.permission_mode
        
        # System prompt
        if system_prompt:
            options_dict["system_prompt"] = system_prompt
        
        # Working directory (SDK uses 'cwd' not 'working_directory')
        if config.working_directory:
            options_dict["cwd"] = config.working_directory
        
        # Allowed tools
        if config.allowed_tools:
            options_dict["allowed_tools"] = config.allowed_tools
        
        # Session ID for resuming (SDK uses 'resume' parameter)
        if session_id:
            options_dict["resume"] = session_id
        
        # Setting sources
        options_dict["setting_sources"] = ["user", "project", "local"]
        
        return ClaudeAgentOptions(**options_dict)

    def _load_system_prompt(self, config: ClaudeConfig) -> Optional[str]:
        """Load system prompt from CLAUDE.md and SYSTEM_PROMPT.md files."""
        system_prompt = config.append_system_prompt or ""

        # Try to load CLAUDE.md from working directory
        if config.working_directory:
            claude_md_paths = [
                Path(config.working_directory) / ".claude" / "CLAUDE.md",
                Path(config.working_directory) / "CLAUDE.md",
            ]

            for claude_md_path in claude_md_paths:
                if claude_md_path.exists():
                    try:
                        claude_md_content = claude_md_path.read_text(encoding='utf-8')
                        # Prepend CLAUDE.md content to system prompt
                        if system_prompt:
                            system_prompt = f"{claude_md_content}\n\n{system_prompt}"
                        else:
                            system_prompt = claude_md_content
                        break  # Use first found CLAUDE.md
                    except Exception:
                        pass  # Silently ignore read errors

            # Try to load SYSTEM_PROMPT.md from working directory
            system_prompt_path = Path(config.working_directory) / "SYSTEM_PROMPT.md"
            if system_prompt_path.exists():
                try:
                    system_prompt_content = system_prompt_path.read_text(encoding='utf-8')
                    # Append SYSTEM_PROMPT.md content to system prompt
                    if system_prompt:
                        system_prompt = f"{system_prompt}\n\n{system_prompt_content}"
                    else:
                        system_prompt = system_prompt_content
                except Exception:
                    pass  # Silently ignore read errors

        return system_prompt if system_prompt else None

    def _parse_response(
        self, messages: list, config: ClaudeConfig
    ) -> ClaudeResponse:
        """Parse Claude SDK output into ClaudeResponse."""
        try:
            # Extract content from all messages
            content_parts = []
            session_id = None
            result_text = None
            
            for msg in messages:
                # Get the class name to determine message type
                msg_type = type(msg).__name__
                
                # Extract session ID from SystemMessage or ResultMessage
                if hasattr(msg, 'session_id') and msg.session_id:
                    session_id = msg.session_id
                
                # Handle AssistantMessage - contains the actual response
                if msg_type == 'AssistantMessage':
                    if hasattr(msg, 'content') and msg.content:
                        for block in msg.content:
                            # TextBlock has a 'text' attribute
                            if hasattr(block, 'text'):
                                content_parts.append(block.text)
                            # Fallback to string conversion
                            elif isinstance(block, str):
                                content_parts.append(block)
                
                # Handle ResultMessage - contains the final result
                elif msg_type == 'ResultMessage':
                    if hasattr(msg, 'result') and msg.result:
                        result_text = msg.result
            
            # Use assistant message content first, fallback to result
            final_content = "".join(content_parts) if content_parts else (result_text or "")
            
            return ClaudeResponse(
                content=final_content,
                raw_output=str(messages),
                success=True,
                metadata={
                    "messages": [str(m) for m in messages],
                    "claude_session_id": session_id,
                },
            )
        except Exception as e:
            # Fallback: try to extract any text we can
            import traceback
            error_details = traceback.format_exc()
            print(f"Error parsing response: {error_details}")
            
            fallback_content = str(messages)
            return ClaudeResponse(
                content=fallback_content,
                raw_output=fallback_content,
                success=True,
                error=f"Failed to parse SDK response: {str(e)}",
            )

    def _extract_content_from_result(self, result: dict) -> str:
        """Extract text content from Claude SDK response."""
        # Handle different response structures
        if "content" in result:
            content = result["content"]
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
        if "result" in result:
            return result["result"]
        if "text" in result:
            return result["text"]
        if "message" in result:
            return result["message"]
        if "output" in result:
            return result["output"]

        # Last resort: return the whole result as string
        return str(result)

