"""Query objects for QA operations following CQRS pattern."""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID


@dataclass
class QaResponse:
    """Response from a QA operation."""
    
    question: str
    answer: str
    sources: List['QaSource']
    notebook_id: UUID
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    
    
@dataclass
class QaSource:
    """Source information used in QA response."""
    
    text: str
    source_id: Optional[UUID]
    chunk_index: int
    relevance_score: float
    source_name: Optional[str] = None
    source_type: Optional[str] = None


@dataclass
class GetQaHistoryQuery:
    """Query to get QA history for a notebook."""
    
    notebook_id: UUID
    limit: int = 20
    offset: int = 0
    
    def __post_init__(self):
        """Validate query parameters."""
        if self.limit <= 0:
            raise ValueError("limit must be positive")
        if self.offset < 0:
            raise ValueError("offset cannot be negative")


@dataclass
class QaHistoryItem:
    """Item in QA history."""
    
    id: UUID
    notebook_id: UUID
    question: str
    answer: str
    sources_count: int
    created_at: str  # ISO format timestamp
    confidence_score: Optional[float] = None