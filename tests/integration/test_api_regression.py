"""Regression tests for API endpoints."""
import pytest
from uuid import uuid4
import requests

root_url = "http://localhost:8000"

def test_create_and_get_notebook():
    """Tests creating a notebook and then fetching it."""
    # Create a new notebook
    notebook_name = f"My Test Notebook {uuid4()}"
    response = requests.post(f"{root_url}/api/notebooks", json={"name": notebook_name})
    assert response.status_code == 201
    created_notebook = response.json()
    assert created_notebook["name"] == notebook_name

    # Get the notebook
    notebook_id = created_notebook["id"]
    response = requests.get(f"{root_url}/api/notebooks/{notebook_id}")
    assert response.status_code == 200
    fetched_notebook = response.json()
    assert fetched_notebook["name"] == notebook_name
    assert fetched_notebook["id"] == notebook_id

    

@pytest.mark.asyncio
async def test_root_endpoint():    
    # make http request to root endpoint
    response = requests.get(root_url)
    
    # Assert status code
    assert response.status_code == 200

    # Assert response content
    data = response.json()
    
    assert "message" in data
    assert data["message"] == "Discovery API"


def test_list_notebooks_after_creation():
    """Tests that a newly created notebook appears in the list of notebooks."""
    # Create a new notebook
    notebook_name = f"My Test Notebook {uuid4()}"
    create_response = requests.post(f"{root_url}/api/notebooks", json={"name": notebook_name})
    assert create_response.status_code == 201
    created_notebook = create_response.json()
    notebook_id = created_notebook["id"]

    # List notebooks
    list_response = requests.get(f"{root_url}/api/notebooks")
    assert list_response.status_code == 200
    listed_notebooks = list_response.json()["notebooks"]

    # Check if the created notebook is in the list
    assert any(notebook['id'] == notebook_id for notebook in listed_notebooks)

def test_add_source_to_notebook():
    """Tests adding a source to a notebook."""
    # Create a new notebook
    notebook_name = f"My Test Notebook {uuid4()}"
    create_response = requests.post(f"{root_url}/api/notebooks", json={"name": notebook_name})
    assert create_response.status_code == 201
    created_notebook = create_response.json()
    notebook_id = created_notebook["id"]

    # Add a source to the notebook
    source_url = "https://en.wikipedia.org/wiki/Walt_Disney"
    add_source_response = requests.post(f"{root_url}/api/sources/url", json={"notebook_id": notebook_id, "url": source_url})
    assert add_source_response.status_code == 201
    added_source = add_source_response.json()
    assert added_source["notebook_id"] == notebook_id
    assert added_source["source_type"] == "url"
    assert added_source["url"] == source_url

    # Verify the source was added
    list_sources_response = requests.get(f"{root_url}/api/sources/notebook/{notebook_id}")
    assert list_sources_response.status_code == 200
    listed_sources = list_sources_response.json()["sources"]
    assert any(source['id'] == added_source['id'] for source in listed_sources)

