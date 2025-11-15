#!/usr/bin/env python3
"""
Standalone test - This should be run OUTSIDE of Claude Code.

This demonstrates how claude-code-server is meant to be used:
in a standalone Python application, not within Claude Code itself.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from claude_code_server import ClaudeCodeClient, ClaudeConfig, OutputFormat


def main():
    print("=" * 70)
    print("Standalone Test - Run this OUTSIDE Claude Code")
    print("=" * 70)

    # Check if running inside Claude Code
    if os.environ.get("CLAUDECODE") == "1":
        print("\n⚠️  WARNING: You are running this inside Claude Code!")
        print("   This test is meant to be run in a standalone Python environment.")
        print("\n   To test properly:")
        print("   1. Open a new terminal (outside Claude Code)")
        print("   2. Run: python3 test_standalone.py")
        print("\n   Continuing anyway, but it may hang...\n")

    client = ClaudeCodeClient(
        config=ClaudeConfig(
            output_format=OutputFormat.JSON,
            timeout=10,
        )
    )

    print(f"\nClaude CLI Version: {client.get_version()}")

    print("\nSending test message...")
    try:
        response = client.chat("Say 'Hello from standalone Python!'")
        print(f"\n✓ Success!")
        print(f"Response: {response.content[:200]}...")
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
