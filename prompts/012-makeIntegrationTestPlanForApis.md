# Integration Test Plan for Discovery API

## Objectives
- Verify notebook and source endpoints satisfy the documented contract (status codes, payloads, validation, and error semantics).
- Exercise primary user workflows end-to-end: notebook creation and lifecycle operations, source ingestion, soft delete/restore, and metadata management.
- Ensure integrations with external providers (file storage, content extraction, web fetch) behave predictably when substituted with deterministic test doubles.

## Scope
- Endpoints in the `/api/notebooks` and `/api/sources` namespaces plus their sub-routes.
- FastAPI application as wired in `src/api/main.py`, real database persistence layer, and dependency override hooks.
- Excludes background tasks, authentication/authorization flows (none currently enforced), and downstream analytics.

## Environment & Tooling
- Boot database via `pgDockerCompose/docker-compose.yaml`; run `alembic upgrade head` to migrate schema.
- Launch API with test configuration (set `DATABASE_URL`, `FILE_STORAGE_ROOT`, etc.) targeting disposable resources under `/tmp/discovery-tests`.
- Use `pytest` + `httpx.AsyncClient` or FastAPI `TestClient` inside `tests/integration`.
- Provide dependency overrides for:
	- `FileStorageProvider` → temp directory implementation recording stored bytes.
	- `ContentExtractionProvider` → stub returning deterministic text and metadata.
	- `WebFetchProvider` → stub returning synthetic HTML/title content.

## Data Management
- Create notebooks and sources through the API within fixtures to mirror real usage.
- Wrap each test in a database transaction rollback fixture or truncate tables between tests to keep isolation.
- Generate UUIDs via the API responses; for 404 paths, use `uuid4()` that does not exist in DB.
- Maintain deterministic timestamps by freezing time when necessary (e.g., `freezegun`) or relaxing assertions to ranges.

## Test Execution Strategy
1. Session-scoped fixture: spin up FastAPI app with dependency overrides and database connection.
2. Function-scoped fixture: start transaction/savepoint; roll back after test.
3. Seed baseline notebook (via `POST /api/notebooks`) for source-related tests.
4. Assert responses with JSON schema helpers or Pydantic models; cross-check DB state via repository interfaces where necessary.
5. Clean up temp storage folders after suite completes.

## Notebook Endpoint Coverage

| Endpoint | Scenario | Assertions |
| --- | --- | --- |
| `POST /api/notebooks` | minimal payload (name only) | 201; response fields populated; `source_count=0`; persists in DB |
|  | payload with description & tags | 201; tags stored and echoed back |
|  | duplicate name within tenant | 409; error body with `error="duplicate_notebook_name"` (adjust to actual string) |
|  | missing name | 400; validation errors include `name` |
| `GET /api/notebooks` | default listing | 200; length equals seeded count; sorted by `updated_at desc` |
|  | filter by tags (body payload) | 200; every notebook contains requested tag |
|  | pagination (`limit`/`offset`) | 200; windowed results; `total` unchanged |
| `GET /api/notebooks/{id}` | existing notebook | 200; response matches created notebook |
|  | unknown UUID | 404; error response |
| `PUT /api/notebooks/{id}` | full update name/description/tags | 200; DB reflects values; `updated_at` advanced |
|  | partial update description only | 200; name unchanged |
|  | duplicate name collision | 409; conflict error |
|  | invalid payload (empty string name) | 400; validation error |
| `DELETE /api/notebooks/{id}` | delete without sources | 204; subsequent `GET` returns 404 |
|  | delete with sources, `cascade=false` | 400; validation error with reason |
|  | delete with sources, `cascade=true` | 204; notebook gone; sources soft-deleted |
|  | repeat delete | 404 |
| `PATCH /api/notebooks/{id}/rename` | rename success | 200; new name + updated timestamp |
|  | rename to duplicate name | 409 |
|  | rename invalid name | 400 |
| `POST /api/notebooks/{id}/tags` | add new tags | 200; union of existing + new, no duplicates |
|  | add duplicate tag | 200; duplicates removed |
|  | notebook missing | 404 |
| `DELETE /api/notebooks/{id}/tags` | remove existing tags | 200; tag removed |
|  | remove tag absent | 200; tags unchanged |

## Source Endpoint Coverage

| Endpoint | Scenario | Assertions |
| --- | --- | --- |
| `POST /api/sources/file` | import markdown file | 201; stored with `source_type="file"`; storage provider called |
|  | duplicate content hash same notebook | 409 conflict |
|  | missing notebook id | 400 validation |
|  | notebook not found | 404 |
| `POST /api/sources/url` | import with provided title | 201; response includes supplied title |
|  | import without title (fetch stub) | 201; title from stub |
|  | duplicate URL hash | 409 |
|  | notebook not found | 404 |
| `GET /api/sources/{id}` | fetch existing | 200; matches stored data |
|  | `include_deleted=true` on soft-deleted source | 200; `deleted_at` populated |
|  | unknown id | 404 |
| `DELETE /api/sources/{id}` | soft delete | 204; DB `deleted_at` not null |
|  | delete missing id | 404 |
| `GET /api/sources/notebook/{notebook_id}` | list defaults | 200; counts match notebook `source_count` |
|  | filter by `source_type=file` | 200; all rows type file |
|  | include deleted | returns soft-deleted entry |
|  | pagination | respects `limit`/`offset` |
| `PATCH /api/sources/{id}/rename` | rename success | 200; name updated |
|  | invalid empty name | 400 |
|  | unknown id | 404 |
| `POST /api/sources/{id}/restore` | restore soft-deleted | 200; `deleted_at` null |
|  | restore not deleted | 400 |
|  | restore missing id | 404 |
| `POST /api/sources/{id}/extract` | trigger extraction | 200; stub extraction text saved |
|  | extract missing id | 404 |
| `GET /api/sources/{id}/preview` | default length | 200; preview length ≤500 |
|  | custom `length` query | 200; preview length matches |
|  | unknown id | 404 |

## Cross-Cutting Checks
- Validate response bodies against Pydantic response models to catch schema regressions.
- Confirm `created_at` remains constant while `updated_at` advances after update/rename operations.
- For cascade delete path, assert notebook removal updates related counts (e.g., list sources returns empty) and that audit fields remain.
- Ensure providers were invoked with expected arguments via stub spies (file path, URL, force flags).
- Log response payloads on assertion failures to accelerate debugging.

## Automation & Maintenance
- Organize tests into `tests/integration/test_notebooks_api.py` and `tests/integration/test_sources_api.py` with helper module for shared fixtures.
- Use `pytest.mark.integration` to allow selective execution.
- Add CI job running integration suite after unit tests; collect coverage for endpoints.
- Review this plan whenever OpenAPI spec changes; keep fixture stubs synchronized with provider interfaces.