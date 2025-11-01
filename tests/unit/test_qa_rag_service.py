"""Unit tests for QaRagService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import Mock, patch

from src.core.services.qa_rag_service import QaRagService
from src.core.commands.qa_commands import AskQuestionCommand, GenerateAnswerCommand
from src.core.queries.qa_queries import QaResponse, QaSource
from src.core.interfaces.providers.i_llm_provider import LlmGenerationParameters
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
    mock = Mock()
    # Default successful similarity search response
    mock.query_similarity.return_value = Result.success([
        {
            "text": "This is relevant content about machine learning.",
            "metadata": {
                "source_id": "123e4567-e89b-12d3-a456-426614174000",
                "chunk_index": 0,
                "source_name": "ML Guide",
                "source_type": "document"
            },
            "certainty": 0.85
        },
        {
            "text": "Machine learning algorithms can be categorized into supervised and unsupervised learning.",
            "metadata": {
                "source_id": "123e4567-e89b-12d3-a456-426614174001",
                "chunk_index": 1,
                "source_name": "ML Basics",
                "source_type": "article"
            },
            "certainty": 0.78
        }
    ])
    return mock


@pytest.fixture
def llm_provider():
    """Mock LLM provider."""
    mock = Mock()
    # Default successful generation response
    mock.generate.return_value = Result.success(
        "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. [1][2]"
    )
    mock.get_model_info.return_value = Result.success({
        "name": "gemini-2.0-flash-001",
        "provider": "google_gemini"
    })
    return mock


@pytest.fixture
def service(notebook_repository, vector_db_provider, llm_provider):
    """Fixture to provide a service instance with dependencies."""
    return QaRagService(
        notebook_repository=notebook_repository,
        vector_db_provider=vector_db_provider,
        llm_provider=llm_provider
    )


@pytest.fixture
def test_notebook(notebook_repository):
    """Create a test notebook."""
    notebook = Notebook(
        id=uuid4(),
        name="Machine Learning Notes",
        description="Notes about ML concepts",
        tags=["ml", "ai"]
    )
    result = notebook_repository.add(notebook)
    assert result.is_success
    return notebook


class TestAskQuestion:
    """Tests for asking questions using RAG."""

    def test_ask_question_success(self, service, test_notebook, vector_db_provider, llm_provider):
        """Test successful question answering."""
        command = AskQuestionCommand(
            notebook_id=test_notebook.id,
            question="What is machine learning?",
            max_sources=5
        )

        result = service.ask_question(command)

        assert result.is_success
        response = result.value
        assert isinstance(response, QaResponse)
        assert response.question == "What is machine learning?"
        assert "machine learning" in response.answer.lower()
        assert len(response.sources) == 2
        assert response.notebook_id == test_notebook.id
        assert response.confidence_score is not None
        assert response.processing_time_ms is not None

        # Verify vector search was called correctly
        vector_db_provider.query_similarity.assert_called_once()
        call_args = vector_db_provider.query_similarity.call_args
        assert call_args[1]["query_text"] == "What is machine learning?"
        assert call_args[1]["limit"] == 5
        assert call_args[1]["filters"]["notebook_id"] == str(test_notebook.id)

        # Verify LLM was called
        llm_provider.generate.assert_called_once()

    def test_ask_question_notebook_not_found(self, service, vector_db_provider, llm_provider):
        """Test question asking when notebook doesn't exist."""
        non_existent_id = uuid4()
        command = AskQuestionCommand(
            notebook_id=non_existent_id,
            question="What is machine learning?"
        )

        result = service.ask_question(command)

        assert result.is_failure
        assert "not found" in result.error.lower()

    def test_ask_question_no_search_results(self, service, test_notebook, vector_db_provider, llm_provider):
        """Test question asking when no relevant content is found."""
        vector_db_provider.query_similarity.return_value = Result.success([])

        command = AskQuestionCommand(
            notebook_id=test_notebook.id,
            question="What is machine learning?"
        )

        result = service.ask_question(command)

        assert result.is_failure
        assert "no relevant content found" in result.error.lower()

    def test_ask_question_vector_search_failure(self, service, test_notebook, vector_db_provider, llm_provider):
        """Test question asking when vector search fails."""
        vector_db_provider.query_similarity.return_value = Result.failure("Vector DB error")

        command = AskQuestionCommand(
            notebook_id=test_notebook.id,
            question="What is machine learning?"
        )

        result = service.ask_question(command)

        assert result.is_failure
        assert "failed to search for relevant content" in result.error.lower()

    def test_ask_question_llm_failure(self, service, test_notebook, vector_db_provider, llm_provider):
        """Test question asking when LLM generation fails."""
        llm_provider.generate.return_value = Result.failure("LLM error")

        command = AskQuestionCommand(
            notebook_id=test_notebook.id,
            question="What is machine learning?"
        )

        result = service.ask_question(command)

        assert result.is_failure
        assert "failed to generate answer" in result.error.lower()

    def test_ask_question_with_custom_parameters(self, service, test_notebook, vector_db_provider, llm_provider):
        """Test question asking with custom LLM parameters."""
        custom_params = LlmGenerationParameters(
            temperature=0.5,
            max_tokens=2000,
            top_p=0.8
        )

        command = AskQuestionCommand(
            notebook_id=test_notebook.id,
            question="What is machine learning?",
            max_sources=3,
            llm_parameters=custom_params
        )

        result = service.ask_question(command)

        assert result.is_success

        # Verify custom parameters were passed to LLM
        llm_call_args = llm_provider.generate.call_args
        llm_params = llm_call_args[0][1]  # Second argument (parameters)
        assert llm_params.temperature == 0.5
        assert llm_params.max_tokens == 2000
        assert llm_params.top_p == 0.8


class TestGenerateAnswer:
    """Tests for answer generation."""

    def test_generate_answer_success(self, service, llm_provider):
        """Test successful answer generation."""
        command = GenerateAnswerCommand(
            question="What is machine learning?",
            context_chunks=["Machine learning is AI", "ML uses algorithms"],
            notebook_id=uuid4()
        )

        result = service._generate_answer(command)

        assert result.is_success
        assert "machine learning" in result.value.lower()

        # Verify LLM was called with proper prompt
        llm_provider.generate.assert_called_once()
        call_args = llm_provider.generate.call_args
        prompt = call_args[0][0]
        assert "machine learning" in prompt.lower()
        assert "context:" in prompt.lower()
        assert "ML uses algorithms" in prompt

    def test_generate_answer_with_citations(self, service, llm_provider):
        """Test answer generation includes citation instructions."""
        command = GenerateAnswerCommand(
            question="What is machine learning?",
            context_chunks=["ML definition", "ML types"],
            notebook_id=uuid4(),
            include_citations=True
        )

        result = service._generate_answer(command)

        assert result.is_success

        # Check that citation instructions were included in prompt
        call_args = llm_provider.generate.call_args
        prompt = call_args[0][0]
        assert "cite the source" in prompt.lower() or "citation" in prompt.lower()

    def test_generate_answer_without_citations(self, service, llm_provider):
        """Test answer generation without citation instructions."""
        command = GenerateAnswerCommand(
            question="What is machine learning?",
            context_chunks=["ML definition", "ML types"],
            notebook_id=uuid4(),
            include_citations=False
        )

        result = service._generate_answer(command)

        assert result.is_success

        # Check that citation instructions were not included
        call_args = llm_provider.generate.call_args
        prompt = call_args[0][0]
        assert "cite the source" not in prompt.lower()


class TestConfidenceScoreCalculation:
    """Tests for confidence score calculation."""

    def test_calculate_confidence_score_empty_sources(self, service):
        """Test confidence score calculation with no sources."""
        score = service._calculate_confidence_score([])
        assert score == 0.0

    def test_calculate_confidence_score_single_source(self, service):
        """Test confidence score calculation with one source."""
        sources = [
            QaSource(
                text="Test content",
                source_id=uuid4(),
                chunk_index=0,
                relevance_score=0.8
            )
        ]
        score = service._calculate_confidence_score(sources)
        assert 0.0 <= score <= 1.0

    def test_calculate_confidence_score_multiple_sources(self, service):
        """Test confidence score calculation with multiple sources."""
        sources = [
            QaSource(text="Content 1", source_id=uuid4(), chunk_index=0, relevance_score=0.9),
            QaSource(text="Content 2", source_id=uuid4(), chunk_index=1, relevance_score=0.8),
            QaSource(text="Content 3", source_id=uuid4(), chunk_index=2, relevance_score=0.7)
        ]
        score = service._calculate_confidence_score(sources)
        assert 0.0 <= score <= 1.0
        # More sources should generally give higher confidence
        assert score > 0.5


class TestBuildRagPrompt:
    """Tests for RAG prompt building."""

    def test_build_rag_prompt_with_citations(self, service):
        """Test building RAG prompt with citation instructions."""
        question = "What is machine learning?"
        context_chunks = ["ML is AI subset", "ML uses algorithms"]
        
        prompt = service._build_rag_prompt(question, context_chunks, include_citations=True)
        
        assert "What is machine learning?" in prompt
        assert "[1] ML is AI subset" in prompt
        assert "[2] ML uses algorithms" in prompt
        assert "cite the source" in prompt.lower() or "citation" in prompt.lower()

    def test_build_rag_prompt_without_citations(self, service):
        """Test building RAG prompt without citation instructions."""
        question = "What is machine learning?"
        context_chunks = ["ML is AI subset", "ML uses algorithms"]
        
        prompt = service._build_rag_prompt(question, context_chunks, include_citations=False)
        
        assert "What is machine learning?" in prompt
        assert "[1] ML is AI subset" in prompt
        assert "[2] ML uses algorithms" in prompt
        assert "cite the source" not in prompt.lower()

    def test_build_rag_prompt_empty_context(self, service):
        """Test building RAG prompt with empty context."""
        question = "What is machine learning?"
        context_chunks = []
        
        prompt = service._build_rag_prompt(question, context_chunks)
        
        assert "What is machine learning?" in prompt
        assert "Context:" in prompt