"""Validation error model for Result pattern."""
from typing import Optional
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a validation error for a specific field or rule."""

    field: str
    message: str
    code: Optional[str] = None

    def __str__(self) -> str:
        """String representation of validation error."""
        if self.code:
            return f"{self.field}: {self.message} (code: {self.code})"
        return f"{self.field}: {self.message}"
