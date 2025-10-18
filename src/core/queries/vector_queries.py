"""Query objects for Vector operations following CQRS pattern."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from uuid import UUID


@dataclass
class SimilaritySearchQuery:
    """Query to search for similar content within a notebook."""

    notebook_id: UUID
    query_text: str
    collection_name: str = "discovery_content"
    limit: int = 10


@dataclass
class SimilaritySearchResult:
    """Result from a similarity search."""

    text: str
    source_id: Optional[UUID]
    chunk_index: int
    distance: Optional[float]
    certainty: Optional[float]
    metadata: Dict[str, Any]

    @staticmethod
    def from_vector_result(result: Dict[str, Any]) -> 'SimilaritySearchResult':
        """Create a result from a vector database result."""
        metadata = result.get("metadata", {})

        # Parse source_id from string to UUID if present
        source_id_str = metadata.get("source_id")
        source_id = UUID(source_id_str) if source_id_str else None

        return SimilaritySearchResult(
            text=result.get("text", ""),
            source_id=source_id,
            chunk_index=metadata.get("chunk_index", 0),
            distance=result.get("distance"),
            certainty=result.get("certainty"),
            metadata=metadata
        )


@dataclass
class GetVectorCountQuery:
    """Query to get count of vectors for a notebook."""

    notebook_id: UUID
    collection_name: str = "discovery_content"
