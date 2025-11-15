"""Query objects for Mind Map operations following CQRS pattern."""
from typing import List, Optional
from dataclasses import dataclass
from uuid import UUID


@dataclass
class MindMapSource:
    """Source information for mind map generation."""
    
    text: str
    source_id: Optional[UUID]
    chunk_index: int
    relevance_score: float
    source_name: Optional[str] = None
    source_type: Optional[str] = None


@dataclass
class MindMapResponse:
    """Response from mind map generation."""
    
    prompt: str
    markdown_outline: str
    sources: List[MindMapSource]
    notebook_id: UUID
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
