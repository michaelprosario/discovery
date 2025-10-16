# UV Migration Guide

Successfully migrated the Discovery project from `pip` to **uv** - the fast Python package manager.

## What Changed

### 1. Project Configuration ✅

**pyproject.toml** - Updated with:
- Project metadata (`[project]` section)
- Dependencies defined in `[project.dependencies]`
- Dev dependencies in `[dependency-groups]` (new uv format)
- Hatchling build configuration with source packages
- Removed deprecated `tool.uv.dev-dependencies`

**New Files:**
- `.python-version` - Specifies Python 3.12

### 2. Documentation Updates ✅

Updated all documentation to use `uv` commands:
- `README_API.md` - Installation and running instructions
- `QUICK_START.md` - Quick start guide with uv
- `IMPLEMENTATION_SUMMARY.md` - How to run section

### 3. Development Scripts ✅

Created helper scripts in `scripts/`:
- `setup.sh` - One-command project setup
- `dev.sh` - Start development server
- `test.sh` - Run tests
- `scripts/README.md` - Scripts documentation

All scripts are executable and use `uv` commands.

## Migration Commands

### Old (pip) vs New (uv)

| Task | Old Command | New Command |
|------|-------------|-------------|
| **Install dependencies** | `pip install -r requirements.txt` | `uv sync` |
| **Add dependency** | `pip install <package>` | `uv add <package>` |
| **Add dev dependency** | `pip install --dev <package>` | `uv add --dev <package>` |
| **Run tests** | `pytest tests/ -v` | `uv run pytest tests/ -v` |
| **Start server** | `python -m uvicorn ...` | `uv run uvicorn ...` |
| **Activate venv** | `source venv/bin/activate` | `source .venv/bin/activate` |

## Quick Start with uv

### Install uv (First Time)
```bash
# Unix/macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Project
```bash
# Sync dependencies (creates .venv automatically)
uv sync

# This installs all dependencies from pyproject.toml
```

### Run Tests
```bash
# All tests
uv run pytest tests/ -v

# Specific tests
uv run pytest tests/unit/ -v
```

**Result: 42/42 tests passing ✅**

### Start Development Server
```bash
uv run uvicorn src.api.main:app --reload
```

Access at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Why uv?

### Speed Improvements 🚀
- **10-100x faster** than pip for package installation
- Parallel downloads and installations
- Efficient caching and dependency resolution

### Better Dependency Management
- Reliable, deterministic dependency resolution
- Automatic virtual environment management
- Compatible with existing pip workflows

### Developer Experience
- Single command setup (`uv sync`)
- No need to manually create/activate virtual environments
- Works with existing `requirements.txt` and `pyproject.toml`

## Project Structure Changes

### Before
```
discovery/
├── requirements.txt       # pip dependencies
├── pyproject.toml        # minimal config
└── ...
```

### After
```
discovery/
├── pyproject.toml        # Complete project config with dependencies
├── .python-version       # Python version specification
├── .venv/               # Auto-created virtual environment
├── uv.lock              # Dependency lock file (auto-generated)
├── scripts/             # Helper scripts
│   ├── setup.sh
│   ├── dev.sh
│   ├── test.sh
│   └── README.md
└── ...
```

## Removed Files

- `requirements.txt` - Replaced by `pyproject.toml` dependencies
- `verify_api.py` - Replaced by integration tests

## Benefits for This Project

### 1. Faster Development
- Dependencies install in seconds instead of minutes
- Quick iteration during development

### 2. Consistent Environment
- Lock file ensures everyone has same dependencies
- No version conflicts or surprises

### 3. Simplified Commands
```bash
# One command to rule them all
uv sync

# Run anything without activating venv
uv run pytest
uv run uvicorn ...
```

### 4. Better CI/CD
- Faster build times in CI
- More reliable dependency resolution
- Consistent across environments

## Testing Verification

Ran complete test suite with uv:
```bash
uv run pytest tests/ -v
```

**Result:**
- ✅ 42/42 tests passing
- ✅ All unit tests work
- ✅ All integration tests work
- ✅ Same behavior as pip

## Common uv Commands

```bash
# Sync dependencies (like pip install -r requirements.txt)
uv sync

# Add a package
uv add requests

# Add a dev dependency
uv add --dev pytest

# Remove a package
uv remove requests

# Upgrade all dependencies
uv sync --upgrade

# Lock dependencies without installing
uv lock

# Run Python script
uv run python script.py

# Run any command in venv
uv run <command>

# Create requirements.txt for compatibility
uv pip freeze > requirements.txt
```

## Backwards Compatibility

The project remains compatible with pip:
```bash
# Still works (not recommended)
pip install -e .
pytest tests/
```

But uv is now the recommended approach for:
- Faster installations
- Better dependency management
- Modern Python development workflow

## Resources

- **uv Documentation**: https://github.com/astral-sh/uv
- **Installation Guide**: https://docs.astral.sh/uv/
- **GitHub**: https://github.com/astral-sh/uv

## Summary

✅ **Successfully migrated to uv**
- All dependencies working
- All 42 tests passing
- Documentation updated
- Helper scripts created
- Faster, more reliable builds

**Recommended for all new development work!**
