#!/usr/bin/env python3
"""Test script to reproduce and test the notebook deletion bug."""

import asyncio
import sys
import os
sys.path.insert(0, '/workspaces/discovery')

from httpx import AsyncClient, ASGITransport
from src.api.main import app

# Set up mock dependencies
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository
from src.infrastructure.repositories.in_memory_source_repository import InMemorySourceRepository
from src.core.interfaces.providers.i_web_fetch_provider import IWebFetchProvider, WebContent
from src.core.interfaces.providers.i_content_extraction_provider import IContentExtractionProvider
from src.core.interfaces.providers.i_file_storage_provider import IFileStorageProvider
from src.core.results.result import Result
from src.api.notebooks_router import get_notebook_repository
from src.api.sources_router import get_source_repository, get_web_fetch_provider, get_content_extraction_provider, get_file_storage_provider

# Mock Providers
class MockWebFetchProvider(IWebFetchProvider):
    def fetch_url(self, url: str, timeout: int = 30) -> Result['WebContent']:
        return Result.success(WebContent(url=url, title=f"Title for {url}", html="", text=f"Content from {url}", metadata={}))

    def validate_url(self, url: str) -> Result[bool]:
        return Result.success(True)

    def extract_main_content(self, html: str) -> Result[str]:
        return Result.success(html)

class MockContentExtractionProvider(IContentExtractionProvider):
    def extract_text_from_pdf(self, file_path: str) -> Result[str]:
        return Result.success(f"Extracted text from PDF: {file_path}")

    def extract_text_from_docx(self, file_path: str) -> Result[str]:
        return Result.success(f"Extracted text from DOCX: {file_path}")

    def extract_text_from_doc(self, file_path: str) -> Result[str]:
        return Result.success(f"Extracted text from DOC: {file_path}")

    def extract_text_from_txt(self, file_path: str) -> Result[str]:
        return Result.success("This is a test file.")

    def extract_text_from_markdown(self, file_path: str) -> Result[str]:
        return Result.success("This is a test file.")

class MockFileStorageProvider(IFileStorageProvider):
    def store_file(self, content: bytes, destination: str) -> Result[str]:
        return Result.success(destination)

    def retrieve_file(self, path: str) -> Result[bytes]:
        return Result.success(b"file content")

    def delete_file(self, path: str) -> Result[None]:
        return Result.success(None)

    def get_file_size(self, path: str) -> Result[int]:
        return Result.success(100)

    def file_exists(self, path: str) -> Result[bool]:
        return Result.success(True)

def setup_test_dependencies():
    """Set up test dependencies."""
    notebook_repo = InMemoryNotebookRepository()
    source_repo = InMemorySourceRepository()
    web_fetch_provider = MockWebFetchProvider()
    content_extraction_provider = MockContentExtractionProvider()
    file_storage_provider = MockFileStorageProvider()

    def _get_notebook_repo():
        yield notebook_repo

    def _get_source_repo():
        yield source_repo

    def _get_web_fetch_provider():
        return web_fetch_provider

    def _get_content_extraction_provider():
        return content_extraction_provider

    def _get_file_storage_provider():
        return file_storage_provider

    # Override dependencies
    app.dependency_overrides[get_notebook_repository] = _get_notebook_repo
    app.dependency_overrides[get_source_repository] = _get_source_repo
    app.dependency_overrides[get_web_fetch_provider] = _get_web_fetch_provider
    app.dependency_overrides[get_content_extraction_provider] = _get_content_extraction_provider
    app.dependency_overrides[get_file_storage_provider] = _get_file_storage_provider

async def test_delete_notebook_with_sources():
    """Test deleting a notebook that has sources."""
    
    # Set up dependencies
    setup_test_dependencies()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new notebook
        notebook_name = "Test Notebook for Deletion"
        create_response = await client.post("/api/notebooks", json={"name": notebook_name})
        assert create_response.status_code == 201
        created_notebook = create_response.json()
        notebook_id = created_notebook["id"]
        print(f"Created notebook: {notebook_id}")

        # Add a source to the notebook
        source_url = "https://en.wikipedia.org/wiki/Walt_Disney"
        add_source_response = await client.post("/api/sources/url", json={"notebook_id": notebook_id, "url": source_url})
        if add_source_response.status_code != 201:
            print(f"Failed to add source: {add_source_response.status_code}")
            print(f"Response: {add_source_response.text}")
            return False
        
        added_source = add_source_response.json()
        print(f"Added source: {added_source['id']}")

        # Verify the source was added
        list_sources_response = await client.get(f"/api/sources/notebook/{notebook_id}")
        assert list_sources_response.status_code == 200
        listed_sources = list_sources_response.json()["sources"]
        assert len(listed_sources) == 1
        print(f"Verified source count: {len(listed_sources)}")

        # Now try to delete the notebook with cascade=True
        print("Attempting to delete notebook with cascade=True...")
        delete_response = await client.delete(f"/api/notebooks/{notebook_id}?cascade=true")
        
        if delete_response.status_code != 204:
            print(f"DELETE FAILED: {delete_response.status_code}")
            print(f"Response: {delete_response.text}")
            return False
        
        print("Delete successful!")

        # Verify the notebook is deleted
        get_response = await client.get(f"/api/notebooks/{notebook_id}")
        assert get_response.status_code == 404
        print("Confirmed notebook is deleted")

        return True

if __name__ == "__main__":
    success = asyncio.run(test_delete_notebook_with_sources())
    if success:
        print("✅ Test passed! Notebook deletion with sources works correctly.")
    else:
        print("❌ Test failed! There's still an issue with notebook deletion.")
        sys.exit(1)