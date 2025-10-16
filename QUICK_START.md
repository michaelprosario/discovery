# Quick Start Guide

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

## Run Tests

```bash
# All tests (42 tests)
pytest tests/ -v

# Expected output: 42 passed ✅
```

## Run API Server

```bash
# Start server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Access docs: http://localhost:8000/docs
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
open http://localhost:8000/docs
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
