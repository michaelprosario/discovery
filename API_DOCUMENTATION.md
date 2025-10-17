# Discovery API Documentation

Complete API documentation for the Discovery application - a local NotebookLM-like research application following Clean Architecture principles.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Authentication

Currently, the API does not require authentication. This is suitable for local usage. For production deployment, add authentication middleware.

## API Endpoints

### Health & Info

#### GET /
Get API information

**Response (200 OK)**:
```json
{
  "message": "Discovery API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

#### GET /health
Health check endpoint

**Response (200 OK)**:
```json
{
  "status": "healthy"
}
```

---

## Notebooks API

### Create Notebook

**POST** `/api/notebooks`

Create a new notebook for organizing research sources.

**Request Body**:
```json
{
  "name": "AI Research 2024",
  "description": "Research on artificial intelligence trends",
  "tags": ["ai", "machine-learning", "research"]
}
```

**Response (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "AI Research 2024",
  "description": "Research on artificial intelligence trends",
  "tags": ["ai", "machine-learning", "research"],
  "source_count": 0,
  "output_count": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Validation error (empty name, name too long, etc.)
- `409 Conflict`: Notebook name already exists

---

### Get Notebook

**GET** `/api/notebooks/{notebook_id}`

Retrieve a specific notebook by ID.

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier

**Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "AI Research 2024",
  "description": "Research on artificial intelligence trends",
  "tags": ["ai", "machine-learning", "research"],
  "source_count": 5,
  "output_count": 2,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Notebook does not exist

---

### List Notebooks

**GET** `/api/notebooks`

List all notebooks with optional filtering and sorting.

**Query Parameters**:
- `tags` (array, optional): Filter by tags (can specify multiple)
- `sort_by` (string, optional): Sort field (`name`, `created_at`, `updated_at`, `source_count`)
  - Default: `updated_at`
- `sort_order` (string, optional): Sort order (`asc`, `desc`)
  - Default: `desc`
- `limit` (integer, optional): Maximum number of results
- `offset` (integer, optional): Number of results to skip (pagination)
  - Default: 0

**Example Request**:
```
GET /api/notebooks?tags=ai&tags=research&sort_by=name&sort_order=asc&limit=10&offset=0
```

**Response (200 OK)**:
```json
{
  "notebooks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "AI Research 2024",
      "description": "Research on artificial intelligence trends",
      "tags": ["ai", "machine-learning", "research"],
      "source_count": 5,
      "output_count": 2,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-16T14:20:00Z"
    }
  ],
  "total": 1
}
```

---

### Update Notebook

**PUT** `/api/notebooks/{notebook_id}`

Update notebook details (partial updates supported).

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier

**Request Body** (all fields optional):
```json
{
  "name": "AI Research 2025",
  "description": "Updated research focus",
  "tags": ["ai", "deep-learning"]
}
```

**Response (200 OK)**: Returns updated notebook

**Error Responses**:
- `400 Bad Request`: Validation error
- `404 Not Found`: Notebook does not exist
- `409 Conflict`: New name conflicts with existing notebook

---

### Rename Notebook

**PATCH** `/api/notebooks/{notebook_id}/rename`

Rename a notebook (specialized endpoint for name changes).

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier

**Request Body**:
```json
{
  "new_name": "Machine Learning Research"
}
```

**Response (200 OK)**: Returns renamed notebook

**Error Responses**:
- `400 Bad Request`: Invalid name
- `404 Not Found`: Notebook does not exist
- `409 Conflict`: Name already in use

---

### Delete Notebook

**DELETE** `/api/notebooks/{notebook_id}`

Delete a notebook (and optionally its sources).

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier
- `cascade` (query, boolean, optional): Delete all sources and outputs
  - Default: false

**Example Requests**:
```
DELETE /api/notebooks/{id}              # Fails if notebook has sources
DELETE /api/notebooks/{id}?cascade=true # Deletes notebook and all sources
```

**Response (204 No Content)**: Successful deletion

**Error Responses**:
- `400 Bad Request`: Cannot delete (has sources and cascade=false)
- `404 Not Found`: Notebook does not exist

---

### Add Tags

**POST** `/api/notebooks/{notebook_id}/tags`

Add tags to a notebook.

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier

**Request Body**:
```json
{
  "tags": ["nlp", "transformer"]
}
```

**Response (200 OK)**: Returns notebook with updated tags

**Error Responses**:
- `404 Not Found`: Notebook does not exist

---

### Remove Tags

**DELETE** `/api/notebooks/{notebook_id}/tags`

Remove tags from a notebook.

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier

**Request Body**:
```json
{
  "tags": ["old-tag"]
}
```

**Response (200 OK)**: Returns notebook with updated tags

**Error Responses**:
- `404 Not Found`: Notebook does not exist

---

## Sources API

### Import File Source

**POST** `/api/sources/file`

Import a file source (PDF, DOCX, TXT, MD) into a notebook.

**The content is automatically extracted from the file** - you only need to provide the file path!

**Request Body**:
```json
{
  "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Research Paper on Neural Networks",
  "file_path": "/documents/neural_networks.pdf",
  "file_type": "pdf"
}
```

**Fields**:
- `notebook_id` (UUID, required): Parent notebook
- `name` (string, required): Source display name (1-500 chars)
- `file_path` (string, required): Path to the file on the server
  - Content will be automatically extracted from this file
- `file_type` (string, required): File type (`pdf`, `docx`, `doc`, `txt`, `md`)

**How It Works**:
1. System validates the file path exists and is accessible
2. Extracts text content from the file using the appropriate extraction method:
   - PDF: Uses PyPDF2 to extract text from all pages
   - DOCX: Uses python-docx to extract paragraphs and tables
   - DOC: Uses antiword system utility (requires `antiword` to be installed)
   - TXT/MD: Direct text file reading with encoding detection
3. Calculates file size automatically
4. Generates content hash for duplicate detection
5. Extracts metadata (file name, extension)
6. Creates source with extracted content

**Response (201 Created)**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Research Paper on Neural Networks",
  "source_type": "file",
  "file_type": "pdf",
  "url": null,
  "file_path": "/documents/neural_networks.pdf",
  "file_size": 2048576,
  "content_hash": "sha256_hash...",
  "extracted_text": "Extracted text content from the PDF...",
  "metadata": {
    "original_file_name": "neural_networks.pdf",
    "file_extension": ".pdf"
  },
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z",
  "deleted_at": null
}
```

**Error Responses**:
- `400 Bad Request`: Validation error, file not found, unsupported file type, or extraction failed
- `404 Not Found`: Notebook does not exist
- `409 Conflict`: Duplicate content (same file content already imported)

---

### Import URL Source

**POST** `/api/sources/url`

Import a URL source (web page, article) into a notebook.

**The content AND title are automatically fetched from the URL** - you only need to provide the URL!

**Minimal Request Body**:
```json
{
  "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://arxiv.org/abs/1706.03762"
}
```

**Request Body with Custom Title**:
```json
{
  "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://arxiv.org/abs/1706.03762",
  "title": "Custom Title for This Source"
}
```

**Fields**:
- `notebook_id` (UUID, required): Parent notebook
- `url` (string, required): Source URL (must start with http:// or https://)
  - Content will be automatically fetched from this URL
  - Title will be automatically extracted if not provided
- `title` (string, optional): Custom title/name for the source
  - If not provided, the page title will be extracted automatically

**How It Works**:
1. System validates the URL format
2. Fetches content from the URL using HTTP request
3. Extracts page title (from `<title>` tag, og:title, or `<h1>`)
4. Extracts main text content from HTML (removing ads, navigation, etc.)
5. Extracts metadata (description, author, etc.)
6. Uses provided title OR extracted title as the source name
7. Creates source with fetched content

**Response (201 Created)**: Returns source object (similar to file source)

**Error Responses**:
- `400 Bad Request`: Validation error, invalid URL format, or failed to fetch URL
- `404 Not Found`: Notebook does not exist
- `409 Conflict`: Duplicate content (same URL content already imported)

---

### Get Source

**GET** `/api/sources/{source_id}`

Retrieve a specific source by ID.

**Parameters**:
- `source_id` (path, UUID): Source identifier
- `include_deleted` (query, boolean, optional): Include soft-deleted sources
  - Default: false

**Response (200 OK)**: Returns source object

**Error Responses**:
- `404 Not Found`: Source does not exist

---

### List Sources by Notebook

**GET** `/api/sources/notebook/{notebook_id}`

List all sources for a specific notebook.

**Parameters**:
- `notebook_id` (path, UUID): Notebook identifier
- `include_deleted` (query, boolean, optional): Include soft-deleted sources
- `source_type` (query, string, optional): Filter by type (`file`, `url`)
- `file_type` (query, string, optional): Filter by file type (`pdf`, `docx`, etc.)
- `sort_by` (query, string, optional): Sort field (`name`, `created_at`, `updated_at`)
  - Default: `created_at`
- `sort_order` (query, string, optional): Sort order (`asc`, `desc`)
  - Default: `desc`
- `limit` (query, integer, optional): Maximum results
- `offset` (query, integer, optional): Pagination offset

**Example Request**:
```
GET /api/sources/notebook/{id}?source_type=file&file_type=pdf&sort_by=name&limit=20
```

**Response (200 OK)**:
```json
{
  "sources": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Research Paper",
      "source_type": "file",
      "file_type": "pdf",
      "file_path": "/path/to/file.pdf",
      "content_hash": "sha256...",
      "created_at": "2024-01-16T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Rename Source

**PATCH** `/api/sources/{source_id}/rename`

Rename a source.

**Parameters**:
- `source_id` (path, UUID): Source identifier

**Request Body**:
```json
{
  "new_name": "Updated Source Name"
}
```

**Response (200 OK)**: Returns updated source

**Error Responses**:
- `400 Bad Request`: Invalid name
- `404 Not Found`: Source does not exist

---

### Delete Source

**DELETE** `/api/sources/{source_id}`

Soft delete a source (can be restored later).

**Parameters**:
- `source_id` (path, UUID): Source identifier
- `notebook_id` (query, UUID, required): Parent notebook ID (for validation)

**Example Request**:
```
DELETE /api/sources/{source_id}?notebook_id={notebook_id}
```

**Response (204 No Content)**: Successful deletion

**Error Responses**:
- `404 Not Found`: Source does not exist

---

### Restore Source

**POST** `/api/sources/{source_id}/restore`

Restore a soft-deleted source.

**Parameters**:
- `source_id` (path, UUID): Source identifier
- `notebook_id` (query, UUID, required): Parent notebook ID

**Example Request**:
```
POST /api/sources/{source_id}/restore?notebook_id={notebook_id}
```

**Response (200 OK)**: Returns restored source

**Error Responses**:
- `400 Bad Request`: Source is not deleted
- `404 Not Found`: Source does not exist

---

### Extract Content

**POST** `/api/sources/{source_id}/extract`

Extract text content from a source file.

**Parameters**:
- `source_id` (path, UUID): Source identifier

**Request Body**:
```json
{
  "force": false
}
```

**Fields**:
- `force` (boolean, optional): Force re-extraction even if already extracted
  - Default: false

**Response (200 OK)**: Returns source with extracted text populated

**Error Responses**:
- `404 Not Found`: Source does not exist

**Note**: This endpoint requires content extraction providers to be configured. Returns source as-is if providers are not available.

---

### Get Source Preview

**GET** `/api/sources/{source_id}/preview`

Get a preview of source content.

**Parameters**:
- `source_id` (path, UUID): Source identifier
- `length` (query, integer, optional): Preview length in characters
  - Default: 500
  - Max: 5000

**Example Request**:
```
GET /api/sources/{source_id}/preview?length=1000
```

**Response (200 OK)**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Research Paper",
  "preview": "Abstract: This paper introduces...",
  "full_text_length": 25000
}
```

**Error Responses**:
- `404 Not Found`: Source does not exist

---

## Error Responses

All error responses follow a consistent format:

### Validation Error (400)
```json
{
  "error": "Validation failed",
  "validation_errors": [
    {
      "field": "name",
      "message": "Name cannot be empty or whitespace only",
      "code": "REQUIRED"
    }
  ]
}
```

### Generic Error (4xx, 5xx)
```json
{
  "error": "Error message description"
}
```

## Common Status Codes

- `200 OK`: Successful GET/PUT/PATCH request
- `201 Created`: Successful POST request (resource created)
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Validation error or malformed request
- `404 Not Found`: Resource does not exist
- `409 Conflict`: Resource conflict (duplicate name, etc.)
- `500 Internal Server Error`: Server error

## Data Types

### UUID Format
All IDs are UUIDs in standard format:
```
550e8400-e29b-41d4-a716-446655440000
```

### DateTime Format
All timestamps use ISO 8601 format with UTC timezone:
```
2024-01-15T10:30:00Z
```

### Enum Values

**SourceType**: `file`, `url`

**FileType**: `pdf`, `docx`, `doc`, `txt`, `md`

**SortOption**: `name`, `created_at`, `updated_at`, `source_count`

**SortOrder**: `asc`, `desc`

## Examples

### Complete Workflow Example

1. **Create a notebook**:
```bash
curl -X POST http://localhost:8000/api/notebooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Machine Learning Papers",
    "description": "Collection of ML research papers",
    "tags": ["ml", "research"]
  }'
```

2. **Import a PDF source** (content extracted automatically):
```bash
curl -X POST http://localhost:8000/api/sources/file \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Attention Is All You Need",
    "file_path": "/papers/attention.pdf",
    "file_type": "pdf"
  }'
```

3. **Import a URL source** (content and title fetched automatically):
```bash
curl -X POST http://localhost:8000/api/sources/url \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "url": "https://arxiv.org/abs/1706.03762"
  }'
```

Or with custom title:
```bash
curl -X POST http://localhost:8000/api/sources/url \
  -H "Content-Type: application/json" \
  -d '{
    "notebook_id": "550e8400-e29b-41d4-a716-446655440000",
    "url": "https://arxiv.org/abs/1706.03762",
    "title": "Attention Is All You Need - Transformer Paper"
  }'
```

4. **List all sources in notebook**:
```bash
curl -X GET "http://localhost:8000/api/sources/notebook/550e8400-e29b-41d4-a716-446655440000"
```

5. **Get source preview**:
```bash
curl -X GET "http://localhost:8000/api/sources/660e8400-e29b-41d4-a716-446655440001/preview?length=500"
```

## Running the API

### Start the Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Set database connection
export DATABASE_URL="postgresql://postgres:Foobar321@localhost:5432/postgres"

# Run migrations
alembic upgrade head

# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

The API follows Clean Architecture principles:

- **API Layer** (`src/api/`): FastAPI routers and DTOs
- **Core Layer** (`src/core/`): Business logic, services, entities
- **Infrastructure Layer** (`src/infrastructure/`): Repositories, database

**Dependencies flow inward**: API → Core ← Infrastructure

### Key Design Patterns

1. **Dependency Injection**: Repositories and services injected via FastAPI's DI
2. **Result Pattern**: All service methods return `Result<T>` for error handling
3. **CQRS**: Commands for writes, Queries for reads
4. **Repository Pattern**: Abstract data access behind interfaces
5. **DTO Pattern**: Separate API models from domain entities

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

All 113 unit tests pass, covering:
- NotebookManagementService (38 tests)
- SourceIngestionService (24 tests)
- PostgresNotebookRepository (23 tests)
- PostgresSourceRepository (26 tests)

## Future Enhancements

Planned features:
- Output generation endpoints (summaries, blog posts, etc.)
- Template management endpoints
- Full-text search across sources
- File upload support (multipart/form-data)
- Authentication and authorization
- Rate limiting
- Caching (Redis)
- Background job processing

## Support

For issues or questions:
- Check interactive documentation: http://localhost:8000/docs
- Review unit tests for usage examples
- See `MIGRATIONS_GUIDE.md` for database setup
