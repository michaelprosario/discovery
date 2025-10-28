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
