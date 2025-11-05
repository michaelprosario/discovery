"""Repository interface for Output entity - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...entities.output import Output
from ...results.result import Result
from ...queries.output_queries import (
    ListOutputsByNotebookQuery,
    ListAllOutputsQuery,
    SearchOutputsQuery
)


class IOutputRepository(ABC):
    """
    Repository interface for Output persistence operations.

    This interface is defined in the Core layer following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations.

    Following CRUD rules from domain_model.md:
    - provide a way to add domain entity
    - provide a way to update domain entity
    - provide a way to upsert domain entity
    - provide a way to get entity by Id(Guid)
    - provide a way to check if entity exists by Id(Guid)
    """

    @abstractmethod
    def add(self, output: Output) -> Result[Output]:
        """
        Add a new output to the repository.

        Args:
            output: The output entity to add

        Returns:
            Result[Output]: Success with the added output or failure
        """
        pass

    @abstractmethod
    def update(self, output: Output) -> Result[Output]:
        """
        Update an existing output in the repository.

        Args:
            output: The output entity to update

        Returns:
            Result[Output]: Success with the updated output or failure
        """
        pass

    @abstractmethod
    def upsert(self, output: Output) -> Result[Output]:
        """
        Add or update an output (insert if doesn't exist, update if exists).

        Args:
            output: The output entity to upsert

        Returns:
            Result[Output]: Success with the upserted output or failure
        """
        pass

    @abstractmethod
    def get_by_id(self, output_id: UUID) -> Result[Optional[Output]]:
        """
        Get an output by its ID.

        Args:
            output_id: The UUID of the output

        Returns:
            Result[Optional[Output]]: Success with output if found, None if not found, or failure
        """
        pass

    @abstractmethod
    def exists(self, output_id: UUID) -> Result[bool]:
        """
        Check if an output exists by its ID.

        Args:
            output_id: The UUID of the output

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        pass

    @abstractmethod
    def delete(self, output_id: UUID) -> Result[None]:
        """
        Delete an output by its ID.

        Args:
            output_id: The UUID of the output to delete

        Returns:
            Result[None]: Success or failure
        """
        pass

    @abstractmethod
    def get_by_notebook(self, query: ListOutputsByNotebookQuery) -> Result[List[Output]]:
        """
        Get all outputs for a specific notebook with optional filtering and sorting.

        Args:
            query: Query parameters for filtering and sorting

        Returns:
            Result[List[Output]]: Success with list of outputs or failure
        """
        pass

    @abstractmethod
    def get_all(self, query: Optional[ListAllOutputsQuery] = None) -> Result[List[Output]]:
        """
        Get all outputs with optional filtering and sorting.

        Args:
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Output]]: Success with list of outputs or failure
        """
        pass

    @abstractmethod
    def search(self, query: SearchOutputsQuery) -> Result[List[Output]]:
        """
        Search outputs by content or title.

        Args:
            query: Search query parameters

        Returns:
            Result[List[Output]]: Success with list of matching outputs or failure
        """
        pass

    @abstractmethod
    def count_by_notebook(self, notebook_id: UUID) -> Result[int]:
        """
        Get the count of outputs for a specific notebook.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[int]: Success with count or failure
        """
        pass

    @abstractmethod
    def count(self, query: Optional[ListAllOutputsQuery] = None) -> Result[int]:
        """
        Get the total count of outputs.

        Args:
            query: Optional query parameters for filtering

        Returns:
            Result[int]: Success with count or failure
        """
        pass

    @abstractmethod
    def delete_by_notebook(self, notebook_id: UUID) -> Result[None]:
        """
        Delete all outputs for a specific notebook.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[None]: Success or failure
        """
        pass