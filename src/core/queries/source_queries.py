"""Query objects for Source operations following CQRS pattern."""
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ..value_objects.enums import SourceType, FileType, SortOption, SortOrder


@dataclass
class GetSourceByIdQuery:
    """Query to get a source by its ID."""

    source_id: UUID
    include_deleted: bool = False  # If True, include soft-deleted sources


@dataclass
class ListSourcesQuery:
    """Query to list sources in a notebook with optional filtering and sorting."""

    notebook_id: UUID
    source_types: Optional[List[SourceType]] = None
    file_types: Optional[List[FileType]] = None
    include_deleted: bool = False
    sort_by: SortOption = SortOption.CREATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: int = 0


@dataclass
class CheckSourceExistsQuery:
    """Query to check if a source exists by ID."""

    source_id: UUID
    include_deleted: bool = False


@dataclass
class CheckDuplicateSourceQuery:
    """Query to check if a source with the same content hash exists in a notebook."""

    notebook_id: UUID
    content_hash: str


@dataclass
class GetSourceCountQuery:
    """Query to get count of sources in a notebook."""

    notebook_id: UUID
    include_deleted: bool = False


@dataclass
class SourceSummary:
    """Summary information about a source for list views."""

    id: UUID
    notebook_id: UUID
    name: str
    source_type: SourceType
    file_type: Optional[FileType]
    url: Optional[str]
    file_size: Optional[int]
    has_extracted_text: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    @staticmethod
    def from_source(source) -> 'SourceSummary':
        """Create a summary from a source entity."""
        return SourceSummary(
            id=source.id,
            notebook_id=source.notebook_id,
            name=source.name,
            source_type=source.source_type,
            file_type=source.file_type,
            url=source.url,
            file_size=source.file_size,
            has_extracted_text=bool(source.extracted_text),
            created_by=source.created_by,
            created_at=source.created_at,
            updated_at=source.updated_at,
            deleted_at=source.deleted_at
        )
