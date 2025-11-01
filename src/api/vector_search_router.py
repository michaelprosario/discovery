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


class CreateCollectionRequest(BaseModel):
    """Request to create a collection for a notebook."""
    pass  # No parameters needed - notebook_id comes from path parameter


class CreateCollectionResponse(BaseModel):
    """Response from collection creation."""
    notebook_id: UUID
    collection_name: str
    message: str
    created: bool


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


@router.post(
    "/{notebook_id}/collection",
    response_model=CreateCollectionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        500: {"model": ErrorResponse, "description": "Collection creation failed"}
    }
)
def create_collection(
    notebook_id: UUID,
    request: CreateCollectionRequest = CreateCollectionRequest(),
    service: VectorIngestionService = Depends(get_vector_ingestion_service)
):
    """
    Create a vector collection for a notebook.

    This endpoint creates a Weaviate collection with the schema defined for storing
    notebook content chunks. The collection name follows the pattern 'Notebook{notebook_id_without_hyphens}'.

    Args:
        notebook_id: UUID of the notebook to create collection for (from path)
        request: Collection creation parameters (currently empty)
        service: Injected vector ingestion service

    Returns:
        Collection creation result with collection name and status

    Raises:
        HTTPException: 404 if notebook not found, 500 if creation fails
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository
    from ..infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
    import os

    # First verify that the notebook exists
    db = next(get_db())
    try:
        notebook_repository = PostgresNotebookRepository(db)
        from ..core.queries.notebook_queries import GetNotebookByIdQuery
        from ..core.services.notebook_management_service import NotebookManagementService
        
        notebook_service = NotebookManagementService(notebook_repository)
        query = GetNotebookByIdQuery(notebook_id=notebook_id)
        notebook_result = notebook_service.get_notebook_by_id(query)
        
        if notebook_result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Notebook with ID {notebook_id} not found"}
            )
    finally:
        db.close()

    # Get collection name using the existing helper function
    collection_name = get_collection_name(notebook_id)

    # Create vector database provider
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_key = os.getenv("WEAVIATE_KEY")
    vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)

    try:
        # Check if collection already exists
        exists_result = vector_db_provider.collection_exists(collection_name)
        if exists_result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": f"Failed to check collection existence: {exists_result.error}"}
            )

        already_existed = exists_result.value

        # Create collection using the provider's method
        result = vector_db_provider.create_collection_if_not_exists(collection_name)

        if result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": f"Failed to create collection: {result.error}"}
            )

        message = f"Collection '{collection_name}' already existed" if already_existed else f"Collection '{collection_name}' created successfully"

        return CreateCollectionResponse(
            notebook_id=notebook_id,
            collection_name=collection_name,
            message=message,
            created=not already_existed
        )

    finally:
        vector_db_provider.close()


@router.get(
    "/{notebook_id}/collection/debug",
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        500: {"model": ErrorResponse, "description": "Debug failed"}
    }
)
def debug_collection(
    notebook_id: UUID
):
    """
    Debug endpoint to check collection contents and counts.
    
    This endpoint helps troubleshoot collection issues by showing both
    filtered and unfiltered counts, plus sample data.
    """
    from ..infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
    import os

    collection_name = get_collection_name(notebook_id)
    
    # Create vector database provider
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_key = os.getenv("WEAVIATE_KEY")
    vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)

    try:
        # Check if collection exists
        exists_result = vector_db_provider.collection_exists(collection_name)
        if exists_result.is_failure or not exists_result.value:
            return {
                "collection_name": collection_name,
                "exists": False,
                "error": exists_result.error if exists_result.is_failure else "Collection does not exist"
            }

        # Get total count (no filter)
        total_count_result = vector_db_provider.get_document_count(collection_name, None)
        total_count = total_count_result.value if total_count_result.is_success else 0

        # Get filtered count (with notebook_id filter)
        filtered_count_result = vector_db_provider.get_document_count(
            collection_name, 
            {"notebook_id": str(notebook_id)}
        )
        filtered_count = filtered_count_result.value if filtered_count_result.is_success else 0

        # Try to get a sample document to see the structure
        client = vector_db_provider._get_client()
        collection = client.collections.get(collection_name)
        
        sample_docs = []
        try:
            response = collection.query.fetch_objects(limit=3)
            for obj in response.objects:
                sample_docs.append({
                    "id": str(obj.uuid),
                    "properties": dict(obj.properties)
                })
        except:
            try:
                response = collection.query.near_text(query="", limit=3)
                for obj in response.objects:
                    sample_docs.append({
                        "id": str(obj.uuid),
                        "properties": dict(obj.properties)
                    })
            except Exception as e:
                sample_docs = [{"error": f"Could not fetch sample: {str(e)}"}]

        return {
            "collection_name": collection_name,
            "exists": True,
            "total_count": total_count,
            "filtered_count": filtered_count,
            "filter_used": {"notebook_id": str(notebook_id)},
            "sample_documents": sample_docs
        }

    finally:
        vector_db_provider.close()
