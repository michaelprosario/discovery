"""In-memory implementation of ISourceRepository for testing."""
from typing import Dict, List, Optional
from uuid import UUID
from copy import deepcopy

from ...core.entities.source import Source
from ...core.interfaces.repositories.i_source_repository import ISourceRepository
from ...core.queries.source_queries import ListSourcesQuery
from ...core.results.result import Result
from ...core.value_objects.enums import SortOption, SortOrder


class InMemorySourceRepository(ISourceRepository):
    """
    In-memory implementation of ISourceRepository for testing.

    This provides a simple dictionary-based storage for sources without
    requiring a real database.
    """

    def __init__(self):
        """Initialize the in-memory storage."""
        self._sources: Dict[UUID, Source] = {}

    def add(self, source: Source) -> Result[Source]:
        """Add a new source to the repository."""
        if source.id in self._sources:
            return Result.failure(f"Source with ID {source.id} already exists")

        self._sources[source.id] = deepcopy(source)
        return Result.success(deepcopy(source))

    def update(self, source: Source) -> Result[Source]:
        """Update an existing source in the repository."""
        if source.id not in self._sources:
            return Result.failure(f"Source with ID {source.id} not found")

        self._sources[source.id] = deepcopy(source)
        return Result.success(deepcopy(source))

    def upsert(self, source: Source) -> Result[Source]:
        """Add or update a source."""
        self._sources[source.id] = deepcopy(source)
        return Result.success(deepcopy(source))

    def get_by_id(self, source_id: UUID, include_deleted: bool = False) -> Result[Optional[Source]]:
        """Get a source by its ID."""
        source = self._sources.get(source_id)

        if source is None:
            return Result.success(None)

        if not include_deleted and source.is_deleted():
            return Result.success(None)

        return Result.success(deepcopy(source))

    def exists(self, source_id: UUID, include_deleted: bool = False) -> Result[bool]:
        """Check if a source exists by its ID."""
        source = self._sources.get(source_id)

        if source is None:
            return Result.success(False)

        if not include_deleted and source.is_deleted():
            return Result.success(False)

        return Result.success(True)

    def get_by_notebook(self, notebook_id: UUID, query: Optional[ListSourcesQuery] = None) -> Result[List[Source]]:
        """Get all sources for a notebook with optional filtering and sorting."""
        # Filter by notebook_id
        sources = [
            deepcopy(src) for src in self._sources.values()
            if src.notebook_id == notebook_id
        ]

        # Apply query filters if provided
        if query:
            # Filter by deleted status
            if not query.include_deleted:
                sources = [src for src in sources if not src.is_deleted()]

            # Filter by source types
            if query.source_types:
                sources = [src for src in sources if src.source_type in query.source_types]

            # Filter by file types
            if query.file_types:
                sources = [src for src in sources if src.file_type in query.file_types]

            # Apply sorting
            reverse = query.sort_order == SortOrder.DESC

            if query.sort_by == SortOption.NAME:
                sources.sort(key=lambda s: s.name.lower(), reverse=reverse)
            elif query.sort_by == SortOption.CREATED_AT:
                sources.sort(key=lambda s: s.created_at, reverse=reverse)
            elif query.sort_by == SortOption.UPDATED_AT:
                sources.sort(key=lambda s: s.updated_at, reverse=reverse)

            # Apply pagination
            if query.offset:
                sources = sources[query.offset:]
            if query.limit:
                sources = sources[:query.limit]

        return Result.success(sources)

    def get_by_content_hash(self, notebook_id: UUID, content_hash: str) -> Result[Optional[Source]]:
        """Get a source by its content hash within a notebook."""
        for source in self._sources.values():
            if (source.notebook_id == notebook_id and
                source.content_hash == content_hash and
                not source.is_deleted()):
                return Result.success(deepcopy(source))

        return Result.success(None)

    def soft_delete(self, source_id: UUID) -> Result[None]:
        """Soft delete a source."""
        source = self._sources.get(source_id)

        if source is None:
            return Result.failure(f"Source with ID {source_id} not found")

        delete_result = source.soft_delete()
        if delete_result.is_failure:
            return delete_result

        return Result.success(None)

    def delete(self, source_id: UUID) -> Result[None]:
        """Permanently delete a source."""
        if source_id not in self._sources:
            return Result.failure(f"Source with ID {source_id} not found")

        del self._sources[source_id]
        return Result.success(None)

    def count(self, notebook_id: UUID, include_deleted: bool = False) -> Result[int]:
        """Get the count of sources in a notebook."""
        count = 0
        for source in self._sources.values():
            if source.notebook_id == notebook_id:
                if include_deleted or not source.is_deleted():
                    count += 1

        return Result.success(count)

    def clear(self):
        """Clear all sources (for testing)."""
        self._sources.clear()
