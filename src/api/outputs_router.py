"""FastAPI router for Output CRUD operations."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query

from ..core.services.output_management_service import OutputManagementService
from ..core.services.blog_generation_service import BlogGenerationService
from ..core.commands.output_commands import (
    CreateOutputCommand,
    UpdateOutputCommand,
    DeleteOutputCommand,
    GenerateBlogPostCommand
)
from ..core.queries.output_queries import (
    GetOutputByIdQuery,
    ListOutputsByNotebookQuery,
    ListAllOutputsQuery,
    SearchOutputsQuery
)
from ..core.value_objects.enums import SortOption, SortOrder, OutputType, OutputStatus
from .auth.firebase_auth import get_current_user_email
from .auth.authorization import require_resource_owner_or_fail
from .dtos import (
    CreateOutputRequest,
    UpdateOutputRequest,
    GenerateBlogPostRequest,
    OutputResponse,
    OutputSummaryResponse,
    OutputListResponse,
    OutputPreviewResponse,
    ErrorResponse,
    ValidationErrorResponse,
    ValidationErrorDetail
)

router = APIRouter(prefix="/api/outputs", tags=["outputs"])


def get_output_repository():
    """
    Dependency injection for IOutputRepository.

    Creates a PostgresOutputRepository with a database session.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_output_repository import PostgresOutputRepository

    db = next(get_db())
    try:
        repository = PostgresOutputRepository(db)
        yield repository
    finally:
        db.close()


def get_notebook_repository():
    """
    Dependency injection for INotebookRepository.
    """
    from ..infrastructure.database.connection import get_db
    from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository

    db = next(get_db())
    try:
        repository = PostgresNotebookRepository(db)
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
    from ..infrastructure.providers.openai_llm_provider import OpenAiLlmProvider
    return OpenAiLlmProvider()


def get_content_extraction_provider():
    """
    Dependency injection for IContentExtractionProvider.
    """
    from ..infrastructure.providers.content_extraction_provider import ContentExtractionProvider
    return ContentExtractionProvider()


def get_output_service(
    output_repository=Depends(get_output_repository),
    notebook_repository=Depends(get_notebook_repository)
) -> OutputManagementService:
    """
    Dependency injection for OutputManagementService.
    """
    return OutputManagementService(output_repository, notebook_repository)


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


def to_output_summary_response(summary) -> OutputSummaryResponse:
    """Convert output summary to response DTO."""
    return OutputSummaryResponse(
        id=summary.id,
        notebook_id=summary.notebook_id,
        title=summary.title,
        output_type=summary.output_type.value,
        status=summary.status.value,
        word_count=summary.word_count,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        completed_at=summary.completed_at
    )


@router.post(
    "",
    response_model=OutputResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def create_output(
    request: CreateOutputRequest,
    notebook_id: UUID = Query(..., description="UUID of the parent notebook"),
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    Create a new output.

    Requires authentication. The output will be owned by the authenticated user.

    Args:
        request: Output creation data
        notebook_id: UUID of the parent notebook
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        Created output

    Raises:
        HTTPException: 400 for validation errors, 401 for unauthorized, 404 if notebook not found
    """
    command = CreateOutputCommand(
        notebook_id=notebook_id,
        title=request.title,
        created_by=current_user_email,
        output_type=OutputType(request.output_type),
        prompt=request.prompt,
        template_name=request.template_name
    )

    result = service.create_output(command)

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

    return to_output_response(result.value)


@router.get(
    "/{output_id}",
    response_model=OutputResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Output not found"}
    }
)
def get_output(
    output_id: UUID,
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    Get an output by its ID.

    Requires authentication. Only the owner can access the output.

    Args:
        output_id: UUID of the output
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        Output details

    Raises:
        HTTPException: 401 for unauthorized, 404 if output not found or not owned by user
    """
    query = GetOutputByIdQuery(output_id=output_id)
    result = service.get_output_by_id(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    output = result.value
    require_resource_owner_or_fail(output, current_user_email, "Output")

    return to_output_response(output)


@router.get(
    "",
    response_model=OutputListResponse,
    responses={
        200: {"description": "List of outputs"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def list_outputs(
    notebook_id: Optional[UUID] = Query(None, description="Filter by notebook ID"),
    output_type: Optional[OutputType] = Query(None, description="Filter by output type"),
    output_status: Optional[OutputStatus] = Query(None, alias="status", description="Filter by status"),
    sort_by: SortOption = SortOption.UPDATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: Optional[int] = None,
    offset: int = 0,
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    List outputs with optional filtering and sorting.

    Requires authentication. Only returns outputs owned by the authenticated user.

    Args:
        notebook_id: Filter by notebook ID (optional)
        output_type: Filter by output type (optional)
        output_status: Filter by status (optional)
        sort_by: Sort field (default: updated_at)
        sort_order: Sort order (default: desc)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        List of outputs with total count
    """
    if notebook_id:
        # List outputs for specific notebook
        query = ListOutputsByNotebookQuery(
            notebook_id=notebook_id,
            output_type=output_type,
            status=output_status,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        result = service.list_outputs_by_notebook(query)
        count_result = service.get_output_count_by_notebook(notebook_id)
    else:
        # List all outputs
        query = ListAllOutputsQuery(
            output_type=output_type,
            status=output_status,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        result = service.list_all_outputs(query)
        count_result = service.get_total_output_count(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error}
        )

    # Filter outputs by owner
    outputs = [o for o in result.value if o.created_by == current_user_email]
    total = len(outputs)

    return OutputListResponse(
        outputs=[to_output_summary_response(summary) for summary in outputs],
        total=total
    )


@router.put(
    "/{output_id}",
    response_model=OutputResponse,
    responses={
        400: {"model": ValidationErrorResponse, "description": "Validation error or output not editable"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Output not found"}
    }
)
def update_output(
    output_id: UUID,
    request: UpdateOutputRequest,
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    Update an existing output.

    Requires authentication. Only the owner can update the output.

    Args:
        output_id: UUID of the output to update
        request: Update data
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        Updated output

    Raises:
        HTTPException: 400 for validation errors or if not editable, 401 for unauthorized, 404 if not found
    """
    # First verify ownership
    get_query = GetOutputByIdQuery(output_id=output_id)
    get_result = service.get_output_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Output")

    command = UpdateOutputCommand(
        output_id=output_id,
        title=request.title,
        content=request.content
    )

    result = service.update_output(command)

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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )

    return to_output_response(result.value)


@router.delete(
    "/{output_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ErrorResponse, "description": "Cannot delete (output not editable)"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Output not found"}
    }
)
def delete_output(
    output_id: UUID,
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    Delete an output.

    Requires authentication. Only the owner can delete the output.

    Args:
        output_id: UUID of the output to delete
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 400 if not editable, 401 for unauthorized, 404 if not found
    """
    # First verify ownership
    get_query = GetOutputByIdQuery(output_id=output_id)
    get_result = service.get_output_by_id(get_query)
    if get_result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": get_result.error}
        )
    require_resource_owner_or_fail(get_result.value, current_user_email, "Output")

    command = DeleteOutputCommand(output_id=output_id)
    result = service.delete_output(command)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": result.error}
            )

    return None


@router.get(
    "/search",
    response_model=OutputListResponse,
    responses={
        200: {"description": "Search results"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
def search_outputs(
    q: str = Query(..., description="Search term"),
    notebook_id: Optional[UUID] = Query(None, description="Filter by notebook ID"),
    output_type: Optional[OutputType] = Query(None, description="Filter by output type"),
    output_status: Optional[OutputStatus] = Query(None, alias="status", description="Filter by status"),
    sort_by: SortOption = SortOption.UPDATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    limit: Optional[int] = None,
    offset: int = 0,
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    Search outputs by content or title.

    Requires authentication. Only searches within outputs owned by the authenticated user.

    Args:
        q: Search term
        notebook_id: Filter by notebook ID (optional)
        output_type: Filter by output type (optional)
        output_status: Filter by status (optional)
        sort_by: Sort field (default: updated_at)
        sort_order: Sort order (default: desc)
        limit: Maximum number of results (optional)
        offset: Number of results to skip (default: 0)
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        List of matching outputs
    """
    query = SearchOutputsQuery(
        search_term=q,
        notebook_id=notebook_id,
        output_type=output_type,
        status=output_status,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    result = service.search_outputs(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error}
        )

    # Filter outputs by owner
    outputs = [o for o in result.value if o.created_by == current_user_email]

    return OutputListResponse(
        outputs=[to_output_summary_response(summary) for summary in outputs],
        total=len(outputs)
    )


@router.get(
    "/{output_id}/preview",
    response_model=OutputPreviewResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Output not found"}
    }
)
def get_output_preview(
    output_id: UUID,
    length: int = Query(300, ge=50, le=1000, description="Preview length in characters"),
    current_user_email: str = Depends(get_current_user_email),
    service: OutputManagementService = Depends(get_output_service)
):
    """
    Get a preview of output content.

    Requires authentication. Only the owner can preview the output.

    Args:
        output_id: UUID of the output
        length: Preview length in characters
        current_user_email: Email of the authenticated user
        service: Injected output service

    Returns:
        Output preview

    Raises:
        HTTPException: 401 for unauthorized, 404 if output not found
    """
    query = GetOutputByIdQuery(output_id=output_id)
    result = service.get_output_by_id(query)

    if result.is_failure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": result.error}
        )

    output = result.value
    require_resource_owner_or_fail(output, current_user_email, "Output")

    preview = output.content[:length] + "..." if len(output.content) > length else output.content

    return OutputPreviewResponse(
        id=output.id,
        title=output.title,
        preview=preview,
        full_content_length=len(output.content),
        word_count=output.word_count
    )