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
