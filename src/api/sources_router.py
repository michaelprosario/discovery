"""FastAPI router for Source CRUD operations."""
from typing import List, Optional
from uuid import UUID
import base64
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from ..core.services.source_ingestion_service import SourceIngestionService
from ..core.services.article_search_service import ArticleSearchService
from ..core.commands.source_commands import (
    ImportFileSourceCommand,
    ImportUrlSourceCommand,
    ImportTextSourceCommand,
    DeleteSourceCommand,
    RestoreSourceCommand,
    RenameSourceCommand,
    ExtractContentCommand
)
from ..core.queries.source_queries import (
    GetSourceByIdQuery,
    ListSourcesQuery,
    GetSourceCountQuery
)
from ..core.queries.article_search_queries import ArticleSearchQuery
from ..core.value_objects.enums import SourceType, FileType, SortOption, SortOrder
from .dtos import (
    ImportFileSourceRequest,
    ImportUrlSourceRequest,
    ImportTextSourceRequest,
    RenameSourceRequest,
    ExtractContentRequest,
    SourceResponse,
    SourceListResponse,
    SourcePreviewResponse,
    AddSourcesBySearchRequest,
    AddSourcesBySearchResult,
    AddSourcesBySearchResponse,
    ErrorResponse,
    ValidationErrorResponse,
    ValidationErrorDetail
)

router = APIRouter(prefix="/api/sources", tags=["sources"])


def get_source_repository():
    """
    Dependency injection for ISourceRepository.

    Creates a PostgresSourceRepository with a database session.
    Uses FastAPI's dependency injection system.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_source_repository import PostgresSourceRepository

    # Get database session
    db = next(get_db())
    try:
        repository = PostgresSourceRepository(db)
        yield repository
    finally:
        db.close()


from .notebooks_router import get_notebook_repository


def get_web_fetch_provider():
    """
    Dependency injection for IWebFetchProvider.

    Creates an HttpWebFetchProvider instance.
    """
    from ..infrastructure.providers.http_web_fetch_provider import HttpWebFetchProvider
    return HttpWebFetchProvider()


def get_content_extraction_provider():
    """
    Dependency injection for IContentExtractionProvider.

    Creates a FileContentExtractionProvider instance.
    """
    from ..infrastructure.providers.file_content_extraction_provider import FileContentExtractionProvider
    return FileContentExtractionProvider()


def get_file_storage_provider():
    """
    Dependency injection for IFileStorageProvider.

    Creates a LocalFileStorageProvider instance.
    """
    from ..infrastructure.providers.local_file_storage_provider import LocalFileStorageProvider
    return LocalFileStorageProvider()


def get_source_service(
    source_repo = Depends(get_source_repository),
    notebook_repo = Depends(get_notebook_repository),
    web_fetch_provider = Depends(get_web_fetch_provider),
    content_extraction_provider = Depends(get_content_extraction_provider),
    file_storage_provider = Depends(get_file_storage_provider)
) -> SourceIngestionService:
    """
    Dependency injection for SourceIngestionService.

    Uses dependency injection to get repository implementations and providers.
    """
    return SourceIngestionService(
        source_repository=source_repo,
        notebook_repository=notebook_repo,
        file_storage_provider=file_storage_provider,
        content_extraction_provider=content_extraction_provider,
        web_fetch_provider=web_fetch_provider
    )


def to_source_response(source) -> SourceResponse:
    """Convert source entity to response DTO."""
    return SourceResponse(
        id=source.id,
        notebook_id=source.notebook_id,
        name=source.name,
        source_type=source.source_type.value,
        file_type=source.file_type.value if source.file_type else None,
        url=source.url,
        file_path=source.file_path,
        file_size=source.file_size,
        content_hash=source.content_hash,
        extracted_text=source.extracted_text,
        metadata=source.metadata,
        created_at=source.created_at,
        updated_at=source.updated_at,
        deleted_at=source.deleted_at
    )


def summary_to_source_response(summary) -> SourceResponse:
    """Convert source summary to response DTO."""
    return SourceResponse(
        id=summary.id,
        notebook_id=summary.notebook_id,
        name=summary.name,
        source_type=summary.source_type.value,
        file_type=summary.file_type.value if summary.file_type else None,
        url=summary.url,
        file_path=None,  # SourceSummary doesn't include file_path
        file_size=summary.file_size,
        content_hash="",  # SourceSummary doesn't include content_hash
        extracted_text="",  # SourceSummary only has has_extracted_text flag
        metadata={},  # SourceSummary doesn't include metadata
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        deleted_at=summary.deleted_at
    )


@router.post(
    "/file",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate content"}
    }
)
def import_file_source(
    request: ImportFileSourceRequest,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Import a file source into a notebook.

    The content is sent as a base64 encoded string.

    Args:
        request: File source import data (name, file_content, file_type, notebook_id)
        service: Injected source service

    Returns:
        Created source

    Raises:
        HTTPException: 400 for validation/extraction errors, 404 if notebook not found, 409 for duplicates
    """
    # Convert file_type string to enum
    try:
        file_type_enum = FileType(request.file_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Unsupported file type: {request.file_type}"}
        )

    # Decode base64 content
    try:
        content_bytes = base64.b64decode(request.file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid base64 content: {str(e)}"}
        )

    # Build metadata
    metadata = {
        "file_size": len(content_bytes),
    }

    command = ImportFileSourceCommand(
        notebook_id=request.notebook_id,
        file_name=request.name,
        file_type=file_type_enum,
        file_content=content_bytes,
        metadata=metadata
    )

    result = service.import_file_source(command)

    if result.is_failure:
        if result.validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": result.error,
                    "validation_errors": [
                        ValidationErrorDetail(
                            field=err.field,
                            message=err.message,
                            code=err.code
                        ).model_dump()
                        for err in result.validation_errors
                    ]
                }
            )
        elif "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        elif "duplicate" in result.error.lower() or "already exists" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )

    return to_source_response(result.value)


@router.post(
    "/url",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate content"}
    }
)
def import_url_source(
    request: ImportUrlSourceRequest,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Import a URL source into a notebook.

    The content will be automatically fetched from the URL.
    The name/title will be extracted from the page if not provided.

    Args:
        request: URL source import data (url, notebook_id, optional title)
        service: Injected source service
        web_fetch_provider: Injected web fetch provider

    Returns:
        Created source

    Raises:
        HTTPException: 400 for validation/fetch errors, 404 if notebook not found, 409 for duplicates
    """

    # Use provided title or extracted title as the name
    # If title is provided in request, use it; otherwise use extracted title
    name = request.title

    command = ImportUrlSourceCommand(
        notebook_id=request.notebook_id,
        title=name,  # Use title as name
        url=request.url
    )

    result = service.import_url_source(command)

    if result.is_failure:
        if result.validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": result.error,
                    "validation_errors": [
                        ValidationErrorDetail(
                            field=err.field,
                            message=err.message,
                            code=err.code
                        ).model_dump()
                        for err in result.validation_errors
                    ]
                }
            )
        elif "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        elif "duplicate" in result.error.lower() or "already exists" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )

    return to_source_response(result.value)


@router.post(
    "/text",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate content"}
    }
)
def import_text_source(
    request: ImportTextSourceRequest,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Import a text source into a notebook.

    The text content is provided directly in the request.
    This is useful for pasting text snippets or notes directly into the notebook.

    Args:
        request: Text source import data (title, content, notebook_id)
        service: Injected source service

    Returns:
        Created source

    Raises:
        HTTPException: 400 for validation errors, 404 if notebook not found, 409 for duplicates
    """
    command = ImportTextSourceCommand(
        notebook_id=request.notebook_id,
        title=request.title,
        content=request.content,
        metadata={"content_length": len(request.content)}
    )

    result = service.import_text_source(command)

    if result.is_failure:
        if result.validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": result.error,
                    "validation_errors": [
                        ValidationErrorDetail(
                            field=err.field,
                            message=err.message,
                            code=err.code
                        ).model_dump()
                        for err in result.validation_errors
                    ]
                }
            )
        elif "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        elif "duplicate" in result.error.lower() or "already exists" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )

    return to_source_response(result.value)


@router.get(
    "/{source_id}",
    response_model=SourceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Source not found"}
    }
)
def get_source(
    source_id: UUID,
    include_deleted: bool = False,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Get a source by its ID.

    Args:
        source_id: UUID of the source
        include_deleted: Include soft-deleted sources
        service: Injected source service

    Returns:
        Source details

    Raises:
        HTTPException: 404 if source not found
    """
    query = GetSourceByIdQuery(
        source_id=source_id,
        include_deleted=include_deleted
    )
    result = service.get_source_by_id(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    return to_source_response(result.value)


@router.get(
    "/notebook/{notebook_id}",
    response_model=SourceListResponse,
    responses={
        200: {"description": "List of sources for notebook"}
    }
)
def list_sources_by_notebook(
    notebook_id: UUID,
    include_deleted: bool = False,
    source_type: Optional[str] = None,
    file_type: Optional[str] = None,
    sort_by: SortOption = SortOption.CREATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: Optional[int] = None,
    offset: int = 0,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    List all sources for a notebook with optional filtering and sorting.

    Args:
        notebook_id: UUID of the notebook
        include_deleted: Include soft-deleted sources
        source_type: Filter by source type ('file' or 'url')
        file_type: Filter by file type (for file sources)
        sort_by: Sort field (default: created_at)
        sort_order: Sort order (default: desc)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        service: Injected source service

    Returns:
        List of sources with total count
    """
    # Convert string enums if provided
    source_type_enum = None
    if source_type:
        try:
            source_type_enum = SourceType(source_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Invalid source_type: {source_type}"}
            )

    file_type_enum = None
    if file_type:
        try:
            file_type_enum = FileType(file_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Invalid file_type: {file_type}"}
            )

    query = ListSourcesQuery(
        notebook_id=notebook_id,
        include_deleted=include_deleted,
        source_types=[source_type_enum] if source_type_enum else None,
        file_types=[file_type_enum] if file_type_enum else None,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    result = service.list_sources(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error}
        )

    count_query = GetSourceCountQuery(notebook_id=notebook_id, include_deleted=include_deleted)
    count_result = service.get_count(count_query)
    total = count_result.value if count_result.is_success else 0

    return SourceListResponse(
        sources=[summary_to_source_response(summary) for summary in result.value],
        total=total
    )


@router.patch(
    "/{source_id}/rename",
    response_model=SourceResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Source not found"}
    }
)
def rename_source(
    source_id: UUID,
    request: RenameSourceRequest,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Rename a source.

    Args:
        source_id: UUID of the source to rename
        request: New name
        service: Injected source service

    Returns:
        Renamed source

    Raises:
        HTTPException: 400 for validation errors, 404 if not found
    """
    # First get the source to retrieve its notebook_id
    from ..core.queries.source_queries import GetSourceByIdQuery
    
    get_query = GetSourceByIdQuery(source_id=source_id, include_deleted=False)
    get_result = service.get_source_by_id(get_query)
    
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    
    source = get_result.value
    
    # Now use the actual notebook_id from the source
    command = RenameSourceCommand(
        source_id=source_id,
        notebook_id=source.notebook_id,
        new_name=request.new_name
    )

    result = service.rename_source(command)

    if result.is_failure:
        if result.validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": result.error,
                    "validation_errors": [
                        ValidationErrorDetail(
                            field=err.field,
                            message=err.message,
                            code=err.code
                        ).model_dump()
                        for err in result.validation_errors
                    ]
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )

    return to_source_response(result.value)


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Source not found"}
    }
)
def delete_source(
    source_id: UUID,
    notebook_id: UUID,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Soft delete a source.

    Args:
        source_id: UUID of the source to delete
        notebook_id: UUID of the parent notebook (for validation)
        service: Injected source service

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if source not found
    """
    command = DeleteSourceCommand(
        source_id=source_id,
        notebook_id=notebook_id
    )

    result = service.delete_source(command)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    return None


@router.post(
    "/{source_id}/restore",
    response_model=SourceResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Source not deleted"},
        404: {"model": ErrorResponse, "description": "Source not found"}
    }
)
def restore_source(
    source_id: UUID,
    notebook_id: UUID,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Restore a soft-deleted source.

    Args:
        source_id: UUID of the source to restore
        notebook_id: UUID of the parent notebook (for validation)
        service: Injected source service

    Returns:
        Restored source

    Raises:
        HTTPException: 400 if not deleted, 404 if not found
    """
    command = RestoreSourceCommand(
        source_id=source_id,
        notebook_id=notebook_id
    )

    result = service.restore_source(command)

    if result.is_failure:
        if "not deleted" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )

    return to_source_response(result.value)


@router.post(
    "/{source_id}/extract",
    response_model=SourceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Source not found"}
    }
)
def extract_content(
    source_id: UUID,
    request: ExtractContentRequest,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Extract content from a source.

    Args:
        source_id: UUID of the source
        request: Extraction parameters
        service: Injected source service

    Returns:
        Source with extracted content

    Raises:
        HTTPException: 404 if source not found
    """
    # First get the source to retrieve its notebook_id
    from ..core.queries.source_queries import GetSourceByIdQuery
    
    get_query = GetSourceByIdQuery(source_id=source_id, include_deleted=False)
    get_result = service.get_source_by_id(get_query)
    
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    
    source = get_result.value
    
    # Now use the actual notebook_id from the source
    command = ExtractContentCommand(
        source_id=source_id,
        notebook_id=source.notebook_id,
        force_reextract=request.force
    )

    result = service.extract_content(command)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    return to_source_response(result.value)


@router.get(
    "/{source_id}/preview",
    response_model=SourcePreviewResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Source not found"}
    }
)
def get_source_preview(
    source_id: UUID,
    length: int = 500,
    service: SourceIngestionService = Depends(get_source_service)
):
    """
    Get a preview of source content.

    Args:
        source_id: UUID of the source
        length: Length of preview (default: 500 characters)
        service: Injected source service

    Returns:
        Source preview

    Raises:
        HTTPException: 404 if source not found
    """
    query = GetSourceByIdQuery(source_id=source_id, include_deleted=False)
    result = service.get_source_by_id(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    source = result.value
    preview = source.get_preview(length)

    return SourcePreviewResponse(
        id=source.id,
        name=source.name,
        preview=preview,
        full_text_length=len(source.extracted_text)
    )


def get_article_search_service() -> ArticleSearchService:
    """Dependency injection for ArticleSearchService."""
    try:
        from ..infrastructure.providers.gemini_article_search_provider import GeminiArticleSearchProvider
        gemini_provider = GeminiArticleSearchProvider()
        return ArticleSearchService(gemini_provider)
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize article search service: {str(e)}"
        )


@router.post(
    "/search-and-add",
    response_model=AddSourcesBySearchResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        500: {"model": ErrorResponse, "description": "Search or import failed"}
    }
)
def add_sources_by_search(
    request: AddSourcesBySearchRequest,
    source_service: SourceIngestionService = Depends(get_source_service),
    article_service: ArticleSearchService = Depends(get_article_search_service)
):
    """
    Add sources to a notebook by searching for relevant articles.

    This endpoint searches for articles based on a search phrase/question,
    then attempts to add each found article as a URL source to the notebook.

    Args:
        request: Search phrase and notebook information
        source_service: Injected source ingestion service
        article_service: Injected article search service

    Returns:
        Results of the search and source addition process

    Raises:
        HTTPException: 400 for validation errors, 404 if notebook not found, 500 for search failures
    """
    # First, search for articles
    search_query = ArticleSearchQuery(
        question=request.search_phrase,
        max_results=request.max_results
    )

    search_result = article_service.search_articles(search_query)

    if search_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Article search failed: {search_result.error}"}
        )

    articles = search_result.value.articles
    results = []
    total_added = 0

    # Try to add each article as a URL source
    for article in articles:
        try:
            # Create command to import URL source
            import_command = ImportUrlSourceCommand(
                notebook_id=request.notebook_id,
                title=article.title,
                url=article.link
            )

            # Attempt to import the URL source
            import_result = source_service.import_url_source(import_command)

            if import_result.is_success:
                results.append(AddSourcesBySearchResult(
                    title=article.title,
                    url=article.link,
                    source_id=import_result.value.id,
                    success=True,
                    error=None
                ))
                total_added += 1
            else:
                results.append(AddSourcesBySearchResult(
                    title=article.title,
                    url=article.link,
                    source_id=None,
                    success=False,
                    error=import_result.error
                ))

        except Exception as e:
            results.append(AddSourcesBySearchResult(
                title=article.title,
                url=article.link,
                source_id=None,
                success=False,
                error=str(e)
            ))

    return AddSourcesBySearchResponse(
        notebook_id=request.notebook_id,
        search_phrase=request.search_phrase,
        results=results,
        total_found=len(articles),
        total_added=total_added
    )
