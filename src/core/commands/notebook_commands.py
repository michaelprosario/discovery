"""Command objects for Notebook operations following CQRS pattern."""
from typing import Optional, List
from dataclasses import dataclass
from uuid import UUID


@dataclass
class CreateNotebookCommand:
    """Command to create a new notebook."""

    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class UpdateNotebookCommand:
    """Command to update an existing notebook."""

    notebook_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class RenameNotebookCommand:
    """Command to rename a notebook."""

    notebook_id: UUID
    new_name: str


@dataclass
class DeleteNotebookCommand:
    """Command to delete a notebook."""

    notebook_id: UUID
    cascade: bool = False  # If True, delete all sources and outputs


@dataclass
class AddTagsCommand:
    """Command to add tags to a notebook."""

    notebook_id: UUID
    tags: List[str]


@dataclass
class RemoveTagsCommand:
    """Command to remove tags from a notebook."""

    notebook_id: UUID
    tags: List[str]
