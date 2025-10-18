"""Unit tests for ContentSimilarityService."""
import pytest
from uuid import uuid4
from unittest.mock import Mock

from src.core.services.content_similarity_service import ContentSimilarityService
from src.core.queries.vector_queries import (
    SimilaritySearchQuery,
    GetVectorCountQuery
)
from src.core.entities.notebook import Notebook
from src.core.results.result import Result
from src.infrastructure.repositories.in_memory_notebook_repository import InMemoryNotebookRepository


@pytest.fixture
def notebook_repository():
    """Fixture to provide a fresh notebook repository."""
    return InMemoryNotebookRepository()


@pytest.fixture
def vector_db_provider():
    """Mock vector database provider."""
    provider = Mock()

    # Mock similarity search results with valid UUIDs
    source_id_1 = str(uuid4())
    source_id_2 = str(uuid4())
    mock_results = [
        {
            "id": "doc1",
            "text": "This is relevant content about the topic.",
            "metadata": {
                "notebook_id": str(uuid4()),
                "source_id": source_id_1,
                "chunk_index": 0
            },
            "distance": 0.15,
            "certainty": 0.85
        },
        {
            "id": "doc2",
            "text": "Another relevant piece of content.",
            "metadata": {
                "notebook_id": str(uuid4()),
                "source_id": source_id_2,
                "chunk_index": 1
            },
            "distance": 0.25,
            "certainty": 0.75
        }
    ]
    provider.query_similarity.return_value = Result.success(mock_results)
    provider.get_document_count.return_value = Result.success(42)

    return provider


@pytest.fixture
def service(notebook_repository, vector_db_provider):
    """Fixture to provide a service instance with dependencies."""
    return ContentSimilarityService(
        notebook_repository=notebook_repository,
        vector_db_provider=vector_db_provider
    )


@pytest.fixture
def test_notebook(notebook_repository):
    """Create a test notebook."""
    notebook = Notebook.create(name="Test Notebook", description="For testing").value
    notebook_repository.add(notebook)
    return notebook


class TestSearchSimilarContent:
    """Tests for similarity search."""

    def test_search_similar_content_success(self, service, test_notebook, vector_db_provider):
        """Test successful similarity search."""
        query = SimilaritySearchQuery(
            notebook_id=test_notebook.id,
            query_text="test query",
            collection_name="test_collection",
            limit=10
        )

        result = service.search_similar_content(query)

        assert result.is_success
        assert len(result.value) == 2

        # Verify first result
        first_result = result.value[0]
        assert first_result.text == "This is relevant content about the topic."
        assert first_result.chunk_index == 0
        assert first_result.distance == 0.15
        assert first_result.certainty == 0.85

        # Verify vector db was called with correct parameters
        vector_db_provider.query_similarity.assert_called_once_with(
            collection_name="test_collection",
            query_text="test query",
            limit=10,
            filters={"notebook_id": str(test_notebook.id)}
        )

    def test_search_similar_content_notebook_not_found(self, service):
        """Test search fails when notebook doesn't exist."""
        query = SimilaritySearchQuery(
            notebook_id=uuid4(),
            query_text="test query"
        )

        result = service.search_similar_content(query)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_search_similar_content_empty_results(self, service, test_notebook, vector_db_provider):
        """Test search with no matching results."""
        vector_db_provider.query_similarity.return_value = Result.success([])

        query = SimilaritySearchQuery(
            notebook_id=test_notebook.id,
            query_text="test query"
        )

        result = service.search_similar_content(query)

        assert result.is_success
        assert len(result.value) == 0

    def test_search_similar_content_vector_db_failure(self, service, test_notebook, vector_db_provider):
        """Test search fails when vector database query fails."""
        vector_db_provider.query_similarity.return_value = Result.failure("Vector DB error")

        query = SimilaritySearchQuery(
            notebook_id=test_notebook.id,
            query_text="test query"
        )

        result = service.search_similar_content(query)

        assert result.is_failure
        assert "similar content" in result.error.lower()

    def test_search_similar_content_custom_limit(self, service, test_notebook, vector_db_provider):
        """Test search with custom limit."""
        query = SimilaritySearchQuery(
            notebook_id=test_notebook.id,
            query_text="test query",
            limit=5
        )

        result = service.search_similar_content(query)

        assert result.is_success

        # Verify limit was passed to vector db
        call_args = vector_db_provider.query_similarity.call_args
        assert call_args[1]["limit"] == 5

    def test_search_similar_content_result_parsing(self, service, test_notebook, vector_db_provider):
        """Test that results are properly parsed into domain objects."""
        # Mock result with source_id as string UUID
        test_source_id = uuid4()
        mock_results = [
            {
                "id": "doc1",
                "text": "Test content",
                "metadata": {
                    "notebook_id": str(test_notebook.id),
                    "source_id": str(test_source_id),
                    "chunk_index": 5,
                    "source_name": "Test Source"
                },
                "distance": 0.1,
                "certainty": 0.9
            }
        ]
        vector_db_provider.query_similarity.return_value = Result.success(mock_results)

        query = SimilaritySearchQuery(
            notebook_id=test_notebook.id,
            query_text="test query"
        )

        result = service.search_similar_content(query)

        assert result.is_success
        assert len(result.value) == 1

        parsed_result = result.value[0]
        assert parsed_result.text == "Test content"
        assert parsed_result.source_id == test_source_id
        assert parsed_result.chunk_index == 5
        assert parsed_result.distance == 0.1
        assert parsed_result.certainty == 0.9
        assert "source_name" in parsed_result.metadata


class TestGetVectorCount:
    """Tests for getting vector count."""

    def test_get_vector_count_success(self, service, test_notebook, vector_db_provider):
        """Test successful vector count retrieval."""
        query = GetVectorCountQuery(
            notebook_id=test_notebook.id,
            collection_name="test_collection"
        )

        result = service.get_vector_count(query)

        assert result.is_success
        assert result.value == 42

        # Verify vector db was called correctly
        vector_db_provider.get_document_count.assert_called_once_with(
            collection_name="test_collection",
            filters={"notebook_id": str(test_notebook.id)}
        )

    def test_get_vector_count_notebook_not_found(self, service):
        """Test count fails when notebook doesn't exist."""
        query = GetVectorCountQuery(
            notebook_id=uuid4()
        )

        result = service.get_vector_count(query)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_get_vector_count_vector_db_failure(self, service, test_notebook, vector_db_provider):
        """Test count fails when vector database query fails."""
        vector_db_provider.get_document_count.return_value = Result.failure("Vector DB error")

        query = GetVectorCountQuery(
            notebook_id=test_notebook.id
        )

        result = service.get_vector_count(query)

        assert result.is_failure
        assert "count" in result.error.lower()

    def test_get_vector_count_zero(self, service, test_notebook, vector_db_provider):
        """Test count returns zero when no vectors exist."""
        vector_db_provider.get_document_count.return_value = Result.success(0)

        query = GetVectorCountQuery(
            notebook_id=test_notebook.id
        )

        result = service.get_vector_count(query)

        assert result.is_success
        assert result.value == 0
