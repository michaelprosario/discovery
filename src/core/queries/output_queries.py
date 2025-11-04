"""Queries for output operations."""
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..value_objects.enums import OutputType, OutputStatus, SortOption, SortOrder


@dataclass
class GetOutputByIdQuery:
    """Query to get an output by its ID."""
    
    output_id: UUID
    
    def __post_init__(self):
        """Validate query data after initialization."""
        if not self.output_id:
            raise ValueError("Output ID is required")


@dataclass 
class ListOutputsByNotebookQuery:
    """Query to list outputs for a specific notebook."""
    
    notebook_id: UUID
    output_type: Optional[OutputType] = None
    status: Optional[OutputStatus] = None
    sort_by: SortOption = SortOption.UPDATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: int = 0
    
    def __post_init__(self):
        """Validate query data after initialization."""
        if not self.notebook_id:
            raise ValueError("Notebook ID is required")
        
        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be positive")
        
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


@dataclass
class ListAllOutputsQuery:
    """Query to list all outputs across notebooks."""
    
    output_type: Optional[OutputType] = None
    status: Optional[OutputStatus] = None
    notebook_ids: Optional[List[UUID]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: SortOption = SortOption.UPDATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: int = 0
    
    def __post_init__(self):
        """Validate query data after initialization."""
        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be positive")
        
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")
        
        if (self.created_after and self.created_before and 
            self.created_after >= self.created_before):
            raise ValueError("created_after must be before created_before")


@dataclass
class SearchOutputsQuery:
    """Query to search outputs by content or title."""
    
    search_term: str
    notebook_id: Optional[UUID] = None
    output_type: Optional[OutputType] = None
    status: Optional[OutputStatus] = None
    sort_by: SortOption = SortOption.UPDATED_AT
    sort_order: SortOrder = SortOrder.DESC
    limit: Optional[int] = None
    offset: int = 0
    
    def __post_init__(self):
        """Validate query data after initialization."""
        if not self.search_term or not self.search_term.strip():
            raise ValueError("Search term is required")
        
        self.search_term = self.search_term.strip()
        
        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be positive")
        
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")


@dataclass
class OutputSummary:
    """Summary data for output listings."""
    
    id: UUID
    notebook_id: UUID
    title: str
    output_type: OutputType
    status: OutputStatus
    word_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_output(cls, output) -> 'OutputSummary':
        """Create summary from output entity."""
        return cls(
            id=output.id,
            notebook_id=output.notebook_id,
            title=output.title,
            output_type=output.output_type,
            status=output.status,
            word_count=output.word_count,
            created_at=output.created_at,
            updated_at=output.updated_at,
            completed_at=output.completed_at
        )