"""Custom exception types for the Discovery CLI."""

from __future__ import annotations


class DiscoveryCLIError(Exception):
    """Base error for CLI operations."""


class ConfigNotInitializedError(DiscoveryCLIError):
    """Raised when configuration is missing or incomplete."""


class ApiRequestError(DiscoveryCLIError):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class EditorLaunchError(DiscoveryCLIError):
    """Raised when the user's editor cannot be launched."""
