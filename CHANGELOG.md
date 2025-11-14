# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-14

### Added
- Initial release of Claude Code Server
- Core `ClaudeCodeClient` for interacting with Claude CLI
- Session management with `SessionManager`
- Multiple storage backends (InMemory, Redis)
- Comprehensive type definitions with Pydantic
- Error handling and custom exceptions
- Configuration management via `ClaudeConfig`
- Support for all Claude CLI options:
  - Output formats (text, json, streaming-json)
  - Permission modes (default, acceptEdits, bypassPermissions, plan)
  - Tool restrictions
  - Session resumption
  - Custom system prompts
  - Model selection
- Example scripts:
  - Simple chat
  - Multi-turn conversations
  - Webhook bot pattern
- Comprehensive documentation
- Test suite with pytest
- Type checking with mypy
- Code formatting with black
- Linting with ruff

### Documentation
- Complete README with usage examples
- API documentation via docstrings
- Contributing guidelines
- License (MIT)
- Example code for common use cases

## [Unreleased]

### Planned Features
- FastAPI server wrapper
- WebSocket streaming support
- PostgreSQL session storage backend
- SQLite session storage backend
- Enhanced error retry logic
- Metrics and monitoring
- Docker container support
- PyPI package publication
