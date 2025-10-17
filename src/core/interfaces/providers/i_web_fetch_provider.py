"""Web fetch provider interface - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

from ...results.result import Result


@dataclass
class WebContent:
    """Data class for web content fetched from a URL."""

    url: str
    title: str
    html: str
    text: str  # Cleaned/extracted main content
    metadata: Dict[str, Any]


class IWebFetchProvider(ABC):
    """
    Interface for fetching and extracting content from web URLs.

    This interface abstracts web fetching operations following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations.
    """

    @abstractmethod
    def fetch_url(self, url: str, timeout: int = 30) -> Result[WebContent]:
        """
        Fetch content from a URL and extract main content.

        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Result[WebContent]: Success with web content or failure
        """
        pass

    @abstractmethod
    def validate_url(self, url: str) -> Result[bool]:
        """
        Validate that a URL is properly formatted and accessible.

        Args:
            url: The URL to validate

        Returns:
            Result[bool]: Success with True if valid, False otherwise, or failure
        """
        pass

    @abstractmethod
    def extract_main_content(self, html: str) -> Result[str]:
        """
        Extract the main content from HTML, removing ads, navigation, etc.

        Args:
            html: Raw HTML content

        Returns:
            Result[str]: Success with extracted text or failure
        """
        pass
