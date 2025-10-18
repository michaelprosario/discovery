"""Notebook management service - orchestrates notebook CRUD operations."""
from typing import List, Optional
from uuid import UUID

from ..entities.notebook import Notebook
from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..commands.notebook_commands import (
    CreateNotebookCommand,
    UpdateNotebookCommand,
    RenameNotebookCommand,
    DeleteNotebookCommand,
    AddTagsCommand,
    RemoveTagsCommand
)
from ..queries.notebook_queries import (
    GetNotebookByIdQuery,
    ListNotebooksQuery,
    CheckNotebookExistsQuery,
    CheckNotebookNameExistsQuery,
    NotebookSummary
)
from ..results.result import Result
from ..results.validation_error import ValidationError


class NotebookManagementService:
    """
    Domain service for managing notebook lifecycle operations.

    This service orchestrates operations across notebooks and enforces
    business rules. It depends on INotebookRepository abstraction (DIP).
    """

    def __init__(self, notebook_repository: INotebookRepository):
        """
        Initialize the service with its dependencies.

        Args:
            notebook_repository: Repository abstraction for notebook persistence
        """
        self._notebook_repository = notebook_repository

    def create_notebook(self, command: CreateNotebookCommand) -> Result[Notebook]:
        """
        Create a new notebook.

        Business Logic:
        - Validates notebook name uniqueness
        - Normalizes tags
        - Generates UUID and timestamps
        - Creates notebook entity
        - Persists via repository

        Args:
            command: CreateNotebookCommand with notebook details

        Returns:
            Result[Notebook]: Success with created notebook or failure
        """
        # Check if name already exists
        exists_result = self._notebook_repository.exists_by_name(command.name)
        if exists_result.is_failure:
            return Result.failure(f"Failed to check name uniqueness: {exists_result.error}")

        if exists_result.value:
            return Result.validation_failure([
                ValidationError(
                    field="name",
                    message=f"A notebook with name '{command.name}' already exists",
                    code="DUPLICATE_NAME"
                )
            ])

        # Create notebook entity (with validation)
        create_result = Notebook.create(
            name=command.name,
            description=command.description,
            tags=command.tags
        )

        if create_result.is_failure:
            return create_result

        notebook = create_result.value

        # Persist notebook
        add_result = self._notebook_repository.add(notebook)
        if add_result.is_failure:
            return Result.failure(f"Failed to create notebook: {add_result.error}")

        return Result.success(add_result.value)

    def get_notebook_by_id(self, query: GetNotebookByIdQuery) -> Result[Notebook]:
        """
        Get a notebook by its ID.

        Args:
            query: GetNotebookByIdQuery with notebook ID

        Returns:
            Result[Notebook]: Success with notebook or failure if not found
        """
        result = self._notebook_repository.get_by_id(query.notebook_id)

        if result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {result.error}")

        if result.value is None:
            return Result.failure(f"Notebook with ID {query.notebook_id} not found")

        return Result.success(result.value)

    def update_notebook(self, command: UpdateNotebookCommand) -> Result[Notebook]:
        """
        Update an existing notebook.

        Business Logic:
        - Validates notebook exists
        - If name provided, checks uniqueness (excluding current notebook)
        - Updates allowed fields
        - Updates timestamp
        - Persists changes

        Args:
            command: UpdateNotebookCommand with notebook ID and updates

        Returns:
            Result[Notebook]: Success with updated notebook or failure
        """
        # Get existing notebook
        get_result = self._notebook_repository.get_by_id(command.notebook_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = get_result.value

        # Update name if provided
        if command.name is not None:
            # Check name uniqueness
            exists_result = self._notebook_repository.exists_by_name(
                command.name,
                exclude_id=command.notebook_id
            )
            if exists_result.is_failure:
                return Result.failure(f"Failed to check name uniqueness: {exists_result.error}")

            if exists_result.value:
                return Result.validation_failure([
                    ValidationError(
                        field="name",
                        message=f"A notebook with name '{command.name}' already exists",
                        code="DUPLICATE_NAME"
                    )
                ])

            rename_result = notebook.rename(command.name)
            if rename_result.is_failure:
                return rename_result

        # Update description if provided
        if command.description is not None:
            desc_result = notebook.update_description(command.description)
            if desc_result.is_failure:
                return desc_result

        # Update tags if provided
        if command.tags is not None:
            # Replace all tags
            notebook.tags = [tag.lower().strip() for tag in command.tags if tag.strip()]
            notebook.touch()

        # Persist changes
        update_result = self._notebook_repository.update(notebook)
        if update_result.is_failure:
            return Result.failure(f"Failed to update notebook: {update_result.error}")

        return Result.success(update_result.value)

    def rename_notebook(self, command: RenameNotebookCommand) -> Result[Notebook]:
        """
        Rename a notebook.

        Args:
            command: RenameNotebookCommand with notebook ID and new name

        Returns:
            Result[Notebook]: Success with renamed notebook or failure
        """
        # Get existing notebook
        get_result = self._notebook_repository.get_by_id(command.notebook_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = get_result.value

        # Check name uniqueness
        exists_result = self._notebook_repository.exists_by_name(
            command.new_name,
            exclude_id=command.notebook_id
        )
        if exists_result.is_failure:
            return Result.failure(f"Failed to check name uniqueness: {exists_result.error}")

        if exists_result.value:
            return Result.validation_failure([
                ValidationError(
                    field="new_name",
                    message=f"A notebook with name '{command.new_name}' already exists",
                    code="DUPLICATE_NAME"
                )
            ])

        # Rename notebook
        rename_result = notebook.rename(command.new_name)
        if rename_result.is_failure:
            return rename_result

        # Persist changes
        update_result = self._notebook_repository.update(notebook)
        if update_result.is_failure:
            return Result.failure(f"Failed to update notebook: {update_result.error}")

        return Result.success(update_result.value)

    def delete_notebook(self, command: DeleteNotebookCommand) -> Result[None]:
        """
        Delete a notebook.

        Business Logic:
        - Validates notebook exists
        - Checks if notebook has sources/outputs
        - If cascade flag set: soft delete all children (to be implemented)
        - If not cascade: return failure if has children
        - Deletes notebook

        Args:
            command: DeleteNotebookCommand with notebook ID and cascade flag

        Returns:
            Result[None]: Success or failure
        """
        # Get existing notebook
        get_result = self._notebook_repository.get_by_id(command.notebook_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = get_result.value

        # Check if notebook has sources or outputs
        if not command.cascade and (notebook.source_count > 0 or notebook.output_count > 0):
            return Result.validation_failure([
                ValidationError(
                    field="cascade",
                    message=(
                        f"Cannot delete notebook '{notebook.name}' because it contains "
                        f"{notebook.source_count} source(s) and {notebook.output_count} output(s). "
                        f"Use cascade=True to delete all contents."
                    ),
                    code="HAS_CHILDREN"
                )
            ])

        # TODO: If cascade is True, delete all sources and outputs first
        # This would require source and output repositories

        # Delete notebook
        delete_result = self._notebook_repository.delete(command.notebook_id)
        if delete_result.is_failure:
            return Result.failure(f"Failed to delete notebook: {delete_result.error}")

        return Result.success(None)

    def list_notebooks(self, query: ListNotebooksQuery) -> Result[List[NotebookSummary]]:
        """
        List notebooks with optional filtering and sorting.

        Args:
            query: ListNotebooksQuery with filter and sort parameters

        Returns:
            Result[List[NotebookSummary]]: Success with notebook summaries or failure
        """
        # Get notebooks from repository
        get_result = self._notebook_repository.get_all(query)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve notebooks: {get_result.error}")

        notebooks = get_result.value

        # Convert to summaries
        summaries = [NotebookSummary.from_notebook(nb) for nb in notebooks]

        return Result.success(summaries)

    def check_exists(self, query: CheckNotebookExistsQuery) -> Result[bool]:
        """
        Check if a notebook exists.

        Args:
            query: CheckNotebookExistsQuery with notebook ID

        Returns:
            Result[bool]: Success with True/False or failure
        """
        return self._notebook_repository.exists(query.notebook_id)

    def check_name_exists(self, query: CheckNotebookNameExistsQuery) -> Result[bool]:
        """
        Check if a notebook name exists.

        Args:
            query: CheckNotebookNameExistsQuery with name and optional exclude ID

        Returns:
            Result[bool]: Success with True/False or failure
        """
        return self._notebook_repository.exists_by_name(query.name, query.exclude_id)

    def add_tags(self, command: AddTagsCommand) -> Result[Notebook]:
        """
        Add tags to a notebook.

        Args:
            command: AddTagsCommand with notebook ID and tags to add

        Returns:
            Result[Notebook]: Success with updated notebook or failure
        """
        # Get existing notebook
        get_result = self._notebook_repository.get_by_id(command.notebook_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = get_result.value

        # Add tags
        add_result = notebook.add_tags(command.tags)
        if add_result.is_failure:
            return add_result

        # Persist changes
        update_result = self._notebook_repository.update(notebook)
        if update_result.is_failure:
            return Result.failure(f"Failed to update notebook: {update_result.error}")

        return Result.success(update_result.value)

    def remove_tags(self, command: RemoveTagsCommand) -> Result[Notebook]:
        """
        Remove tags from a notebook.

        Args:
            command: RemoveTagsCommand with notebook ID and tags to remove

        Returns:
            Result[Notebook]: Success with updated notebook or failure
        """
        # Get existing notebook
        get_result = self._notebook_repository.get_by_id(command.notebook_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = get_result.value

        # Remove tags
        remove_result = notebook.remove_tags(command.tags)
        if remove_result.is_failure:
            return remove_result

        # Persist changes
        update_result = self._notebook_repository.update(notebook)
        if update_result.is_failure:
            return Result.failure(f"Failed to update notebook: {update_result.error}")

        return Result.success(update_result.value)

    def get_count(self, query: Optional[ListNotebooksQuery] = None) -> Result[int]:
        """
        Get total count of notebooks.

        Returns:
            Result[int]: Success with count or failure
        """
        return self._notebook_repository.count(query)
