#!/usr/bin/env python3
"""
Start Claude Code Server API.

Usage:
    python start_server.py
    python start_server.py --config config.yaml
    python start_server.py --port 8080
"""

import argparse
import uvicorn
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_code_server_api import create_app, load_config
from claude_code_server.logger import setup_logging


def main():
    parser = argparse.ArgumentParser(description="Start Claude Code Server API")
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to config YAML file",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to (overrides config)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=None,
        help="Port to bind to (overrides config)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development)",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of worker processes",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Initialize logging system (before creating app)
    setup_logging(config.logging.model_dump())

    # Override with command line args
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.reload:
        config.reload = args.reload
    if args.workers:
        config.workers = args.workers

    # Create app
    app = create_app(config)

    # Print startup info
    print("=" * 60)
    print("🚀 Claude Code Server API")
    print("=" * 60)
    print(f"   Version: 0.1.0")
    print(f"   Host: {config.host}")
    print(f"   Port: {config.port}")
    print(f"   Working Dir: {config.working_directory}")
    print(f"   Claude Binary: {config.claude_bin}")
    print(f"   Session Store: {config.session_store_type}")
    if config.api_key:
        print(f"   API Key: {'*' * 8} (enabled)")
    print("=" * 60)
    print()
    print(f"📖 API Docs: http://{config.host}:{config.port}/docs")
    print(f"❤️  Health: http://{config.host}:{config.port}/health")
    print()

    # Run server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=config.reload,
        workers=config.workers if not config.reload else 1,
    )


if __name__ == "__main__":
    main()
