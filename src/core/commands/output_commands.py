"""Commands for output operations."""
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from ..value_objects.enums import OutputType


@dataclass
class GenerateBlogPostCommand:
    """Command to generate a blog post from notebook sources."""
    
    notebook_id: UUID
    title: str
    prompt: Optional[str] = None
    template_name: Optional[str] = None
    target_word_count: int = 550  # 500-600 words as requested
    include_references: bool = True
    tone: str = "informative"  # informative, casual, formal, etc.
    
    def __post_init__(self):
        """Validate command data after initialization."""
        if not self.notebook_id:
            raise ValueError("Notebook ID is required")
        
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")
        
        if self.target_word_count < 100 or self.target_word_count > 2000:
            raise ValueError("Target word count must be between 100 and 2000")
        
        # Normalize title
        self.title = self.title.strip()


@dataclass
class CreateOutputCommand:
    """Command to create a new output record."""
    
    notebook_id: UUID
    title: str
    output_type: OutputType = OutputType.BLOG_POST
    prompt: Optional[str] = None
    template_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate command data after initialization."""
        if not self.notebook_id:
            raise ValueError("Notebook ID is required")
        
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")
        
        # Normalize title
        self.title = self.title.strip()


@dataclass
class UpdateOutputCommand:
    """Command to update an existing output."""
    
    output_id: UUID
    title: Optional[str] = None
    content: Optional[str] = None
    
    def __post_init__(self):
        """Validate command data after initialization."""
        if not self.output_id:
            raise ValueError("Output ID is required")
        
        # At least one field must be provided for update
        if self.title is None and self.content is None:
            raise ValueError("At least one field (title or content) must be provided for update")
        
        # Normalize title if provided
        if self.title is not None:
            self.title = self.title.strip()
            if not self.title:
                raise ValueError("Title cannot be empty")


@dataclass
class DeleteOutputCommand:
    """Command to delete an output."""
    
    output_id: UUID
    
    def __post_init__(self):
        """Validate command data after initialization."""
        if not self.output_id:
            raise ValueError("Output ID is required")


@dataclass
class UpdateGenerationStatusCommand:
    """Command to update the generation status of an output."""
    
    output_id: UUID
    content: Optional[str] = None
    references: Optional[List[str]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate command data after initialization."""
        if not self.output_id:
            raise ValueError("Output ID is required")