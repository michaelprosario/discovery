# Discovery API - Notebook CRUD Implementation

This document describes the implementation of the Notebook CRUD operations following Clean Architecture principles.

## Architecture Overview

The implementation follows **Clean Architecture** (Ardalis/Steve Smith style) with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (FastAPI endpoints, DTOs, Request/Response handling)        │
└─────────────────────┬───────────────────────────────────────┘
                      │ depends on
┌─────────────────────▼───────────────────────────────────────┐
│                     Core Layer                               │
│  • Entities (Notebook)                                       │
│  • Services (NotebookManagementService)                      │
│  • Interfaces (INotebookRepository)                          │
│  • Commands, Queries, Results                                │
│  ⚠️  NO dependencies on external frameworks                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ implements
┌─────────────────────▼───────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  • Repository Implementations (InMemoryNotebookRepository)   │
│  • External service integrations                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles Applied

### 1. Dependency Inversion Principle (DIP)
- **Core** defines `INotebookRepository` interface
- **Infrastructure** implements `InMemoryNotebookRepository`
- **Services** depend on abstractions, not implementations

### 2. CQRS Pattern
- **Commands**: Modify state (CreateNotebookCommand, UpdateNotebookCommand, etc.)
- **Queries**: Read state (GetNotebookByIdQuery, ListNotebooksQuery, etc.)
- All service methods accept Command or Query objects

### 3. Result Pattern
- Services return `Result<T>` instead of throwing exceptions for business failures
- Explicit success/failure handling
- Rich error information with validation details

### 4. Clean Architecture Rules
✅ Core has minimal dependencies (zero external frameworks)
✅ Dependencies point inward (Infrastructure → Core ← API)
✅ Business logic in Core (entities and services)
✅ Highly testable (38 unit tests, all passing)

## Project Structure

```
src/
├── core/                          # Core business logic layer
│   ├── entities/
│   │   └── notebook.py           # Notebook domain entity
│   ├── services/
│   │   └── notebook_management_service.py  # Domain service
│   ├── interfaces/
│   │   └── repositories/
│   │       └── i_notebook_repository.py    # Repository abstraction
│   ├── commands/
│   │   └── notebook_commands.py  # Command objects (CQRS)
│   ├── queries/
│   │   └── notebook_queries.py   # Query objects (CQRS)
│   ├── results/
│   │   ├── result.py             # Result pattern implementation
│   │   └── validation_error.py   # Validation error model
│   └── value_objects/
│       └── enums.py              # Enum value objects
├── infrastructure/               # Infrastructure implementations
│   └── repositories/
│       └── in_memory_notebook_repository.py  # In-memory repo
└── api/                          # API/Presentation layer
    ├── main.py                   # FastAPI application
    ├── notebooks_router.py       # Notebook endpoints
    └── dtos.py                   # Request/Response DTOs

tests/
└── unit/
    └── test_notebook_management_service.py  # 38 unit tests
```

## API Endpoints

All endpoints are available at `/api/notebooks`:

### 1. Create Notebook
```http
POST /api/notebooks
Content-Type: application/json

{
  "name": "Research Project",
  "description": "My research notes",
  "tags": ["research", "science"]
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "name": "Research Project",
  "description": "My research notes",
  "tags": ["research", "science"],
  "source_count": 0,
  "output_count": 0,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 2. Get Notebook by ID
```http
GET /api/notebooks/{notebook_id}
```

**Response**: `200 OK`

### 3. List Notebooks
```http
GET /api/notebooks?tags=research&sort_by=name&sort_order=asc&limit=10&offset=0
```

**Query Parameters**:
- `tags`: Filter by tags (optional, can be multiple)
- `sort_by`: `name`, `created_at`, `updated_at`, `source_count` (default: `updated_at`)
- `sort_order`: `asc`, `desc` (default: `desc`)
- `limit`: Max results (optional)
- `offset`: Skip results (default: 0)

**Response**: `200 OK`
```json
{
  "notebooks": [...],
  "total": 10
}
```

### 4. Update Notebook
```http
PUT /api/notebooks/{notebook_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "New description",
  "tags": ["new", "tags"]
}
```

**Response**: `200 OK`

### 5. Rename Notebook
```http
PATCH /api/notebooks/{notebook_id}/rename
Content-Type: application/json

{
  "new_name": "New Name"
}
```

**Response**: `200 OK`

### 6. Delete Notebook
```http
DELETE /api/notebooks/{notebook_id}?cascade=false
```

**Query Parameters**:
- `cascade`: If `true`, delete all sources and outputs (default: `false`)

**Response**: `204 No Content`

### 7. Add Tags
```http
POST /api/notebooks/{notebook_id}/tags
Content-Type: application/json

{
  "tags": ["new", "tags"]
}
```

**Response**: `200 OK`

### 8. Remove Tags
```http
DELETE /api/notebooks/{notebook_id}/tags
Content-Type: application/json

{
  "tags": ["old", "tags"]
}
```

**Response**: `200 OK`

## Running the Application

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the API Server
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Run Unit Tests
```bash
pytest tests/unit/test_notebook_management_service.py -v
```

**Test Coverage**: 38 tests covering:
- ✅ Create notebooks (8 tests)
- ✅ Get notebooks (2 tests)
- ✅ Update notebooks (5 tests)
- ✅ Rename notebooks (3 tests)
- ✅ Delete notebooks (3 tests)
- ✅ List notebooks (6 tests)
- ✅ Tag operations (4 tests)
- ✅ Existence checks (5 tests)
- ✅ Get count (2 tests)

## Business Rules Enforced

### Notebook Entity Rules
1. Name is required and cannot be empty or whitespace-only
2. Name must be unique (case-insensitive)
3. Name cannot exceed 255 characters
4. Description cannot exceed 2000 characters
5. Tags are normalized (lowercase, trimmed)
6. Updated timestamp changes on any modification

### Service Rules
1. Duplicate names are rejected with validation error
2. Cannot delete notebook with sources/outputs unless `cascade=True`
3. All operations update the `updated_at` timestamp
4. Tag additions ignore duplicates
5. Tag removals are idempotent (no error if tag doesn't exist)

## Repository Interface (CRUD)

Following the domain model rules, `INotebookRepository` provides:

✅ `add(notebook)` - Add domain entity
✅ `update(notebook)` - Update domain entity
✅ `upsert(notebook)` - Upsert domain entity
✅ `get_by_id(id)` - Get entity by ID (UUID)
✅ `exists(id)` - Check if entity exists by ID
✅ `exists_by_name(name)` - Check name uniqueness
✅ `delete(id)` - Delete entity
✅ `get_all(query)` - List with filtering/sorting
✅ `count()` - Get total count

## Error Handling

### Validation Errors (400)
```json
{
  "error": "Validation failed: ...",
  "validation_errors": [
    {
      "field": "name",
      "message": "Name is required and cannot be empty",
      "code": "REQUIRED"
    }
  ]
}
```

### Not Found (404)
```json
{
  "error": "Notebook with ID {id} not found"
}
```

### Conflict - Duplicate Name (409)
```json
{
  "error": "A notebook with name 'Test' already exists"
}
```

## Testing Strategy

### Unit Tests
- Test Core layer in isolation
- Use in-memory repository (fast, no external dependencies)
- Mock-free testing (use real implementations where possible)
- Cover all business rules and edge cases

### Integration Tests (Future)
- Test with real database (SQLite/PostgreSQL)
- Test API endpoints end-to-end
- Test concurrent operations

## Next Steps

1. **Add SQLite Repository Implementation**
   - Implement `SqliteNotebookRepository` in Infrastructure layer
   - Use SQLAlchemy or raw SQL
   - Add migrations

2. **Add Source Management**
   - Implement Source entity and service
   - File upload handling
   - URL fetching and content extraction

3. **Add Output Generation**
   - Implement OutputFile entity and service
   - LLM integration (OpenAI, Anthropic, local models)
   - Template management

4. **Add Authentication & Authorization**
   - User management
   - JWT tokens
   - Multi-tenancy support

5. **Add Integration Tests**
   - API endpoint tests with TestClient
   - Database integration tests
   - E2E scenarios

## Architecture Benefits

### Testability
- Core layer has zero external dependencies
- Easy to unit test with in-memory implementations
- 38 tests run in < 1 second

### Maintainability
- Clear separation of concerns
- Changes to infrastructure don't affect Core
- Easy to swap implementations (e.g., in-memory → SQL → NoSQL)

### Flexibility
- Can add new repositories (PostgreSQL, MongoDB, etc.)
- Can add new API layers (GraphQL, gRPC)
- Can add new frontends (React, Vue, CLI)

### Clean Code
- Explicit error handling (no hidden exceptions)
- Type-safe with proper typing
- Self-documenting with clear interfaces

## Example Usage with curl

```bash
# Create notebook
curl -X POST http://localhost:8000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{"name": "My Research", "description": "Test", "tags": ["python"]}'

# List notebooks
curl http://localhost:8000/api/notebooks

# Get notebook by ID
curl http://localhost:8000/api/notebooks/{notebook_id}

# Update notebook
curl -X PUT http://localhost:8000/api/notebooks/{notebook_id} \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# Delete notebook
curl -X DELETE http://localhost:8000/api/notebooks/{notebook_id}
```

## Conclusion

This implementation demonstrates Clean Architecture principles with:
- ✅ Clear separation of Core, Infrastructure, and API layers
- ✅ Dependency Inversion (abstractions in Core)
- ✅ CQRS pattern for commands and queries
- ✅ Result pattern for explicit error handling
- ✅ Comprehensive unit testing (38 tests, all passing)
- ✅ RESTful API with FastAPI
- ✅ Full CRUD operations for Notebook entity

The architecture is ready to scale with additional entities (Source, OutputFile) and features.
