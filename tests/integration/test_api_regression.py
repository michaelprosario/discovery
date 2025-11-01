"""Regression tests for API endpoints."""
import pytest
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
import sys

sys.path.insert(0, '/workspaces/discovery')

from src.api.main import app
from tests.integration.test_sources_api import override_dependencies

root_url = "http://localhost:8000"

@pytest.mark.asyncio
async def test_create_and_get_notebook(override_dependencies):
    """Tests creating a notebook and then fetching it."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new notebook
        notebook_name = f"My Test Notebook {uuid4()}"
        response = await client.post("/api/notebooks", json={"name": notebook_name})
        assert response.status_code == 201
        created_notebook = response.json()
        assert created_notebook["name"] == notebook_name

        # Get the notebook
        notebook_id = created_notebook["id"]
        response = await client.get(f"/api/notebooks/{notebook_id}")
        assert response.status_code == 200
        fetched_notebook = response.json()
        assert fetched_notebook["name"] == notebook_name
        assert fetched_notebook["id"] == notebook_id

    

@pytest.mark.asyncio
async def test_health_check_endpoint(override_dependencies):
    """Test health check endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_notebooks_after_creation(override_dependencies):
    """Tests that a newly created notebook appears in the list of notebooks."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new notebook
        notebook_name = f"My Test Notebook {uuid4()}"
        create_response = await client.post("/api/notebooks", json={"name": notebook_name})
        assert create_response.status_code == 201
        created_notebook = create_response.json()
        notebook_id = created_notebook["id"]

        # List notebooks
        list_response = await client.get("/api/notebooks")
        assert list_response.status_code == 200
        listed_notebooks = list_response.json()["notebooks"]

        # Check if the created notebook is in the list
        assert any(notebook['id'] == notebook_id for notebook in listed_notebooks)

@pytest.mark.asyncio
async def test_add_source_to_notebook(override_dependencies):
    """Tests adding a source to a notebook."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new notebook
        notebook_name = f"My Test Notebook {uuid4()}"
        create_response = await client.post("/api/notebooks", json={"name": notebook_name})
        assert create_response.status_code == 201
        created_notebook = create_response.json()
        notebook_id = created_notebook["id"]

        # Add a source to the notebook
        source_url = "https://en.wikipedia.org/wiki/Walt_Disney"
        add_source_response = await client.post("/api/sources/url", json={"notebook_id": notebook_id, "url": source_url})
        assert add_source_response.status_code == 201
        added_source = add_source_response.json()
        assert added_source["notebook_id"] == notebook_id
        assert added_source["source_type"] == "url"
        assert added_source["url"] == source_url

        # Verify the source was added
        list_sources_response = await client.get(f"/api/sources/notebook/{notebook_id}")
        assert list_sources_response.status_code == 200
        listed_sources = list_sources_response.json()["sources"]
        assert any(source['id'] == added_source['id'] for source in listed_sources)

