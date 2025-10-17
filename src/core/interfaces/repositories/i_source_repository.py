"""Repository interface for Source entity - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ...entities.source import Source
from ...results.result import Result
from ...queries.source_queries import ListSourcesQuery


class ISourceRepository(ABC):
    """
    Repository interface for Source persistence operations.

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
    def add(self, source: Source) -> Result[Source]:
        """
        Add a new source to the repository.

        Args:
            source: The source entity to add

        Returns:
            Result[Source]: Success with the added source or failure
        """
        pass

    @abstractmethod
    def update(self, source: Source) -> Result[Source]:
        """
        Update an existing source in the repository.

        Args:
            source: The source entity to update

        Returns:
            Result[Source]: Success with the updated source or failure
        """
        pass

    @abstractmethod
    def upsert(self, source: Source) -> Result[Source]:
        """
        Add or update a source (insert if doesn't exist, update if exists).

        Args:
            source: The source entity to upsert

        Returns:
            Result[Source]: Success with the upserted source or failure
        """
        pass

    @abstractmethod
    def get_by_id(self, source_id: UUID, include_deleted: bool = False) -> Result[Optional[Source]]:
        """
        Get a source by its ID.

        Args:
            source_id: The UUID of the source
            include_deleted: If True, include soft-deleted sources

        Returns:
            Result[Optional[Source]]: Success with source if found, None if not found, or failure
        """
        pass

    @abstractmethod
    def exists(self, source_id: UUID, include_deleted: bool = False) -> Result[bool]:
        """
        Check if a source exists by its ID.

        Args:
            source_id: The UUID of the source
            include_deleted: If True, include soft-deleted sources

        Returns:
            Result[bool]: Success with True if exists, False if not, or failure
        """
        pass

    @abstractmethod
    def get_by_notebook(self, notebook_id: UUID, query: Optional[ListSourcesQuery] = None) -> Result[List[Source]]:
        """
        Get all sources for a notebook with optional filtering and sorting.

        Args:
            notebook_id: The UUID of the notebook
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Source]]: Success with list of sources or failure
        """
        pass

    @abstractmethod
    def get_by_content_hash(self, notebook_id: UUID, content_hash: str) -> Result[Optional[Source]]:
        """
        Get a source by its content hash within a notebook (for duplicate detection).

        Args:
            notebook_id: The UUID of the notebook
            content_hash: The SHA256 hash of the content

        Returns:
            Result[Optional[Source]]: Success with source if found, None if not found, or failure
        """
        pass

    @abstractmethod
    def soft_delete(self, source_id: UUID) -> Result[None]:
        """
        Soft delete a source by setting its deleted_at timestamp.

        Args:
            source_id: The UUID of the source to soft delete

        Returns:
            Result[None]: Success or failure
        """
        pass

    @abstractmethod
    def delete(self, source_id: UUID) -> Result[None]:
        """
        Permanently delete a source from the repository.

        Args:
            source_id: The UUID of the source to delete

        Returns:
            Result[None]: Success or failure
        """
        pass

    @abstractmethod
    def count(self, notebook_id: UUID, include_deleted: bool = False) -> Result[int]:
        """
        Get the count of sources in a notebook.

        Args:
            notebook_id: The UUID of the notebook
            include_deleted: If True, include soft-deleted sources

        Returns:
            Result[int]: Success with count or failure
        """
        pass
