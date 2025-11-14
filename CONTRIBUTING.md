# Contributing to Claude Code Server

Thank you for your interest in contributing to Claude Code Server! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-code-server.git
   cd claude-code-server
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for all public APIs
- Keep line length to 100 characters

We use `black` for code formatting and `ruff` for linting:

```bash
# Format code
black claude_code_server tests examples

# Lint code
ruff check claude_code_server tests examples
```

### Testing

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=claude_code_server --cov-report=html
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for streaming responses
fix: Handle timeout errors correctly
docs: Update README with new examples
test: Add tests for session management
```

## Pull Request Process

1. **Update documentation** - Add/update docstrings and README if needed
2. **Add tests** - Ensure your code is tested
3. **Run tests** - All tests must pass
4. **Update CHANGELOG** - Add your changes to CHANGELOG.md
5. **Create PR** - Provide a clear description of your changes

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts

## Project Structure

```
claude-code-server/
├── claude_code_server/      # Main package
│   ├── __init__.py          # Package exports
│   ├── client.py            # ClaudeCodeClient
│   ├── session.py           # Session management
│   ├── types.py             # Type definitions
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Test suite
├── examples/                # Example scripts
├── docs/                    # Documentation
└── README.md
```

## Feature Requests

Have an idea? Open an issue with:
- Clear description of the feature
- Use cases
- Example code (if applicable)

## Bug Reports

Found a bug? Open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, Claude Code version)

## Questions?

Feel free to:
- Open a discussion on GitHub
- Ask in pull request comments
- Reach out to maintainers

Thank you for contributing! 🎉
