"""Integration tests for API endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
import sys
sys.path.insert(0, '/workspaces/discovery')

from src.api.main import app
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository
from src.api.notebooks_router import get_notebook_repository


@pytest.fixture(scope="function")
def override_get_repository():
    """Override the repository dependency with in-memory repository for testing."""
    test_repository = InMemoryNotebookRepository()

    def _get_test_repository():
        yield test_repository

    # Override the dependency
    app.dependency_overrides[get_notebook_repository] = _get_test_repository

    yield

    # Clean up
    test_repository.clear()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Discovery API"


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_notebook(override_get_repository):
    """Test creating a notebook."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/notebooks",
            json={
                "name": "Test Notebook",
                "description": "A test notebook",
                "tags": ["test", "demo"]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Notebook"
        assert data["description"] == "A test notebook"
        assert set(data["tags"]) == {"test", "demo"}
        assert "id" in data


@pytest.mark.asyncio
async def test_full_crud_workflow(override_get_repository):
    """Test complete CRUD workflow."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create
        create_response = await client.post(
            "/api/notebooks",
            json={"name": "CRUD Test", "tags": ["test"]}
        )
        assert create_response.status_code == 201
        notebook_id = create_response.json()["id"]

        # Read
        get_response = await client.get(f"/api/notebooks/{notebook_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "CRUD Test"

        # Update
        update_response = await client.put(
            f"/api/notebooks/{notebook_id}",
            json={"description": "Updated"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "Updated"

        # List
        list_response = await client.get("/api/notebooks")
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1

        # Delete
        delete_response = await client.delete(f"/api/notebooks/{notebook_id}")
        assert delete_response.status_code == 204

        # Verify deleted
        get_deleted_response = await client.get(f"/api/notebooks/{notebook_id}")
        assert get_deleted_response.status_code == 404
