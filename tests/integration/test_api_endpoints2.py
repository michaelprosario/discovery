"""Integration tests for API endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
import sys
from uuid import uuid4
import requests
sys.path.insert(0, '/workspaces/discovery')

from src.api.main import app
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository
from src.api.notebooks_router import get_notebook_repository

root_url = "http://localhost:8000"

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
    

