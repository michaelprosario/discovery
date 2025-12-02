"""FastAPI router for Notebook CRUD operations."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query

from ..core.services.notebook_management_service import NotebookManagementService
from ..core.services.blog_generation_service import BlogGenerationService
from ..core.commands.notebook_commands import (
    CreateNotebookCommand,
    UpdateNotebookCommand,
    RenameNotebookCommand,
    DeleteNotebookCommand,
    AddTagsCommand,
    RemoveTagsCommand
)
from ..core.commands.output_commands import GenerateBlogPostCommand
from ..core.queries.notebook_queries import (
    GetNotebookByIdQuery,
    ListNotebooksQuery
)
from ..core.value_objects.enums import SortOption, SortOrder
from .auth.firebase_auth import get_current_user_email
from .auth.authorization import require_resource_owner_or_fail
from .dtos import (
    CreateNotebookRequest,
    UpdateNotebookRequest,
    RenameNotebookRequest,
    AddTagsRequest,
    RemoveTagsRequest,
    GenerateBlogPostRequest,
    NotebookResponse,
    NotebookListResponse,
    OutputResponse,
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


def get_output_repository():
    """
    Dependency injection for IOutputRepository.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_output_repository import PostgresOutputRepository

    db = next(get_db())
    try:
        repository = PostgresOutputRepository(db)
        yield repository
    finally:
        db.close()


def get_source_repository():
    """
    Dependency injection for ISourceRepository.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_source_repository import PostgresSourceRepository

    db = next(get_db())
    try:
        repository = PostgresSourceRepository(db)
        yield repository
    finally:
        db.close()


def get_llm_provider():
    """
    Dependency injection for ILlmProvider.
    """
    from ..infrastructure.providers.gemini_llm_provider import GeminiLlmProvider
    return GeminiLlmProvider()


def get_content_extraction_provider():
    """
    Dependency injection for IContentExtractionProvider.
    """
    from ..infrastructure.providers.file_content_extraction_provider import FileContentExtractionProvider
    return FileContentExtractionProvider()


def get_blog_generation_service(
    notebook_repository=Depends(get_notebook_repository),
    source_repository=Depends(get_source_repository),
    output_repository=Depends(get_output_repository),
    llm_provider=Depends(get_llm_provider),
    content_extraction_provider=Depends(get_content_extraction_provider)
) -> BlogGenerationService:
    """
    Dependency injection for BlogGenerationService.
    """
    return BlogGenerationService(
        notebook_repository,
        source_repository,
        output_repository,
        llm_provider,
        content_extraction_provider
    )


def to_output_response(output) -> OutputResponse:
    """Convert output entity to response DTO."""
    return OutputResponse(
        id=output.id,
        notebook_id=output.notebook_id,
        title=output.title,
        content=output.content,
        output_type=output.output_type.value,
        status=output.status.value,
        prompt=output.prompt,
        template_name=output.template_name,
        metadata=output.metadata,
        source_references=output.source_references,
        word_count=output.word_count,
        created_by=output.created_by,
        created_at=output.created_at,
        updated_at=output.updated_at,
        completed_at=output.completed_at
    )


def to_notebook_response(notebook) -> NotebookResponse:
    """Convert notebook entity to response DTO."""
    return NotebookResponse(
        id=notebook.id,
        name=notebook.name,
        description=notebook.description,
        tags=notebook.tags,
        source_count=notebook.source_count,
        output_count=notebook.output_count,
        created_by=notebook.created_by,
        created_at=notebook.created_at,
        updated_at=notebook.updated_at
    )


@router.post(
    "",
    response_model=NotebookResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Duplicate notebook name"}
    }
)
def create_notebook(
    request: CreateNotebookRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Create a new notebook.

    Requires authentication. The notebook will be owned by the authenticated user.

    Args:
        request: Notebook creation data
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        Created notebook

    Raises:
        HTTPException: 400 for validation errors, 401 for unauthorized, 409 for duplicate names
    """
    command = CreateNotebookCommand(
        name=request.name,
        created_by=current_user_email,
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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def get_notebook(
    notebook_id: UUID,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Get a notebook by its ID.

    Requires authentication. Only the owner can access the notebook.

    Args:
        notebook_id: UUID of the notebook
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        Notebook details

    Raises:
        HTTPException: 401 for unauthorized, 404 if notebook not found or not owned by user
    """
    query = GetNotebookByIdQuery(notebook_id=notebook_id)
    result = service.get_notebook_by_id(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    notebook = result.value
    require_resource_owner_or_fail(notebook, current_user_email, "Notebook")

    return to_notebook_response(notebook)


@router.get(
    "",
    response_model=NotebookListResponse,
    responses={
        200: {"description": "List of notebooks"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def list_notebooks(
    tags: Optional[List[str]] = Query(None),
    sort_by: SortOption = SortOption.UPDATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: Optional[int] = None,
    offset: int = 0,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    List all notebooks owned by the authenticated user with optional filtering and sorting.

    Requires authentication. Only returns notebooks owned by the authenticated user.

    Args:
        tags: Filter by tags (optional)
        sort_by: Sort field (default: updated_at)
        sort_order: Sort order (default: desc)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        current_user_email: Email of the authenticated user
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

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error}
        )

    # Filter notebooks by owner
    notebooks = [nb for nb in result.value if nb.created_by == current_user_email]
    total = len(notebooks)

    return NotebookListResponse(
        notebooks=[to_notebook_response(nb) for nb in notebooks],
        total=total
    )


@router.put(
    "/{notebook_id}",
    response_model=NotebookResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate notebook name"}
    }
)
def update_notebook(
    notebook_id: UUID,
    request: UpdateNotebookRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Update an existing notebook.

    Requires authentication. Only the owner can update the notebook.

    Args:
        notebook_id: UUID of the notebook to update
        request: Update data (partial updates supported)
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        Updated notebook

    Raises:
        HTTPException: 400 for validation errors, 401 for unauthorized, 404 if not found, 409 for duplicate names
    """
    # First verify ownership
    get_query = GetNotebookByIdQuery(notebook_id=notebook_id)
    get_result = service.get_notebook_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Notebook")

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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Duplicate notebook name"}
    }
)
def rename_notebook(
    notebook_id: UUID,
    request: RenameNotebookRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Rename a notebook.

    Requires authentication. Only the owner can rename the notebook.

    Args:
        notebook_id: UUID of the notebook to rename
        request: New name
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        Renamed notebook

    Raises:
        HTTPException: 400 for validation errors, 401 for unauthorized, 404 if not found, 409 for duplicate names
    """
    # First verify ownership
    get_query = GetNotebookByIdQuery(notebook_id=notebook_id)
    get_result = service.get_notebook_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Notebook")

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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def delete_notebook(
    notebook_id: UUID,
    cascade: bool = False,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Delete a notebook.

    Requires authentication. Only the owner can delete the notebook.

    Args:
        notebook_id: UUID of the notebook to delete
        cascade: If True, delete all sources and outputs (default: False)
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 400 if has children and cascade=False, 401 for unauthorized, 404 if not found
    """
    # First verify ownership
    get_query = GetNotebookByIdQuery(notebook_id=notebook_id)
    get_result = service.get_notebook_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Notebook")

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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def add_tags(
    notebook_id: UUID,
    request: AddTagsRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Add tags to a notebook.

    Requires authentication. Only the owner can add tags.

    Args:
        notebook_id: UUID of the notebook
        request: Tags to add
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        Updated notebook

    Raises:
        HTTPException: 401 for unauthorized, 404 if notebook not found
    """
    # First verify ownership
    get_query = GetNotebookByIdQuery(notebook_id=notebook_id)
    get_result = service.get_notebook_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Notebook")

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
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def remove_tags(
    notebook_id: UUID,
    request: RemoveTagsRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: NotebookManagementService = Depends(get_notebook_service)
):
    """
    Remove tags from a notebook.

    Requires authentication. Only the owner can remove tags.

    Args:
        notebook_id: UUID of the notebook
        request: Tags to remove
        current_user_email: Email of the authenticated user
        service: Injected notebook service

    Returns:
        Updated notebook

    Raises:
        HTTPException: 401 for unauthorized, 404 if notebook not found
    """
    # First verify ownership
    get_query = GetNotebookByIdQuery(notebook_id=notebook_id)
    get_result = service.get_notebook_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Notebook")

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


@router.post(
    "/{notebook_id}/generate-blog-post",
    response_model=OutputResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        409: {"model": ErrorResponse, "description": "Notebook has no sources"}
    }
)
def generate_blog_post(
    notebook_id: UUID,
    request: GenerateBlogPostRequest,
    current_user_email: str = Depends(get_current_user_email),
    notebook_service: NotebookManagementService = Depends(get_notebook_service),
    service: BlogGenerationService = Depends(get_blog_generation_service)
):
    """
    Generate a blog post from notebook sources.

    Requires authentication. Only the owner can generate blog posts from a notebook.

    This endpoint creates a blog post of 500-600 words based on all sources
    in the specified notebook. The generation process includes:
    - Extracting content from all sources in the notebook
    - Using LLM to synthesize the content into a cohesive blog post
    - Including reference links at the bottom if requested

    Args:
        notebook_id: UUID of the notebook containing sources
        request: Blog post generation parameters
        current_user_email: Email of the authenticated user
        notebook_service: Injected notebook service
        service: Injected blog generation service

    Returns:
        Generated blog post output

    Raises:
        HTTPException: 400 for validation errors, 401 for unauthorized, 404 if notebook not found,
                      409 if notebook has no sources
    """
    # First verify ownership
    get_query = GetNotebookByIdQuery(notebook_id=notebook_id)
    get_result = notebook_service.get_notebook_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Notebook")

    command = GenerateBlogPostCommand(
        notebook_id=notebook_id,
        title=request.title,
        created_by=current_user_email,
        prompt=request.prompt,
        template_name=request.template_name,
        target_word_count=request.target_word_count,
        include_references=request.include_references,
        tone=request.tone
    )

    result = service.generate_blog_post(command)

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
        elif "no sources" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )

    return to_output_response(result.value)
