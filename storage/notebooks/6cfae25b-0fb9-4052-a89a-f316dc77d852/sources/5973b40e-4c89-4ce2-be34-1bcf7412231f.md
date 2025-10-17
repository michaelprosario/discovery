# Quick Start Guide

## Prerequisites

Install **uv** (fast Python package manager):

```bash
# Unix/macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

## Setup

```bash
# Sync dependencies (creates .venv automatically)
uv sync

# This installs all dependencies from pyproject.toml including dev dependencies
```

## Run Tests

```bash
# All tests (42 tests) using uv run
uv run pytest tests/ -v

# Expected output: 42 passed ✅

# Or run specific test files
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
```

## Run API Server 


## export DATABASE_URL
export DATABASE_URL="postgresql://postgres:Foobar321@localhost:5432/postgres"

```bash
# Start server using uv run
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Access docs: http://localhost:8000/docs
```

**Alternative (using activated virtual environment):**
```bash
# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# Run server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Try the API

```bash
# Create a notebook
curl -X POST http://localhost:8000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{"name": "My Notebook", "tags": ["demo"]}'

# List notebooks
curl http://localhost:8000/api/notebooks

# Access interactive docs
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
start http://localhost:8000/docs  # Windows
```

## Project Structure

```
src/
├── core/          # Business logic (NO external dependencies)
├── infrastructure/ # Repository implementations
└── api/           # FastAPI endpoints

tests/
├── unit/          # 38 unit tests
└── integration/   # 4 integration tests
```

## Key Files

- `src/core/entities/notebook.py` - Domain entity
- `src/core/services/notebook_management_service.py` - Business logic
- `src/core/interfaces/repositories/i_notebook_repository.py` - Repository interface
- `src/api/notebooks_router.py` - API endpoints
- `tests/unit/test_notebook_management_service.py` - Unit tests

## Architecture

```
┌─────────────┐
│   FastAPI   │  (API Layer)
└──────┬──────┘
       │ depends on
┌──────▼──────┐
│    Core     │  (Business Logic - Framework Independent)
└──────┬──────┘
       │ implements
┌──────▼──────┐
│Infrastructure│ (Repositories, External Services)
└─────────────┘
```

## Documentation

- `README_API.md` - Full API documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation details
- `specs/domain_model.md` - Domain design
- `specs/core_stories.md` - User stories
- `specs/clean_architecture.md` - Architecture rules

## Next Steps

See `IMPLEMENTATION_SUMMARY.md` for:
- Complete feature list
- Test coverage details
- Architecture benefits
- Future enhancements
