"""Repository interface for Notebook entity - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...entities.notebook import Notebook
from ...results.result import Result
from ...queries.notebook_queries import ListNotebooksQuery


class INotebookRepository(ABC):
    """
    Repository interface for Notebook persistence operations.

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
    def add(self, notebook: Notebook) -> Result[Notebook]:
        """
        Add a new notebook to the repository.

        Args:
            notebook: The notebook entity to add

        Returns:
            Result[Notebook]: Success with the added notebook or failure
        """
        pass

    @abstractmethod
    def update(self, notebook: Notebook) -> Result[Notebook]:
        """
        Update an existing notebook in the repository.

        Args:
            notebook: The notebook entity to update

        Returns:
            Result[Notebook]: Success with the updated notebook or failure
        """
        pass

    @abstractmethod
    def upsert(self, notebook: Notebook) -> Result[Notebook]:
        """
        Add or update a notebook (insert if doesn't exist, update if exists).

        Args:
            notebook: The notebook entity to upsert

        Returns:
            Result[Notebook]: Success with the upserted notebook or failure
        """
        pass

    @abstractmethod
    def get_by_id(self, notebook_id: UUID) -> Result[Optional[Notebook]]:
        """
        Get a notebook by its ID.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[Optional[Notebook]]: Success with notebook if found, None if not found, or failure
        """
        pass

    @abstractmethod
    def exists(self, notebook_id: UUID) -> Result[bool]:
        """
        Check if a notebook exists by its ID.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        pass

    @abstractmethod
    def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> Result[bool]:
        """
        Check if a notebook with the given name exists.

        Args:
            name: The notebook name to check
            exclude_id: Optional ID to exclude from the check (for updates)

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        pass

    @abstractmethod
    def delete(self, notebook_id: UUID) -> Result[None]:
        """
        Delete a notebook by its ID.

        Args:
            notebook_id: The UUID of the notebook to delete

        Returns:
            Result[None]: Success or failure
        """
        pass

    @abstractmethod
    def get_all(self, query: Optional[ListNotebooksQuery] = None) -> Result[List[Notebook]]:
        """
        Get all notebooks with optional filtering and sorting.

        Args:
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Notebook]]: Success with list of notebooks or failure
        """
        pass

    @abstractmethod
    def count(self) -> Result[int]:
        """
        Get the total count of notebooks.

        Returns:
            Result[int]: Success with count or failure
        """
        pass
