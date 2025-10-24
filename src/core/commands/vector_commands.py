"""Command objects for Vector operations following CQRS pattern."""
from typing import Optional
from dataclasses import dataclass
from uuid import UUID


@dataclass
class IngestNotebookCommand:
    """Command to ingest a notebook and its sources into the vector database."""

    notebook_id: UUID
    collection_name: str = "discovery_content"
    chunk_size: int = 1000
    overlap: int = 200
    force_reingest: bool = False


@dataclass
class DeleteNotebookVectorsCommand:
    """Command to delete all vectors associated with a notebook."""

    notebook_id: UUID
    collection_name: str = "discovery_content"
