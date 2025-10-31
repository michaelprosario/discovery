"""FastAPI router for QA operations."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from ..core.services.qa_rag_service import QaRagService
from ..core.commands.qa_commands import AskQuestionCommand
from ..core.interfaces.providers.i_llm_provider import LlmGenerationParameters
from ..infrastructure.database.connection import get_db
from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository
from ..infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
from ..infrastructure.providers.gemini_llm_provider import GeminiLlmProvider
from .dtos import ErrorResponse
import os

router = APIRouter(prefix="/api/notebooks", tags=["qa-rag"])


# DTOs
class AskQuestionRequest(BaseModel):
    """Request to ask a question about notebook content."""
    question: str = Field(..., min_length=1, max_length=10000, description="Question to ask about the notebook content")
    max_sources: int = Field(default=5, ge=1, le=20, description="Maximum number of source chunks to retrieve")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="LLM temperature for response generation")
    max_tokens: int = Field(default=1500, ge=100, le=4000, description="Maximum tokens for LLM response")


class QaSourceItem(BaseModel):
    """Source information used in QA response."""
    text: str
    source_id: Optional[UUID]
    chunk_index: int
    relevance_score: float
    source_name: Optional[str] = None
    source_type: Optional[str] = None


class QaResponse(BaseModel):
    """Response from QA operation."""
    question: str
    answer: str
    sources: List[QaSourceItem]
    notebook_id: UUID
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None


class QaHealthResponse(BaseModel):
    """Health check response for QA service."""
    status: str
    llm_model: str
    vector_db_status: str


# Dependency injection functions
def get_notebook_repository(db = Depends(get_db)):
    return PostgresNotebookRepository(db)

def get_vector_db_provider():
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_key = os.getenv("WEAVIATE_KEY")
    return WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)

def get_llm_provider():
    return GeminiLlmProvider()

def get_qa_rag_service(
    notebook_repository = Depends(get_notebook_repository),
    vector_db_provider = Depends(get_vector_db_provider),
    llm_provider = Depends(get_llm_provider)
):
    return QaRagService(
        notebook_repository=notebook_repository,
        vector_db_provider=vector_db_provider,
        llm_provider=llm_provider
    )


def get_collection_name(notebook_id: UUID) -> str:
    """
    Helper to get collection name for a notebook.
    
    Weaviate collection names must:
    - Start with uppercase letter
    - Contain only alphanumeric characters (no hyphens, underscores, etc.)
    - Be a valid class name
    
    Args:
        notebook_id: UUID of the notebook
        
    Returns:
        Valid Weaviate collection name in format: Notebook{uuid_without_hyphens}
    """
    # Remove hyphens from UUID and ensure it starts with uppercase
    clean_uuid = str(notebook_id).replace("-", "")
    return f"Notebook{clean_uuid}"


# Endpoints
@router.post(
    "/{notebook_id}/qa",
    response_model=QaResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        400: {"model": ErrorResponse, "description": "Invalid question or parameters"},
        500: {"model": ErrorResponse, "description": "QA operation failed"}
    }
)
def ask_question(
    notebook_id: UUID,
    request: AskQuestionRequest,
    service: QaRagService = Depends(get_qa_rag_service)
):
    """
    Ask a question about notebook content using RAG (Retrieval-Augmented Generation).

    This endpoint:
    1. Searches for relevant content chunks in the notebook using vector similarity
    2. Uses an LLM to generate an answer based on the retrieved context
    3. Returns the answer with source citations

    Args:
        notebook_id: UUID of the notebook to ask about
        request: Question and parameters
        service: Injected QA RAG service

    Returns:
        QA response with answer and sources

    Raises:
        HTTPException: 404 if notebook not found, 400 for invalid input, 500 for operation failure
    """
    # Generate collection name for this notebook
    collection_name = get_collection_name(notebook_id)
    
    # Create LLM parameters
    llm_parameters = LlmGenerationParameters(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=0.9
    )

    # Create command
    command = AskQuestionCommand(
        notebook_id=notebook_id,
        question=request.question,
        max_sources=request.max_sources,
        collection_name=collection_name,
        llm_parameters=llm_parameters
    )

    # Execute QA operation
    result = service.ask_question(command)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        elif "empty" in result.error.lower() or "invalid" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": result.error}
            )

    qa_response = result.value

    # Convert to API response format
    return QaResponse(
        question=qa_response.question,
        answer=qa_response.answer,
        sources=[
            QaSourceItem(
                text=source.text,
                source_id=source.source_id,
                chunk_index=source.chunk_index,
                relevance_score=source.relevance_score,
                source_name=source.source_name,
                source_type=source.source_type
            )
            for source in qa_response.sources
        ],
        notebook_id=qa_response.notebook_id,
        confidence_score=qa_response.confidence_score,
        processing_time_ms=qa_response.processing_time_ms
    )


@router.get(
    "/qa/health",
    response_model=QaHealthResponse,
    responses={
        200: {"description": "QA service health status"}
    }
)
def get_qa_health(
    service: QaRagService = Depends(get_qa_rag_service)
):
    """
    Get health status of the QA service.

    Returns information about the LLM model, vector database connectivity,
    and overall service status.

    Args:
        service: Injected QA RAG service

    Returns:
        Health status information
    """
    try:
        # Get LLM model info
        model_info_result = service._llm_provider.get_model_info()
        llm_model = model_info_result.value.get("name", "unknown") if model_info_result.is_success else "error"
        
        # Check vector database (simple health check)
        vector_status = "connected"
        try:
            # Try a simple operation to check connectivity - just check if we can connect
            client = service._vector_db_provider._get_client()
            collections = client.collections.list_all()
            vector_status = "connected"
        except:
            vector_status = "disconnected"

        return QaHealthResponse(
            status="healthy",
            llm_model=llm_model,
            vector_db_status=vector_status
        )

    except Exception as e:
        return QaHealthResponse(
            status="unhealthy",
            llm_model="error",
            vector_db_status="error"
        )