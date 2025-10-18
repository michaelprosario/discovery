"""Query objects for Notebook operations following CQRS pattern."""
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ..value_objects.enums import SortOption, SortOrder


@dataclass
class GetNotebookByIdQuery:
    """Query to get a notebook by its ID."""

    notebook_id: UUID


@dataclass
class ListNotebooksQuery:
    """Query to list notebooks with optional filtering and sorting."""

    tags: Optional[List[str]] = field(default=None)

    def __post_init__(self):
        if self.tags:
            self.tags = [tag.lower() for tag in self.tags]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: SortOption = SortOption.UPDATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: int = 0


@dataclass
class CheckNotebookExistsQuery:
    """Query to check if a notebook exists by ID."""

    notebook_id: UUID


@dataclass
class CheckNotebookNameExistsQuery:
    """Query to check if a notebook name already exists."""

    name: str
    exclude_id: Optional[UUID] = None  # Exclude this ID from check (for updates)


@dataclass
class NotebookSummary:
    """Summary information about a notebook for list views."""

    id: UUID
    name: str
    description: Optional[str]
    tags: List[str]
    source_count: int
    output_count: int
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_notebook(notebook) -> 'NotebookSummary':
        """Create a summary from a notebook entity."""
        return NotebookSummary(
            id=notebook.id,
            name=notebook.name,
            description=notebook.description,
            tags=notebook.tags.copy(),
            source_count=notebook.source_count,
            output_count=notebook.output_count,
            created_at=notebook.created_at,
            updated_at=notebook.updated_at
        )
