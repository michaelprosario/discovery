"""Output management service - orchestrates output CRUD operations."""
from typing import List, Optional
from uuid import UUID

from ..entities.output import Output
from ..interfaces.repositories.i_output_repository import IOutputRepository
from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..commands.output_commands import (
    CreateOutputCommand,
    UpdateOutputCommand,
    DeleteOutputCommand,
    UpdateGenerationStatusCommand
)
from ..queries.output_queries import (
    GetOutputByIdQuery,
    ListOutputsByNotebookQuery,
    ListAllOutputsQuery,
    SearchOutputsQuery,
    OutputSummary
)
from ..results.result import Result
from ..results.validation_error import ValidationError


class OutputManagementService:
    """
    Domain service for managing output lifecycle operations.

    This service orchestrates operations across outputs and enforces
    business rules. It depends on repository abstractions (DIP).
    """

    def __init__(
        self,
        output_repository: IOutputRepository,
        notebook_repository: INotebookRepository
    ):
        """
        Initialize the service with its dependencies.

        Args:
            output_repository: Repository abstraction for output persistence
            notebook_repository: Repository abstraction for notebook validation
        """
        self._output_repository = output_repository
        self._notebook_repository = notebook_repository

    def create_output(self, command: CreateOutputCommand) -> Result[Output]:
        """
        Create a new output.

        Business Logic:
        - Validates notebook exists
        - Creates output entity
        - Persists via repository
        - Updates notebook output count

        Args:
            command: CreateOutputCommand with output details

        Returns:
            Result[Output]: Success with created output or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        # Create output entity (with validation)
        create_result = Output.create(
            notebook_id=command.notebook_id,
            title=command.title,
            output_type=command.output_type,
            prompt=command.prompt,
            template_name=command.template_name
        )

        if create_result.is_failure:
            return create_result

        output = create_result.value

        # Persist output
        add_result = self._output_repository.add(output)
        if add_result.is_failure:
            return Result.failure(f"Failed to create output: {add_result.error}")

        # Update notebook output count
        notebook = notebook_result.value
        notebook.increment_output_count()
        self._notebook_repository.update(notebook)

        return Result.success(add_result.value)

    def get_output_by_id(self, query: GetOutputByIdQuery) -> Result[Output]:
        """
        Get an output by its ID.

        Args:
            query: GetOutputByIdQuery with output ID

        Returns:
            Result[Output]: Success with output or failure if not found
        """
        result = self._output_repository.get_by_id(query.output_id)

        if result.is_failure:
            return Result.failure(f"Failed to retrieve output: {result.error}")

        if result.value is None:
            return Result.failure(f"Output with ID {query.output_id} not found")

        return Result.success(result.value)

    def update_output(self, command: UpdateOutputCommand) -> Result[Output]:
        """
        Update an existing output.

        Business Logic:
        - Validates output exists
        - Checks if output is editable (not currently generating)
        - Updates allowed fields
        - Updates timestamp
        - Persists changes

        Args:
            command: UpdateOutputCommand with output ID and updates

        Returns:
            Result[Output]: Success with updated output or failure
        """
        # Get existing output
        get_result = self._output_repository.get_by_id(command.output_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve output: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Output with ID {command.output_id} not found")

        output = get_result.value

        # Check if output is editable
        if not output.is_editable():
            return Result.failure("Cannot edit output while generation is in progress")

        # Update title if provided
        if command.title is not None:
            title_result = output.update_title(command.title)
            if title_result.is_failure:
                return title_result

        # Update content if provided
        if command.content is not None:
            content_result = output.update_content(command.content)
            if content_result.is_failure:
                return content_result

        # Persist changes
        update_result = self._output_repository.update(output)
        if update_result.is_failure:
            return Result.failure(f"Failed to update output: {update_result.error}")

        return Result.success(update_result.value)

    def delete_output(self, command: DeleteOutputCommand) -> Result[None]:
        """
        Delete an output.

        Business Logic:
        - Validates output exists
        - Checks if output can be deleted (not currently generating)
        - Deletes output
        - Updates notebook output count

        Args:
            command: DeleteOutputCommand with output ID

        Returns:
            Result[None]: Success or failure
        """
        # Get existing output
        get_result = self._output_repository.get_by_id(command.output_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve output: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Output with ID {command.output_id} not found")

        output = get_result.value

        # Check if output can be deleted
        if not output.is_editable():
            return Result.failure("Cannot delete output while generation is in progress")

        # Delete output
        delete_result = self._output_repository.delete(command.output_id)
        if delete_result.is_failure:
            return Result.failure(f"Failed to delete output: {delete_result.error}")

        # Update notebook output count
        notebook_result = self._notebook_repository.get_by_id(output.notebook_id)
        if notebook_result.is_success and notebook_result.value:
            notebook = notebook_result.value
            notebook.decrement_output_count()
            self._notebook_repository.update(notebook)

        return Result.success(None)

    def list_outputs_by_notebook(self, query: ListOutputsByNotebookQuery) -> Result[List[OutputSummary]]:
        """
        List outputs for a specific notebook.

        Args:
            query: ListOutputsByNotebookQuery with filtering and sorting

        Returns:
            Result[List[OutputSummary]]: Success with list of output summaries or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(query.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {query.notebook_id} not found")

        # Get outputs
        result = self._output_repository.get_by_notebook(query)
        if result.is_failure:
            return Result.failure(f"Failed to retrieve outputs: {result.error}")

        # Convert to summaries
        summaries = [OutputSummary.from_output(output) for output in result.value]
        return Result.success(summaries)

    def list_all_outputs(self, query: Optional[ListAllOutputsQuery] = None) -> Result[List[OutputSummary]]:
        """
        List all outputs with optional filtering.

        Args:
            query: Optional ListAllOutputsQuery with filtering and sorting

        Returns:
            Result[List[OutputSummary]]: Success with list of output summaries or failure
        """
        result = self._output_repository.get_all(query)
        if result.is_failure:
            return Result.failure(f"Failed to retrieve outputs: {result.error}")

        # Convert to summaries
        summaries = [OutputSummary.from_output(output) for output in result.value]
        return Result.success(summaries)

    def search_outputs(self, query: SearchOutputsQuery) -> Result[List[OutputSummary]]:
        """
        Search outputs by content or title.

        Args:
            query: SearchOutputsQuery with search parameters

        Returns:
            Result[List[OutputSummary]]: Success with list of matching output summaries or failure
        """
        result = self._output_repository.search(query)
        if result.is_failure:
            return Result.failure(f"Failed to search outputs: {result.error}")

        # Convert to summaries
        summaries = [OutputSummary.from_output(output) for output in result.value]
        return Result.success(summaries)

    def get_output_count_by_notebook(self, notebook_id: UUID) -> Result[int]:
        """
        Get the count of outputs for a specific notebook.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[int]: Success with count or failure
        """
        result = self._output_repository.count_by_notebook(notebook_id)
        if result.is_failure:
            return Result.failure(f"Failed to count outputs: {result.error}")

        return Result.success(result.value)

    def get_total_output_count(self, query: Optional[ListAllOutputsQuery] = None) -> Result[int]:
        """
        Get the total count of outputs.

        Args:
            query: Optional query for filtering

        Returns:
            Result[int]: Success with count or failure
        """
        result = self._output_repository.count(query)
        if result.is_failure:
            return Result.failure(f"Failed to count outputs: {result.error}")

        return Result.success(result.value)

    def update_generation_status(self, command: UpdateGenerationStatusCommand) -> Result[Output]:
        """
        Update the generation status of an output.

        Used to complete or fail generation from external processes.

        Args:
            command: UpdateGenerationStatusCommand with status updates

        Returns:
            Result[Output]: Success with updated output or failure
        """
        # Get existing output
        get_result = self._output_repository.get_by_id(command.output_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve output: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Output with ID {command.output_id} not found")

        output = get_result.value

        # Update based on command
        if command.error_message:
            # Mark as failed
            fail_result = output.fail_generation(command.error_message)
            if fail_result.is_failure:
                return fail_result
        elif command.content:
            # Mark as completed
            completion_result = output.complete_generation(command.content, command.references)
            if completion_result.is_failure:
                return completion_result
        else:
            return Result.failure("Must provide either content or error_message")

        # Persist changes
        update_result = self._output_repository.update(output)
        if update_result.is_failure:
            return Result.failure(f"Failed to update output: {update_result.error}")

        return Result.success(update_result.value)