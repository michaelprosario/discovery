"""Unit tests for VectorIngestionService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock

from src.core.services.vector_ingestion_service import VectorIngestionService
from src.core.commands.vector_commands import (
    IngestNotebookCommand,
    DeleteNotebookVectorsCommand
)
from src.core.entities.notebook import Notebook
from src.core.entities.source import Source
from src.core.value_objects.enums import SourceType
from src.core.results.result import Result
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository
from src.infrastructure.repositories.in_memory_source_repository import InMemorySourceRepository


@pytest.fixture
def notebook_repository():
    """Fixture to provide a fresh notebook repository."""
    return InMemoryNotebookRepository()


@pytest.fixture
def source_repository():
    """Fixture to provide a fresh source repository."""
    return InMemorySourceRepository()


@pytest.fixture
def vector_db_provider():
    """Mock vector database provider."""
    provider = Mock()
    provider.create_collection_if_not_exists.return_value = Result.success(None)
    provider.upsert_documents.return_value = Result.success(["doc1", "doc2", "doc3"])
    provider.delete_documents.return_value = Result.success(5)
    return provider


@pytest.fixture
def content_segmenter():
    """Mock content segmenter."""
    segmenter = Mock()
    segmenter.segment.return_value = Result.success([
        "This is chunk 1 of the content.",
        "This is chunk 2 of the content.",
        "This is chunk 3 of the content."
    ])
    return segmenter


@pytest.fixture
def service(notebook_repository, source_repository, vector_db_provider, content_segmenter):
    """Fixture to provide a service instance with dependencies."""
    return VectorIngestionService(
        notebook_repository=notebook_repository,
        source_repository=source_repository,
        vector_db_provider=vector_db_provider,
        content_segmenter=content_segmenter
    )


@pytest.fixture
def test_notebook(notebook_repository):
    """Create a test notebook."""
    notebook = Notebook.create(name="Test Notebook", description="For testing").value
    notebook_repository.add(notebook)
    return notebook


@pytest.fixture
def test_source(test_notebook, source_repository):
    """Create a test source with extracted text."""
    source_result = Source.create_url_source(
        notebook_id=test_notebook.id,
        name="Test Source",
        url="https://example.com",
        content="Sample content for testing"
    )
    source = source_result.value
    source.extracted_text = "This is some extracted text content that will be segmented and ingested into the vector database."
    source_repository.add(source)
    return source


class TestIngestNotebook:
    """Tests for ingesting notebook into vector database."""

    def test_ingest_notebook_success(self, service, test_notebook, test_source, vector_db_provider, content_segmenter):
        """Test successful notebook ingestion."""
        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection",
            chunk_size=1000,
            overlap=200
        )

        result = service.ingest_notebook(command)

        assert result.is_success
        assert result.value == 3  # 3 chunks from mock segmenter

        # Verify collection was created
        vector_db_provider.create_collection_if_not_exists.assert_called_once_with("test_collection")

        # Verify segmenter was called
        content_segmenter.segment.assert_called_once()

        # Verify documents were upserted
        vector_db_provider.upsert_documents.assert_called_once()
        call_args = vector_db_provider.upsert_documents.call_args
        assert call_args[0][0] == "test_collection"
        documents = call_args[0][1]
        assert len(documents) == 3
        assert all("text" in doc for doc in documents)
        assert all("metadata" in doc for doc in documents)
        assert documents[0]["metadata"]["notebook_id"] == str(test_notebook.id)
        assert documents[0]["metadata"]["source_id"] == str(test_source.id)

    def test_ingest_notebook_not_found(self, service):
        """Test ingesting non-existent notebook fails."""
        command = IngestNotebookCommand(
            notebook_id=uuid4(),
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_ingest_notebook_no_sources(self, service, test_notebook, vector_db_provider):
        """Test ingesting notebook with no sources."""
        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        assert result.is_success
        assert result.value == 0  # No chunks ingested

        # Collection should still be created
        vector_db_provider.create_collection_if_not_exists.assert_called_once()

    def test_ingest_notebook_source_without_text(self, service, test_notebook, source_repository, vector_db_provider):
        """Test ingesting source without extracted text is skipped."""
        # Create source without extracted text
        source_result = Source.create_url_source(
            notebook_id=test_notebook.id,
            name="Empty Source",
            url="https://example.com",
            content="content"
        )
        source = source_result.value
        source.extracted_text = ""  # No text
        source_repository.add(source)

        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        assert result.is_success
        assert result.value == 0  # No chunks because source has no text

    def test_ingest_notebook_force_reingest(self, service, test_notebook, test_source, vector_db_provider):
        """Test force reingestion deletes existing vectors."""
        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection",
            force_reingest=True
        )

        result = service.ingest_notebook(command)

        assert result.is_success

        # Verify existing vectors were deleted
        vector_db_provider.delete_documents.assert_called_once_with(
            "test_collection",
            {"notebook_id": str(test_notebook.id)}
        )

    def test_ingest_notebook_collection_creation_fails(self, service, test_notebook, vector_db_provider):
        """Test ingestion fails when collection creation fails."""
        vector_db_provider.create_collection_if_not_exists.return_value = Result.failure("Collection creation failed")

        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        assert result.is_failure
        assert "collection" in result.error.lower()

    def test_ingest_notebook_segmentation_fails(self, service, test_notebook, test_source, content_segmenter):
        """Test ingestion continues when segmentation fails for a source."""
        content_segmenter.segment.return_value = Result.failure("Segmentation failed")

        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        # Should succeed but with 0 chunks (failed source is skipped)
        assert result.is_success
        assert result.value == 0

    def test_ingest_notebook_upsert_fails(self, service, test_notebook, test_source, vector_db_provider):
        """Test ingestion fails when upsert fails."""
        vector_db_provider.upsert_documents.return_value = Result.failure("Upsert failed")

        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        assert result.is_failure
        assert "upsert" in result.error.lower()

    def test_ingest_notebook_multiple_sources(self, service, test_notebook, source_repository, content_segmenter):
        """Test ingesting notebook with multiple sources."""
        # Create multiple sources
        for i in range(3):
            source_result = Source.create_url_source(
                notebook_id=test_notebook.id,
                name=f"Source {i}",
                url=f"https://example.com/{i}",
                content=f"content{i}"
            )
            source = source_result.value
            source.extracted_text = f"Text content for source {i}"
            source_repository.add(source)

        command = IngestNotebookCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.ingest_notebook(command)

        assert result.is_success
        # 3 sources × 3 chunks each = 9 total chunks
        assert result.value == 9

        # Verify segmenter was called 3 times
        assert content_segmenter.segment.call_count == 3


class TestDeleteNotebookVectors:
    """Tests for deleting notebook vectors."""

    def test_delete_notebook_vectors_success(self, service, test_notebook, vector_db_provider):
        """Test successful deletion of notebook vectors."""
        command = DeleteNotebookVectorsCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.delete_notebook_vectors(command)

        assert result.is_success
        assert result.value == 5  # From mock return value

        # Verify delete was called with correct parameters
        vector_db_provider.delete_documents.assert_called_once_with(
            "test_collection",
            {"notebook_id": str(test_notebook.id)}
        )

    def test_delete_notebook_vectors_notebook_not_found(self, service):
        """Test deleting vectors for non-existent notebook fails."""
        command = DeleteNotebookVectorsCommand(
            notebook_id=uuid4(),
            collection_name="test_collection"
        )

        result = service.delete_notebook_vectors(command)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_delete_notebook_vectors_delete_fails(self, service, test_notebook, vector_db_provider):
        """Test deletion fails when vector db delete fails."""
        vector_db_provider.delete_documents.return_value = Result.failure("Delete failed")

        command = DeleteNotebookVectorsCommand(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.delete_notebook_vectors(command)

        assert result.is_failure
        assert "delete" in result.error.lower()
