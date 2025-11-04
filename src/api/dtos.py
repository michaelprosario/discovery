"""Data Transfer Objects (DTOs) for API endpoints."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class CreateNotebookRequest(BaseModel):
    """Request model for creating a notebook."""

    name: str = Field(..., min_length=1, max_length=255, description="Notebook name")
    description: Optional[str] = Field(None, max_length=2000, description="Notebook description")
    tags: Optional[List[str]] = Field(default=None, description="List of tags")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate name is not just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class UpdateNotebookRequest(BaseModel):
    """Request model for updating a notebook."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New notebook name")
    description: Optional[str] = Field(None, max_length=2000, description="New description")
    tags: Optional[List[str]] = Field(None, description="New tags (replaces existing)")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not just whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip() if v else None


class RenameNotebookRequest(BaseModel):
    """Request model for renaming a notebook."""

    new_name: str = Field(..., min_length=1, max_length=255, description="New notebook name")

    @field_validator('new_name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate name is not just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class AddTagsRequest(BaseModel):
    """Request model for adding tags to a notebook."""

    tags: List[str] = Field(..., min_length=1, description="Tags to add")


class RemoveTagsRequest(BaseModel):
    """Request model for removing tags from a notebook."""

    tags: List[str] = Field(..., min_length=1, description="Tags to remove")


class NotebookResponse(BaseModel):
    """Response model for a notebook."""

    id: UUID
    name: str
    description: Optional[str]
    tags: List[str]
    source_count: int
    output_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class NotebookListResponse(BaseModel):
    """Response model for a list of notebooks."""

    notebooks: List[NotebookResponse]
    total: int


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str
    details: Optional[dict] = None


class ValidationErrorDetail(BaseModel):
    """Details for a single validation error."""

    field: str
    message: str
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Response model for validation errors."""

    error: str
    validation_errors: List[ValidationErrorDetail]


# Source DTOs

class ImportFileSourceRequest(BaseModel):
    """Request model for importing a file source."""

    notebook_id: UUID = Field(..., description="UUID of the parent notebook")
    name: str = Field(..., min_length=1, max_length=500, description="Source name")
    file_content: str = Field(..., description="Base64 encoded file content")
    file_type: str = Field(..., description="File type (pdf, docx, doc, txt, md)")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate name is not just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class ImportUrlSourceRequest(BaseModel):
    """Request model for importing a URL source."""

    notebook_id: UUID = Field(..., description="UUID of the parent notebook")
    url: str = Field(..., min_length=1, description="Source URL (content will be fetched automatically)")
    title: Optional[str] = Field(None, description="Page title/name (optional, will be extracted from page if not provided)")

    @field_validator('title')
    @classmethod
    def title_not_empty_if_provided(cls, v: Optional[str]) -> Optional[str]:
        """Validate title is not just whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty or whitespace only if provided')
        return v.strip() if v else None

    @field_validator('url')
    @classmethod
    def url_valid_format(cls, v: str) -> str:
        """Validate URL format."""
        if not v.strip():
            raise ValueError('URL cannot be empty')
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class RenameSourceRequest(BaseModel):
    """Request model for renaming a source."""

    new_name: str = Field(..., min_length=1, max_length=500, description="New source name")

    @field_validator('new_name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate name is not just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()


class ExtractContentRequest(BaseModel):
    """Request model for extracting content from a source."""

    force: bool = Field(False, description="Force re-extraction even if already extracted")


class SourceResponse(BaseModel):
    """Response model for a source."""

    id: UUID
    notebook_id: UUID
    name: str
    source_type: str  # 'file' or 'url'
    file_type: Optional[str]  # 'pdf', 'docx', etc.
    url: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    content_hash: str
    extracted_text: str
    metadata: dict
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SourceListResponse(BaseModel):
    """Response model for a list of sources."""

    sources: List[SourceResponse]
    total: int


class SourcePreviewResponse(BaseModel):
    """Response model for source content preview."""

    id: UUID
    name: str
    preview: str
    full_text_length: int


# DTOs for search-based source addition
class AddSourcesBySearchRequest(BaseModel):
    """Request model for adding sources by search phrase."""
    notebook_id: UUID = Field(..., description="UUID of the parent notebook")
    search_phrase: str = Field(..., description="Search phrase or question to find relevant articles", min_length=1)
    max_results: int = Field(5, description="Maximum number of articles to add as sources", ge=1, le=10)


class AddSourcesBySearchResult(BaseModel):
    """Result for a single source addition."""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source_id: Optional[UUID] = Field(None, description="Created source ID (if successful)")
    success: bool = Field(..., description="Whether the source was added successfully")
    error: Optional[str] = Field(None, description="Error message if failed")


class AddSourcesBySearchResponse(BaseModel):
    """Response model for adding sources by search phrase."""
    notebook_id: UUID = Field(..., description="Notebook ID")
    search_phrase: str = Field(..., description="Search phrase used")
    results: List[AddSourcesBySearchResult] = Field(..., description="Results for each found article")
    total_found: int = Field(..., description="Total articles found")
    total_added: int = Field(..., description="Total sources successfully added")


# Output DTOs

class GenerateBlogPostRequest(BaseModel):
    """Request model for generating a blog post."""

    title: str = Field(..., min_length=1, max_length=500, description="Blog post title")
    prompt: Optional[str] = Field(None, max_length=5000, description="Custom prompt for generation")
    template_name: Optional[str] = Field(None, max_length=100, description="Template name to use")
    target_word_count: int = Field(550, ge=100, le=2000, description="Target word count (500-600 recommended)")
    tone: str = Field("informative", description="Tone of the blog post (informative, casual, formal, etc.)")
    include_references: bool = Field(True, description="Include reference links at the bottom")

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate title is not just whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()


class CreateOutputRequest(BaseModel):
    """Request model for creating a new output."""

    title: str = Field(..., min_length=1, max_length=500, description="Output title")
    output_type: str = Field("blog_post", description="Type of output")
    prompt: Optional[str] = Field(None, max_length=5000, description="Custom prompt used")
    template_name: Optional[str] = Field(None, max_length=100, description="Template name used")

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate title is not just whitespace."""
        if not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()


class UpdateOutputRequest(BaseModel):
    """Request model for updating an output."""

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="New output title")
    content: Optional[str] = Field(None, max_length=50000, description="New output content")

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate title is not just whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip() if v else None


class OutputResponse(BaseModel):
    """Response model for an output."""

    id: UUID
    notebook_id: UUID
    title: str
    content: str
    output_type: str
    status: str
    prompt: Optional[str]
    template_name: Optional[str]
    metadata: dict
    source_references: List[str]
    word_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class OutputSummaryResponse(BaseModel):
    """Response model for output summary."""

    id: UUID
    notebook_id: UUID
    title: str
    output_type: str
    status: str
    word_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class OutputListResponse(BaseModel):
    """Response model for a list of outputs."""

    outputs: List[OutputSummaryResponse]
    total: int


class OutputPreviewResponse(BaseModel):
    """Response model for output content preview."""

    id: UUID
    title: str
    preview: str
    full_content_length: int
    word_count: int
