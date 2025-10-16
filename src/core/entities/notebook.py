"""Notebook domain entity."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from ..results.result import Result
from ..results.validation_error import ValidationError


@dataclass
class Notebook:
    """
    A collection container for organizing related sources and outputs
    around a specific research topic or project.
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    source_count: int = 0
    output_count: int = 0

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Normalize name
        if self.name:
            self.name = self.name.strip()

        # Normalize tags
        self.tags = [tag.lower().strip() for tag in self.tags if tag.strip()]

    @staticmethod
    def create(
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Result['Notebook']:
        """
        Factory method to create a new notebook with validation.

        Args:
            name: Notebook name (required, max 255 chars)
            description: Optional description (max 2000 chars)
            tags: Optional list of tags for categorization

        Returns:
            Result[Notebook]: Success with notebook or failure with validation errors
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
        elif len(name) > 255:
            errors.append(ValidationError(
                field="name",
                message="Name cannot exceed 255 characters",
                code="MAX_LENGTH"
            ))

        # Validate description
        if description and len(description) > 2000:
            errors.append(ValidationError(
                field="description",
                message="Description cannot exceed 2000 characters",
                code="MAX_LENGTH"
            ))

        # Return validation failures if any
        if errors:
            return Result.validation_failure(errors)

        # Create notebook
        notebook = Notebook(
            name=name,
            description=description,
            tags=tags or []
        )

        return Result.success(notebook)

    def rename(self, new_name: str) -> Result[None]:
        """
        Rename the notebook.

        Args:
            new_name: New name for the notebook

        Returns:
            Result[None]: Success or failure with validation errors
        """
        errors = []

        # Validate new name
        new_name = new_name.strip() if new_name else ""
        if not new_name:
            errors.append(ValidationError(
                field="new_name",
                message="Name is required and cannot be empty",
                code="REQUIRED"
            ))
        elif len(new_name) > 255:
            errors.append(ValidationError(
                field="new_name",
                message="Name cannot exceed 255 characters",
                code="MAX_LENGTH"
            ))

        if errors:
            return Result.validation_failure(errors)

        # Update name and timestamp
        self.name = new_name
        self.updated_at = datetime.utcnow()

        return Result.success(None)

    def add_tags(self, tags: List[str]) -> Result[None]:
        """
        Add tags to the notebook.

        Args:
            tags: List of tags to add

        Returns:
            Result[None]: Success or failure
        """
        # Normalize and add unique tags
        normalized_tags = [tag.lower().strip() for tag in tags if tag.strip()]
        for tag in normalized_tags:
            if tag not in self.tags:
                self.tags.append(tag)

        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def remove_tags(self, tags: List[str]) -> Result[None]:
        """
        Remove tags from the notebook.

        Args:
            tags: List of tags to remove

        Returns:
            Result[None]: Success or failure
        """
        # Normalize tags for comparison
        normalized_tags = [tag.lower().strip() for tag in tags]
        self.tags = [tag for tag in self.tags if tag not in normalized_tags]

        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def update_description(self, description: Optional[str]) -> Result[None]:
        """
        Update the notebook description.

        Args:
            description: New description (max 2000 chars)

        Returns:
            Result[None]: Success or failure with validation errors
        """
        if description and len(description) > 2000:
            return Result.validation_failure([
                ValidationError(
                    field="description",
                    message="Description cannot exceed 2000 characters",
                    code="MAX_LENGTH"
                )
            ])

        self.description = description
        self.updated_at = datetime.utcnow()
        return Result.success(None)

    def increment_source_count(self) -> None:
        """Increment the source count."""
        self.source_count += 1
        self.updated_at = datetime.utcnow()

    def decrement_source_count(self) -> None:
        """Decrement the source count."""
        if self.source_count > 0:
            self.source_count -= 1
            self.updated_at = datetime.utcnow()

    def increment_output_count(self) -> None:
        """Increment the output count."""
        self.output_count += 1
        self.updated_at = datetime.utcnow()

    def decrement_output_count(self) -> None:
        """Decrement the output count."""
        if self.output_count > 0:
            self.output_count -= 1
            self.updated_at = datetime.utcnow()

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """String representation of the notebook."""
        return f"Notebook(id={self.id}, name='{self.name}', sources={self.source_count})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Notebook(id={self.id}, name='{self.name}', "
            f"sources={self.source_count}, outputs={self.output_count}, "
            f"tags={self.tags})"
        )
