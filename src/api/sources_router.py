"""FastAPI router for Source CRUD operations."""
from typing import List, Optional
from uuid import UUID
import base64
from fastapi import APIRouter, HTTPException, status, Depends

from ..core.services.source_ingestion_service import SourceIngestionService
from ..core.commands.source_commands import (
    ImportFileSourceCommand,
    ImportUrlSourceCommand,
    DeleteSourceCommand,
    RestoreSourceCommand,
    RenameSourceCommand,
    ExtractContentCommand
)
from ..core.queries.source_queries import (
    GetSourceByIdQuery,
    ListSourcesQuery
)
from ..core.value_objects.enums import SourceType, FileType, SortOption, SortOrder
from .dtos import (
    ImportFileSourceRequest,
    ImportUrlSourceRequest,
    RenameSourceRequest,
    ExtractContentRequest,
    SourceResponse,
    SourceListResponse,
    SourcePreviewResponse,
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


def get_notebook_repository():
    """
    Dependency injection for INotebookRepository.

    Needed by SourceIngestionService to validate notebooks and update counts.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository

    # Get database session
    db = next(get_db())
    try:
        repository = PostgresNotebookRepository(db)
        yield repository
    finally:
        db.close()


def get_source_service(
    source_repo = Depends(get_source_repository),
    notebook_repo = Depends(get_notebook_repository)
) -> SourceIngestionService:
    """
    Dependency injection for SourceIngestionService.

    Uses dependency injection to get repository implementations.
    """
    # For now, we pass None for provider dependencies (file storage, content extraction, web fetch)
    # These would be implemented later when those providers are added
    return SourceIngestionService(
        source_repository=source_repo,
        notebook_repository=notebook_repo,
        file_storage_provider=None,
        content_extraction_provider=None,
        web_fetch_provider=None
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

    Args:
        request: File source import data
        service: Injected source service

    Returns:
        Created source

    Raises:
        HTTPException: 400 for validation errors, 404 if notebook not found, 409 for duplicates
    """
    # Decode base64 content for hash calculation
    try:
        content_bytes = base64.b64decode(request.content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid base64 content: {str(e)}"}
        )

    # Convert file_type string to enum
    try:
        file_type_enum = FileType(request.file_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Unsupported file type: {request.file_type}"}
        )

    command = ImportFileSourceCommand(
        notebook_id=request.notebook_id,
        name=request.name,
        file_path=request.file_path,
        file_type=file_type_enum,
        file_size=request.file_size,
        content=content_bytes,
        metadata={}
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

    Args:
        request: URL source import data
        service: Injected source service

    Returns:
        Created source

    Raises:
        HTTPException: 400 for validation errors, 404 if notebook not found, 409 for duplicates
    """
    metadata = {}
    if request.title:
        metadata["title"] = request.title

    command = ImportUrlSourceCommand(
        notebook_id=request.notebook_id,
        name=request.name,
        url=request.url,
        content=request.content,
        metadata=metadata
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
        source_type=source_type_enum,
        file_type=file_type_enum,
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

    count_result = service.get_count(notebook_id, include_deleted)
    total = count_result.value if count_result.is_success else 0

    return SourceListResponse(
        sources=[to_source_response(src) for src in result.value],
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
    command = RenameSourceCommand(
        source_id=source_id,
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
    command = ExtractContentCommand(
        source_id=source_id,
        force=request.force
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
