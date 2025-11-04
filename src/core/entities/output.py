"""Output domain entity."""
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from ..results.result import Result
from ..results.validation_error import ValidationError
from ..value_objects.enums import OutputType, OutputStatus


@dataclass
class Output:
    """
    Represents a generated output file from notebook sources.
    
    An output is generated content like a blog post, summary, or report
    created from the sources within a notebook using AI/LLM processing.
    """

    id: UUID = field(default_factory=uuid4)
    notebook_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    output_type: OutputType = OutputType.BLOG_POST
    status: OutputStatus = OutputStatus.DRAFT
    prompt: Optional[str] = None
    template_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_references: list[str] = field(default_factory=list)
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Normalize title
        if self.title:
            self.title = self.title.strip()
        
        # Calculate word count from content
        if self.content:
            self.word_count = len(self.content.split())
        
        # Ensure metadata is a dict
        if not isinstance(self.metadata, dict):
            self.metadata = {}

    @staticmethod
    def create(
        notebook_id: UUID,
        title: str,
        output_type: OutputType = OutputType.BLOG_POST,
        prompt: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> Result['Output']:
        """
        Factory method to create a new output with validation.

        Args:
            notebook_id: ID of the parent notebook
            title: Title for the output
            output_type: Type of output (default: BLOG_POST)
            prompt: Optional custom prompt used for generation
            template_name: Optional template name used

        Returns:
            Result[Output]: Success with output or failure with validation errors
        """
        errors = []

        # Validate title
        title = title.strip() if title else ""
        if not title:
            errors.append(ValidationError(
                field="title",
                message="Title is required and cannot be empty",
                code="REQUIRED"
            ))
        elif len(title) > 500:
            errors.append(ValidationError(
                field="title",
                message="Title cannot exceed 500 characters",
                code="MAX_LENGTH"
            ))

        # Validate notebook_id
        if not notebook_id:
            errors.append(ValidationError(
                field="notebook_id",
                message="Notebook ID is required",
                code="REQUIRED"
            ))

        # Validate prompt length if provided
        if prompt and len(prompt) > 5000:
            errors.append(ValidationError(
                field="prompt",
                message="Prompt cannot exceed 5000 characters",
                code="MAX_LENGTH"
            ))

        # Return validation failures if any
        if errors:
            return Result.validation_failure(errors)

        # Create output
        output = Output(
            notebook_id=notebook_id,
            title=title,
            output_type=output_type,
            prompt=prompt,
            template_name=template_name,
            status=OutputStatus.DRAFT
        )

        return Result.success(output)

    def update_content(self, content: str) -> Result[None]:
        """
        Update the output content.

        Args:
            content: New content for the output

        Returns:
            Result[None]: Success or failure with validation errors
        """
        errors = []

        # Validate content length (reasonable limit for blog posts)
        if len(content) > 50000:  # ~20-25 pages
            errors.append(ValidationError(
                field="content",
                message="Content cannot exceed 50000 characters",
                code="MAX_LENGTH"
            ))

        if errors:
            return Result.validation_failure(errors)

        # Update content and metadata
        self.content = content
        self.word_count = len(content.split()) if content else 0
        self.updated_at = datetime.utcnow()

        return Result.success(None)

    def start_generation(self) -> Result[None]:
        """
        Mark the output as being generated.

        Returns:
            Result[None]: Success or failure
        """
        if self.status == OutputStatus.GENERATING:
            return Result.failure("Output is already being generated")

        self.status = OutputStatus.GENERATING
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def complete_generation(self, content: str, references: Optional[list[str]] = None) -> Result[None]:
        """
        Mark the output as completed with final content.

        Args:
            content: Final generated content
            references: List of source references used

        Returns:
            Result[None]: Success or failure with validation errors
        """
        if self.status != OutputStatus.GENERATING:
            return Result.failure("Cannot complete output that is not being generated")

        # Update content
        content_result = self.update_content(content)
        if content_result.is_failure:
            return content_result

        # Update status and references
        self.status = OutputStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        if references:
            self.source_references = references

        return Result.success(None)

    def fail_generation(self, error_message: str) -> Result[None]:
        """
        Mark the output generation as failed.

        Args:
            error_message: Reason for failure

        Returns:
            Result[None]: Success
        """
        self.status = OutputStatus.FAILED
        self.metadata["error"] = error_message
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def update_title(self, title: str) -> Result[None]:
        """
        Update the output title.

        Args:
            title: New title

        Returns:
            Result[None]: Success or failure with validation errors
        """
        errors = []

        # Validate new title
        title = title.strip() if title else ""
        if not title:
            errors.append(ValidationError(
                field="title",
                message="Title is required and cannot be empty",
                code="REQUIRED"
            ))
        elif len(title) > 500:
            errors.append(ValidationError(
                field="title",
                message="Title cannot exceed 500 characters",
                code="MAX_LENGTH"
            ))

        if errors:
            return Result.validation_failure(errors)

        # Update title and timestamp
        self.title = title
        self.updated_at = datetime.utcnow()

        return Result.success(None)

    def add_metadata(self, key: str, value: Any) -> Result[None]:
        """
        Add metadata to the output.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Result[None]: Success
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def is_editable(self) -> bool:
        """Check if the output can be edited (not currently generating)."""
        return self.status != OutputStatus.GENERATING

    def get_duration_minutes(self) -> Optional[float]:
        """Get generation duration in minutes if completed."""
        if self.completed_at and self.status == OutputStatus.COMPLETED:
            delta = self.completed_at - self.created_at
            return delta.total_seconds() / 60
        return None

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the output."""
        return f"Output(id={self.id}, title='{self.title}', type={self.output_type.value}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Output(id={self.id}, notebook_id={self.notebook_id}, "
            f"title='{self.title}', type={self.output_type.value}, "
            f"status={self.status.value}, words={self.word_count})"
        )