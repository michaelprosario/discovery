"""FastAPI router for Vector Search operations."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from ..core.services.vector_ingestion_service import VectorIngestionService
from ..core.services.content_similarity_service import ContentSimilarityService
from ..core.commands.vector_commands import (
    IngestNotebookCommand,
    DeleteNotebookVectorsCommand
)
from ..core.queries.vector_queries import (
    SimilaritySearchQuery,
    GetVectorCountQuery
)
from .dtos import ErrorResponse

router = APIRouter(prefix="/api/notebooks", tags=["vector-search"])

# make sure to read .env file 
from dotenv import load_dotenv
load_dotenv()



# DTOs
class IngestNotebookRequest(BaseModel):
    """Request to ingest notebook into vector database."""
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    overlap: int = Field(default=200, ge=0, le=1000)
    force_reingest: bool = Field(default=False)


class IngestNotebookResponse(BaseModel):
    """Response from notebook ingestion."""
    notebook_id: UUID
    chunks_ingested: int
    message: str


class SimilaritySearchRequest(BaseModel):
    """Request for similarity search."""
    query: str = Field(..., min_length=1, max_length=10000)
    limit: int = Field(default=10, ge=1, le=100)


class SimilaritySearchResultItem(BaseModel):
    """Single result from similarity search."""
    text: str
    source_id: Optional[UUID]
    chunk_index: int
    distance: Optional[float]
    certainty: Optional[float]
    source_name: Optional[str] = None


class SimilaritySearchResponse(BaseModel):
    """Response from similarity search."""
    query: str
    results: List[SimilaritySearchResultItem]
    total: int


class VectorCountResponse(BaseModel):
    """Response for vector count."""
    notebook_id: UUID
    vector_count: int


# Dependency injection
def get_vector_ingestion_service() -> VectorIngestionService:
    """
    Dependency injection for VectorIngestionService.

    Creates service with required dependencies.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository
    from ..infrastructure.repositories.postgres_source_repository import PostgresSourceRepository
    from ..infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
    from ..infrastructure.providers.simple_content_segmenter import SimpleContentSegmenter
    import os

    # Get database session
    db = next(get_db())

    # Create repositories
    notebook_repository = PostgresNotebookRepository(db)
    source_repository = PostgresSourceRepository(db)

    # Create providers
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_key = os.getenv("WEAVIATE_KEY")
    vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)
    content_segmenter = SimpleContentSegmenter()

    # Create and return service
    service = VectorIngestionService(
        notebook_repository=notebook_repository,
        source_repository=source_repository,
        vector_db_provider=vector_db_provider,
        content_segmenter=content_segmenter
    )

    try:
        yield service
    finally:
        vector_db_provider.close()
        db.close()


def get_content_similarity_service() -> ContentSimilarityService:
    """
    Dependency injection for ContentSimilarityService.

    Creates service with required dependencies.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository
    from ..infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
    import os

    # Get database session
    db = next(get_db())

    # Create repository
    notebook_repository = PostgresNotebookRepository(db)

    # Create provider
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_key = os.getenv("WEAVIATE_KEY")
    vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)

    # Create and return service
    service = ContentSimilarityService(
        notebook_repository=notebook_repository,
        vector_db_provider=vector_db_provider
    )

    try:
        yield service
    finally:
        vector_db_provider.close()
        db.close()

def get_collection_name(notebook_id: UUID) -> str:
    """Helper to get collection name for a notebook."""
    return "notebook" + str(notebook_id)

# Endpoints
@router.post(
    "/{notebook_id}/ingest",
    response_model=IngestNotebookResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        500: {"model": ErrorResponse, "description": "Ingestion failed"}
    }
)
def ingest_notebook(
    notebook_id: UUID,
    request: IngestNotebookRequest = IngestNotebookRequest(),
    service: VectorIngestionService = Depends(get_vector_ingestion_service)
):
    """
    Ingest a notebook and its sources into the vector database.

    This endpoint segments the content of all sources in the notebook into chunks
    and stores them with embeddings in the vector database for similarity search.

    Args:
        notebook_id: UUID of the notebook to ingest
        request: Ingestion parameters (chunk size, overlap, force reingest)
        service: Injected vector ingestion service

    Returns:
        Ingestion result with count of chunks created

    Raises:
        HTTPException: 404 if notebook not found, 500 if ingestion fails
    """
    collection_name = get_collection_name(notebook_id)
    command = IngestNotebookCommand(
        notebook_id=notebook_id,
        collection_name=collection_name,
        chunk_size=request.chunk_size,
        overlap=request.overlap,
        force_reingest=request.force_reingest
    )

    result = service.ingest_notebook(command)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": result.error}
            )

    return IngestNotebookResponse(
        notebook_id=notebook_id,
        chunks_ingested=result.value,
        message=f"Successfully ingested {result.value} content chunks into vector database"
    )


@router.get(
    "/{notebook_id}/similar",
    response_model=SimilaritySearchResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        500: {"model": ErrorResponse, "description": "Search failed"}
    }
)
def search_similar_content(
    notebook_id: UUID,
    query: str = Query(..., min_length=1, max_length=10000, description="Search query text"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of results"),
    service: ContentSimilarityService = Depends(get_content_similarity_service)
):
    """
    Search for similar content within a notebook using semantic similarity.

    This endpoint performs a vector similarity search to find content chunks
    that are semantically similar to the query text.

    Args:
        notebook_id: UUID of the notebook to search within
        query: Search query text
        limit: Maximum number of results to return
        service: Injected content similarity service

    Returns:
        List of similar content chunks with relevance scores

    Raises:
        HTTPException: 404 if notebook not found, 500 if search fails
    """
    search_query = SimilaritySearchQuery(
        notebook_id=notebook_id,
        query_text=query,
        collection_name=get_collection_name(notebook_id),
        limit=limit
    )

    result = service.search_similar_content(search_query)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": result.error}
            )

    search_results = result.value

    return SimilaritySearchResponse(
        query=query,
        results=[
            SimilaritySearchResultItem(
                text=r.text,
                source_id=r.source_id,
                chunk_index=r.chunk_index,
                distance=r.distance,
                certainty=r.certainty,
                source_name=r.metadata.get("source_name")
            )
            for r in search_results
        ],
        total=len(search_results)
    )


@router.get(
    "/{notebook_id}/vectors/count",
    response_model=VectorCountResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def get_vector_count(
    notebook_id: UUID,
    service: ContentSimilarityService = Depends(get_content_similarity_service)
):
    """
    Get the count of vectors stored for a notebook.

    Args:
        notebook_id: UUID of the notebook
        service: Injected content similarity service

    Returns:
        Count of vectors in the vector database

    Raises:
        HTTPException: 404 if notebook not found
    """
    query = GetVectorCountQuery(
        notebook_id=notebook_id,
        collection_name=get_collection_name(notebook_id)
    )

    result = service.get_vector_count(query)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": result.error}
            )

    return VectorCountResponse(
        notebook_id=notebook_id,
        vector_count=result.value
    )


@router.delete(
    "/{notebook_id}/vectors",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def delete_notebook_vectors(
    notebook_id: UUID,
    service: VectorIngestionService = Depends(get_vector_ingestion_service)
):
    """
    Delete all vectors associated with a notebook.

    Args:
        notebook_id: UUID of the notebook
        service: Injected vector ingestion service

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if notebook not found
    """
    command = DeleteNotebookVectorsCommand(
        notebook_id=notebook_id,
        collection_name=get_collection_name(notebook_id)
    )

    result = service.delete_notebook_vectors(command)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": result.error}
            )

    return None
