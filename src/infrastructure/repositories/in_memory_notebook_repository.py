"""In-memory implementation of INotebookRepository for testing and development."""
from typing import Optional, List, Dict
from uuid import UUID
from copy import deepcopy

from ...core.entities.notebook import Notebook
from ...core.interfaces.repositories.i_notebook_repository import INotebookRepository
from ...core.results.result import Result
from ...core.queries.notebook_queries import ListNotebooksQuery
from ...core.value_objects.enums import SortOption, SortOrder


class InMemoryNotebookRepository(INotebookRepository):
    """
    In-memory implementation of INotebookRepository.

    This implementation stores notebooks in memory using a dictionary.
    Suitable for testing and development, not for production use.
    """

    def __init__(self):
        """Initialize the repository with an empty storage."""
        self._storage: Dict[UUID, Notebook] = {}

    def add(self, notebook: Notebook) -> Result[Notebook]:
        """
        Add a new notebook to the repository.

        Args:
            notebook: The notebook entity to add

        Returns:
            Result[Notebook]: Success with the added notebook or failure
        """
        if notebook.id in self._storage:
            return Result.failure(f"Notebook with ID {notebook.id} already exists")

        # Store a copy to prevent external modification
        self._storage[notebook.id] = deepcopy(notebook)
        return Result.success(deepcopy(notebook))

    def update(self, notebook: Notebook) -> Result[Notebook]:
        """
        Update an existing notebook in the repository.

        Args:
            notebook: The notebook entity to update

        Returns:
            Result[Notebook]: Success with the updated notebook or failure
        """
        if notebook.id not in self._storage:
            return Result.failure(f"Notebook with ID {notebook.id} not found")

        # Update the stored notebook
        self._storage[notebook.id] = deepcopy(notebook)
        return Result.success(deepcopy(notebook))

    def upsert(self, notebook: Notebook) -> Result[Notebook]:
        """
        Add or update a notebook (insert if doesn't exist, update if exists).

        Args:
            notebook: The notebook entity to upsert

        Returns:
            Result[Notebook]: Success with the upserted notebook or failure
        """
        self._storage[notebook.id] = deepcopy(notebook)
        return Result.success(deepcopy(notebook))

    def get_by_id(self, notebook_id: UUID) -> Result[Optional[Notebook]]:
        """
        Get a notebook by its ID.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[Optional[Notebook]]: Success with notebook if found, None if not found
        """
        notebook = self._storage.get(notebook_id)
        if notebook is None:
            return Result.success(None)

        return Result.success(deepcopy(notebook))

    def exists(self, notebook_id: UUID) -> Result[bool]:
        """
        Check if a notebook exists by its ID.

        Args:
            notebook_id: The UUID of the notebook

        Returns:
            Result[bool]: Success with True if exists, False if not
        """
        return Result.success(notebook_id in self._storage)

    def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> Result[bool]:
        """
        Check if a notebook with the given name exists.

        Args:
            name: The notebook name to check (case-insensitive comparison)
            exclude_id: Optional ID to exclude from the check (for updates)

        Returns:
            Result[bool]: Success with True if exists, False if not
        """
        normalized_name = name.strip().lower()

        for notebook_id, notebook in self._storage.items():
            # Skip if this is the excluded ID
            if exclude_id and notebook_id == exclude_id:
                continue

            # Case-insensitive comparison
            if notebook.name.lower() == normalized_name:
                return Result.success(True)

        return Result.success(False)

    def delete(self, notebook_id: UUID) -> Result[None]:
        """
        Delete a notebook by its ID.

        Args:
            notebook_id: The UUID of the notebook to delete

        Returns:
            Result[None]: Success or failure
        """
        if notebook_id not in self._storage:
            return Result.failure(f"Notebook with ID {notebook_id} not found")

        del self._storage[notebook_id]
        return Result.success(None)

    def get_all(self, query: Optional[ListNotebooksQuery] = None) -> Result[List[Notebook]]:
        """
        Get all notebooks with optional filtering and sorting.

        Args:
            query: Optional query parameters for filtering and sorting

        Returns:
            Result[List[Notebook]]: Success with list of notebooks
        """
        notebooks = list(self._storage.values())

        # Apply filters if query provided
        if query:
            # Filter by tags
            if query.tags:
                notebooks = [
                    nb for nb in notebooks
                    if any(tag in nb.tags for tag in query.tags)
                ]

            # Filter by date range
            if query.date_from:
                notebooks = [nb for nb in notebooks if nb.created_at >= query.date_from]

            if query.date_to:
                notebooks = [nb for nb in notebooks if nb.created_at <= query.date_to]

            # Sort notebooks
            reverse = query.sort_order == SortOrder.DESC

            if query.sort_by == SortOption.NAME:
                notebooks.sort(key=lambda nb: nb.name.lower(), reverse=reverse)
            elif query.sort_by == SortOption.CREATED_AT:
                notebooks.sort(key=lambda nb: nb.created_at, reverse=reverse)
            elif query.sort_by == SortOption.UPDATED_AT:
                notebooks.sort(key=lambda nb: nb.updated_at, reverse=reverse)
            elif query.sort_by == SortOption.SOURCE_COUNT:
                notebooks.sort(key=lambda nb: nb.source_count, reverse=reverse)

            # Apply pagination
            if query.offset:
                notebooks = notebooks[query.offset:]

            if query.limit:
                notebooks = notebooks[:query.limit]

        # Return deep copies to prevent external modification
        return Result.success([deepcopy(nb) for nb in notebooks])

    def count(self) -> Result[int]:
        """
        Get the total count of notebooks.

        Returns:
            Result[int]: Success with count
        """
        return Result.success(len(self._storage))

    def clear(self) -> None:
        """Clear all notebooks from the repository (useful for testing)."""
        self._storage.clear()
