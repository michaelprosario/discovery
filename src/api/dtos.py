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
    file_path: str = Field(..., min_length=1, description="Path to the file (content will be extracted automatically)")
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
