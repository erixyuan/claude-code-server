#!/usr/bin/env python3
"""
Simple chat example - Basic usage of ClaudeCodeClient.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from claude_code_server import ClaudeCodeClient, ClaudeConfig, OutputFormat, PermissionMode


def main():
    print("=" * 60)
    print("Claude Code Server - Simple Chat Example")
    print("=" * 60)

    # Create client with configuration
    client = ClaudeCodeClient(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            permission_mode=PermissionMode.BYPASS_PERMISSIONS,
            timeout=60,
        )
    )

    # Get version
    print(f"\nClaude CLI Version: {client.get_version()}")

    # Send a simple message
    print("\n→ Sending message: 'Hello, Claude!'")
    response = client.chat("Hello, Claude! Please introduce yourself briefly.")

    print(f"\n← Claude responded:")
    print(response.content)
    print(f"\nSuccess: {response.success}")


if __name__ == "__main__":
    main()
