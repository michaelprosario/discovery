"""FastAPI router for Notebook CRUD operations."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query

from ..core.services.notebook_management_service import NotebookManagementService
from ..core.commands.notebook_commands import (
    CreateNotebookCommand,
    UpdateNotebookCommand,
    RenameNotebookCommand,
    DeleteNotebookCommand,
    AddTagsCommand,
    RemoveTagsCommand
)
from ..core.queries.notebook_queries import (
    GetNotebookByIdQuery,
    ListNotebooksQuery
)
from ..core.value_objects.enums import SortOption, SortOrder
from .dtos import (
    CreateNotebookRequest,
    UpdateNotebookRequest,
    RenameNotebookRequest,
    AddTagsRequest,
    RemoveTagsRequest,
    NotebookResponse,
    NotebookListResponse,
    ErrorResponse,
    ValidationErrorResponse,
    ValidationErrorDetail
)

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


def get_notebook_repository():
    """
    Dependency injection for INotebookRepository.

    Creates a PostgresNotebookRepository with a database session.
    Uses FastAPI's dependency injection system.
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


def get_notebook_service(repository = Depends(get_notebook_repository)) -> NotebookManagementService:
    """
    Dependency injection for NotebookManagementService.

    Uses dependency injection to get the repository implementation.
    """
    return NotebookManagementService(repository)


def to_notebook_response(notebook) -> NotebookResponse:
    """Convert notebook entity to response DTO."""
    return NotebookResponse(
        id=notebook.id,
        name=notebook.name,
        description=notebook.description,
        tags=notebook.tags,
        source_count=notebook.source_count,
        output_count=notebook.output_count,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at
    )


@router.post(
    "",
    response_model=NotebookResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Duplicate notebook name"}
    }
)
def create_notebook(
    request: CreateNotebookRequest,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Create a new notebook.

    Args:
        request: Notebook creation data
        service: Injected notebook service

    Returns:
        Created notebook

    Raises:
        HTTPException: 400 for validation errors, 409 for duplicate names
    """
    command = CreateNotebookCommand(
        name=request.name,
        description=request.description,
        tags=request.tags
    )

    result = service.create_notebook(command)

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
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )

    return to_notebook_response(result.value)


@router.get(
    "/{notebook_id}",
    response_model=NotebookResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def get_notebook(
    notebook_id: UUID,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Get a notebook by its ID.

    Args:
        notebook_id: UUID of the notebook
        service: Injected notebook service

    Returns:
        Notebook details

    Raises:
        HTTPException: 404 if notebook not found
    """
    query = GetNotebookByIdQuery(notebook_id=notebook_id)
    result = service.get_notebook_by_id(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    return to_notebook_response(result.value)


@router.get(
    "",
    response_model=NotebookListResponse,
    responses={
        200: {"description": "List of notebooks"}
    }
)
def list_notebooks(
    tags: Optional[List[str]] = Query(None),
    sort_by: SortOption = SortOption.UPDATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: Optional[int] = None,
    offset: int = 0,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    List all notebooks with optional filtering and sorting.

    Args:
        tags: Filter by tags (optional)
        sort_by: Sort field (default: updated_at)
        sort_order: Sort order (default: desc)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        service: Injected notebook service

    Returns:
        List of notebooks with total count
    """
    query = ListNotebooksQuery(
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    result = service.list_notebooks(query)

    result = service.list_notebooks(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error}
        )

    notebooks = result.value
    count_result = service.get_count(query)
    total = count_result.value if count_result.is_success else 0

    return NotebookListResponse(
        notebooks=[to_notebook_response(nb) for nb in notebooks],
        total=total
    )


@router.put(
    "/{notebook_id}",
    response_model=NotebookResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate notebook name"}
    }
)
def update_notebook(
    notebook_id: UUID,
    request: UpdateNotebookRequest,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Update an existing notebook.

    Args:
        notebook_id: UUID of the notebook to update
        request: Update data (partial updates supported)
        service: Injected notebook service

    Returns:
        Updated notebook

    Raises:
        HTTPException: 400 for validation errors, 404 if not found, 409 for duplicate names
    """
    command = UpdateNotebookCommand(
        notebook_id=notebook_id,
        name=request.name,
        description=request.description,
        tags=request.tags
    )

    result = service.update_notebook(command)

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
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )

    return to_notebook_response(result.value)


@router.patch(
    "/{notebook_id}/rename",
    response_model=NotebookResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate notebook name"}
    }
)
def rename_notebook(
    notebook_id: UUID,
    request: RenameNotebookRequest,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Rename a notebook.

    Args:
        notebook_id: UUID of the notebook to rename
        request: New name
        service: Injected notebook service

    Returns:
        Renamed notebook

    Raises:
        HTTPException: 400 for validation errors, 404 if not found, 409 for duplicate names
    """
    command = RenameNotebookCommand(
        notebook_id=notebook_id,
        new_name=request.new_name
    )

    result = service.rename_notebook(command)

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
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )

    return to_notebook_response(result.value)


@router.delete(
    "/{notebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Cannot delete (has children)"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def delete_notebook(
    notebook_id: UUID,
    cascade: bool = False,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Delete a notebook.

    Args:
        notebook_id: UUID of the notebook to delete
        cascade: If True, delete all sources and outputs (default: False)
        service: Injected notebook service

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 400 if has children and cascade=False, 404 if not found
    """
    command = DeleteNotebookCommand(
        notebook_id=notebook_id,
        cascade=cascade
    )

    result = service.delete_notebook(command)

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

    return None


@router.post(
    "/{notebook_id}/tags",
    response_model=NotebookResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def add_tags(
    notebook_id: UUID,
    request: AddTagsRequest,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Add tags to a notebook.

    Args:
        notebook_id: UUID of the notebook
        request: Tags to add
        service: Injected notebook service

    Returns:
        Updated notebook

    Raises:
        HTTPException: 404 if notebook not found
    """
    command = AddTagsCommand(
        notebook_id=notebook_id,
        tags=request.tags
    )

    result = service.add_tags(command)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    return to_notebook_response(result.value)


@router.delete(
    "/{notebook_id}/tags",
    response_model=NotebookResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def remove_tags(
    notebook_id: UUID,
    request: RemoveTagsRequest,
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Remove tags from a notebook.

    Args:
        notebook_id: UUID of the notebook
        request: Tags to remove
        service: Injected notebook service

    Returns:
        Updated notebook

    Raises:
        HTTPException: 404 if notebook not found
    """
    command = RemoveTagsCommand(
        notebook_id=notebook_id,
        tags=request.tags
    )

    result = service.remove_tags(command)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    return to_notebook_response(result.value)
