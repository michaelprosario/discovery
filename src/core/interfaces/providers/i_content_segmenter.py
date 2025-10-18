"""Content segmenter interface - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import List

from ...results.result import Result


class IContentSegmenter(ABC):
    """
    Interface for segmenting content into chunks for embedding.

    This interface abstracts content segmentation operations following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations using various segmentation strategies.
    """

    @abstractmethod
    def segment(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> Result[List[str]]:
        """
        Segment text into overlapping chunks suitable for embedding.

        Args:
            text: The text content to segment
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            Result[List[str]]: Success with list of text chunks or failure
        """
        pass

    @abstractmethod
    def segment_by_paragraphs(
        self,
        text: str,
        max_chunk_size: int = 1000
    ) -> Result[List[str]]:
        """
        Segment text by paragraphs, combining smaller paragraphs to reach target size.

        Args:
            text: The text content to segment
            max_chunk_size: Maximum size for each chunk in characters

        Returns:
            Result[List[str]]: Success with list of text chunks or failure
        """
        pass

    @abstractmethod
    def segment_by_sentences(
        self,
        text: str,
        max_chunk_size: int = 1000
    ) -> Result[List[str]]:
        """
        Segment text by sentences, combining sentences to reach target size.

        Args:
            text: The text content to segment
            max_chunk_size: Maximum size for each chunk in characters

        Returns:
            Result[List[str]]: Success with list of text chunks or failure
        """
        pass
