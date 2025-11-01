"""Integration tests for Sources API endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
import sys
import os
import tempfile
from uuid import uuid4, UUID
from typing import Dict, Any


from unittest.mock import patch


sys.path.insert(0, '/workspaces/discovery')

from src.api.main import app
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository
from src.infrastructure.repositories.in_memory_source_repository import InMemorySourceRepository
from src.core.interfaces.providers.i_web_fetch_provider import IWebFetchProvider, WebContent
from src.core.interfaces.providers.i_content_extraction_provider import IContentExtractionProvider
from src.core.interfaces.providers.i_file_storage_provider import IFileStorageProvider
from src.core.results.result import Result
from src.api.notebooks_router import get_notebook_repository
from src.api.sources_router import get_source_repository, get_web_fetch_provider, get_content_extraction_provider, get_file_storage_provider
from src.core.value_objects.enums import FileType

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

@pytest.fixture(scope="function")
def override_dependencies():
    """Override dependencies for testing."""
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

    app.dependency_overrides[get_notebook_repository] = _get_notebook_repo
    app.dependency_overrides[get_source_repository] = _get_source_repo
    app.dependency_overrides[get_web_fetch_provider] = _get_web_fetch_provider
    app.dependency_overrides[get_content_extraction_provider] = _get_content_extraction_provider
    app.dependency_overrides[get_file_storage_provider] = _get_file_storage_provider

    yield

    notebook_repo.clear()
    source_repo.clear()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("os.path.getsize", return_value=100)
async def test_import_file_source(mock_getsize, override_dependencies):
    """Test importing a file source."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a notebook
        create_notebook_response = await client.post(
            "/api/notebooks",
            json={"name": "Test Notebook for Sources"}
        )
        assert create_notebook_response.status_code == 201
        notebook_id = create_notebook_response.json()["id"]

        # 2. Create a temporary file and read its content
        file_content = b"This is a test file."
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        # 3. Encode the content in base64
        import base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')

        # 4. Import the file source
        import_response = await client.post(
            "/api/sources/file",
            json={
                "notebook_id": notebook_id,
                "name": "Test File Source",
                "file_content": encoded_content,
                "file_type": "txt"
            }
        )

        # 5. Assertions
        assert import_response.status_code == 201
        data = import_response.json()
        assert data["name"] == "Test File Source"
        assert data["notebook_id"] == notebook_id
        assert data["source_type"] == "file"
        assert data["file_type"] == "txt"
        assert "This is a test file." in data["extracted_text"]

        # Clean up the temporary file
        os.remove(tmp_file_path)