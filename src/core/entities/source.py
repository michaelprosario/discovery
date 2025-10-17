"""Source domain entity."""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field
import hashlib

from ..results.result import Result
from ..results.validation_error import ValidationError
from ..value_objects.enums import SourceType, FileType


@dataclass
class Source:
    """
    A research material imported into a notebook (file or URL).

    Business Rules:
    - Either file_path or url must be set based on source_type
    - File size must be positive and within limits (e.g., max 50MB)
    - Content hash used for duplicate detection
    - Name defaults to filename or page title if not provided
    - Soft delete: deleted_at set instead of physical deletion
    - Cannot modify extracted_text directly (regenerate from source)
    """

    id: UUID = field(default_factory=uuid4)
    notebook_id: UUID = field(default_factory=uuid4)
    name: str = ""
    source_type: SourceType = SourceType.FILE
    file_type: Optional[FileType] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_hash: str = ""
    extracted_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    # Constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    MAX_NAME_LENGTH = 500

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        if self.name:
            self.name = self.name.strip()

    @staticmethod
    def create_file_source(
        notebook_id: UUID,
        name: str,
        file_path: str,
        file_type: FileType,
        file_size: int,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result['Source']:
        """
        Factory method to create a new file source with validation.

        Args:
            notebook_id: Parent notebook UUID
            name: Display name for the source
            file_path: Local file path
            file_type: Type of file (PDF, DOCX, etc.)
            file_size: Size in bytes
            content: File content for hash calculation
            metadata: Optional metadata dictionary

        Returns:
            Result[Source]: Success with source or failure with validation errors
        """
        errors = []

        # Validate name
        name = name.strip() if name else ""
        if not name:
            errors.append(ValidationError(
                field="name",
                message="Name is required and cannot be empty",
                code="REQUIRED"
            ))
        elif len(name) > Source.MAX_NAME_LENGTH:
            errors.append(ValidationError(
                field="name",
                message=f"Name cannot exceed {Source.MAX_NAME_LENGTH} characters",
                code="MAX_LENGTH"
            ))

        # Validate file_path
        if not file_path or not file_path.strip():
            errors.append(ValidationError(
                field="file_path",
                message="File path is required for file sources",
                code="REQUIRED"
            ))

        # Validate file_size
        if file_size <= 0:
            errors.append(ValidationError(
                field="file_size",
                message="File size must be positive",
                code="INVALID_VALUE"
            ))
        elif file_size > Source.MAX_FILE_SIZE:
            errors.append(ValidationError(
                field="file_size",
                message=f"File size exceeds maximum limit of {Source.MAX_FILE_SIZE / (1024*1024):.0f}MB",
                code="MAX_SIZE"
            ))

        if errors:
            return Result.validation_failure(errors)

        # Calculate content hash
        content_hash = hashlib.sha256(content).hexdigest()

        # Create source
        source = Source(
            notebook_id=notebook_id,
            name=name,
            source_type=SourceType.FILE,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            content_hash=content_hash,
            metadata=metadata or {}
        )

        return Result.success(source)

    @staticmethod
    def create_url_source(
        notebook_id: UUID,
        name: str,
        url: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result['Source']:
        """
        Factory method to create a new URL source with validation.

        Args:
            notebook_id: Parent notebook UUID
            name: Display name for the source
            url: Source URL
            content: Fetched content for hash calculation
            metadata: Optional metadata dictionary

        Returns:
            Result[Source]: Success with source or failure with validation errors
        """
        errors = []

        # Validate name
        name = name.strip() if name else ""
        if not name:
            errors.append(ValidationError(
                field="name",
                message="Name is required and cannot be empty",
                code="REQUIRED"
            ))
        elif len(name) > Source.MAX_NAME_LENGTH:
            errors.append(ValidationError(
                field="name",
                message=f"Name cannot exceed {Source.MAX_NAME_LENGTH} characters",
                code="MAX_LENGTH"
            ))

        # Validate URL
        if not url or not url.strip():
            errors.append(ValidationError(
                field="url",
                message="URL is required for URL sources",
                code="REQUIRED"
            ))
        elif not (url.startswith('http://') or url.startswith('https://')):
            errors.append(ValidationError(
                field="url",
                message="URL must start with http:// or https://",
                code="INVALID_FORMAT"
            ))

        if errors:
            return Result.validation_failure(errors)

        # Calculate content hash
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Create source
        source = Source(
            notebook_id=notebook_id,
            name=name,
            source_type=SourceType.URL,
            url=url,
            content_hash=content_hash,
            metadata=metadata or {}
        )

        return Result.success(source)

    def rename(self, new_name: str) -> Result[None]:
        """
        Rename the source.

        Args:
            new_name: New name for the source

        Returns:
            Result[None]: Success or failure with validation errors
        """
        errors = []

        new_name = new_name.strip() if new_name else ""
        if not new_name:
            errors.append(ValidationError(
                field="new_name",
                message="Name is required and cannot be empty",
                code="REQUIRED"
            ))
        elif len(new_name) > self.MAX_NAME_LENGTH:
            errors.append(ValidationError(
                field="new_name",
                message=f"Name cannot exceed {self.MAX_NAME_LENGTH} characters",
                code="MAX_LENGTH"
            ))

        if errors:
            return Result.validation_failure(errors)

        self.name = new_name
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def update_extracted_text(self, text: str) -> Result[None]:
        """
        Update the extracted text content.

        Args:
            text: Extracted text content

        Returns:
            Result[None]: Success or failure
        """
        self.extracted_text = text
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def soft_delete(self) -> Result[None]:
        """
        Soft delete the source by setting deleted_at timestamp.

        Returns:
            Result[None]: Success or failure
        """
        if self.deleted_at is not None:
            return Result.failure("Source is already deleted")

        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def restore(self) -> Result[None]:
        """
        Restore a soft-deleted source.

        Returns:
            Result[None]: Success or failure
        """
        if self.deleted_at is None:
            return Result.failure("Source is not deleted")

        self.deleted_at = None
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def is_deleted(self) -> bool:
        """
        Check if the source is soft-deleted.

        Returns:
            bool: True if deleted, False otherwise
        """
        return self.deleted_at is not None

    def get_preview(self, length: int = 500) -> str:
        """
        Get a preview of the extracted text.

        Args:
            length: Maximum length of preview

        Returns:
            str: Preview text
        """
        if not self.extracted_text:
            return ""

        if len(self.extracted_text) <= length:
            return self.extracted_text

        return self.extracted_text[:length] + "..."

    def validate_file_type(self) -> Result[None]:
        """
        Validate that file_type is set for file sources.

        Returns:
            Result[None]: Success or failure with validation error
        """
        if self.source_type == SourceType.FILE and self.file_type is None:
            return Result.validation_failure([
                ValidationError(
                    field="file_type",
                    message="File type is required for file sources",
                    code="REQUIRED"
                )
            ])

        return Result.success(None)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the source."""
        return f"Source(id={self.id}, name='{self.name}', type={self.source_type.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Source(id={self.id}, name='{self.name}', type={self.source_type.value}, "
            f"notebook_id={self.notebook_id}, deleted={self.is_deleted()})"
        )
