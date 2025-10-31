"""Command objects for Source operations following CQRS pattern."""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID

from ..value_objects.enums import FileType


@dataclass
class ImportFileSourceCommand:
    """Command to import a file source into a notebook."""

    notebook_id: UUID
    file_name: str
    file_type: FileType
    file_content: bytes  # Raw file content for storage and hash calculation
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ImportUrlSourceCommand:
    """Command to import a URL source into a notebook."""

    notebook_id: UUID
    url: str
    title: Optional[str] = None  # If None, will be extracted from page


@dataclass
class DeleteSourceCommand:
    """Command to delete a source (soft delete)."""

    source_id: UUID
    notebook_id: UUID  # For validation


@dataclass
class RestoreSourceCommand:
    """Command to restore a soft-deleted source."""

    source_id: UUID
    notebook_id: UUID  # For validation


@dataclass
class RenameSourceCommand:
    """Command to rename a source."""

    source_id: UUID
    notebook_id: UUID  # For validation
    new_name: str


@dataclass
class ExtractContentCommand:
    """Command to extract content from a source."""

    source_id: UUID
    notebook_id: UUID  # For validation
    force_reextract: bool = False  # If True, re-extract even if already extracted
