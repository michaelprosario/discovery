# Development Scripts

Helper scripts for common development tasks using **uv**.

## Available Scripts

### setup.sh
Installs uv (if needed) and syncs all project dependencies.

```bash
./scripts/setup.sh
```

### dev.sh
Starts the API development server with auto-reload.

```bash
./scripts/dev.sh
```

Server will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### test.sh
Runs the test suite.

```bash
# Run all tests
./scripts/test.sh

# Run specific test path
./scripts/test.sh tests/unit/
./scripts/test.sh tests/integration/
```

## Direct uv Commands

You can also use uv commands directly:

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Start server
uv run uvicorn src.api.main:app --reload

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Update dependencies
uv sync --upgrade
```

## Why uv?

**uv** is a fast Python package installer and resolver written in Rust:

- ⚡ 10-100x faster than pip
- 🔒 Reliable dependency resolution
- 🎯 Drop-in replacement for pip and pip-tools
- 📦 Handles virtual environments automatically
- 🔄 Compatible with existing Python projects

Learn more: https://github.com/astral-sh/uv
