"""Simple content segmenter implementation."""
from typing import List
import re

from ...core.interfaces.providers.i_content_segmenter import IContentSegmenter
from ...core.results.result import Result


class SimpleContentSegmenter(IContentSegmenter):
    """
    Concrete implementation of IContentSegmenter with straightforward text-splitting strategies.

    This segmenter provides multiple strategies for breaking down text into chunks
    suitable for embedding and vector search.
    """

    def segment(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> Result[List[str]]:
        """
        Segment text into overlapping chunks of approximately equal size.

        This method uses a sliding window approach to create chunks with overlap,
        ensuring context is preserved between chunks.

        Args:
            text: The text content to segment
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            Result[List[str]]: Success with list of text chunks or failure
        """
        try:
            if not text or not text.strip():
                return Result.failure("Cannot segment empty text")

            if chunk_size <= 0:
                return Result.failure("Chunk size must be positive")

            if overlap < 0:
                return Result.failure("Overlap cannot be negative")

            if overlap >= chunk_size:
                return Result.failure("Overlap must be less than chunk size")

            text = text.strip()
            chunks = []

            # If text is shorter than chunk size, return as single chunk
            if len(text) <= chunk_size:
                return Result.success([text])

            # Create overlapping chunks
            start = 0
            while start < len(text):
                end = start + chunk_size

                # If this is not the last chunk, try to break at a sentence or word boundary
                if end < len(text):
                    # Look for sentence boundaries (. ! ?) within last 20% of chunk
                    boundary_search_start = end - int(chunk_size * 0.2)
                    boundary_text = text[boundary_search_start:end]

                    # Try to find sentence boundary
                    sentence_match = re.search(r'[.!?]\s', boundary_text)
                    if sentence_match:
                        end = boundary_search_start + sentence_match.end()
                    else:
                        # Try to find word boundary
                        word_match = re.search(r'\s', boundary_text[::-1])
                        if word_match:
                            end = end - word_match.start()

                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)

                # Move start position (with overlap)
                start = end - overlap

                # Prevent infinite loop
                if start <= chunks[-1] if chunks else 0:
                    start = end

            return Result.success(chunks)

        except Exception as e:
            return Result.failure(f"Failed to segment text: {str(e)}")

    def segment_by_paragraphs(
        self,
        text: str,
        max_chunk_size: int = 1000
    ) -> Result[List[str]]:
        """
        Segment text by paragraphs, combining smaller paragraphs to reach target size.

        This method preserves paragraph boundaries while ensuring chunks don't exceed
        the maximum size. It's ideal for content with clear paragraph structure.

        Args:
            text: The text content to segment
            max_chunk_size: Maximum size for each chunk in characters

        Returns:
            Result[List[str]]: Success with list of text chunks or failure
        """
        try:
            if not text or not text.strip():
                return Result.failure("Cannot segment empty text")

            if max_chunk_size <= 0:
                return Result.failure("Max chunk size must be positive")

            text = text.strip()

            # Split by paragraphs (double newline or single newline)
            paragraphs = re.split(r'\n\s*\n|\n', text)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

            if not paragraphs:
                return Result.failure("No paragraphs found in text")

            chunks = []
            current_chunk = []
            current_size = 0

            for paragraph in paragraphs:
                paragraph_size = len(paragraph)

                # If single paragraph exceeds max size, split it using basic segmentation
                if paragraph_size > max_chunk_size:
                    # Flush current chunk if not empty
                    if current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = []
                        current_size = 0

                    # Split large paragraph
                    split_result = self.segment(paragraph, max_chunk_size, 100)
                    if split_result.is_success:
                        chunks.extend(split_result.value)
                    continue

                # If adding this paragraph would exceed max size, start new chunk
                if current_size + paragraph_size + 2 > max_chunk_size and current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = [paragraph]
                    current_size = paragraph_size
                else:
                    current_chunk.append(paragraph)
                    current_size += paragraph_size + (2 if current_chunk else 0)

            # Add remaining chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))

            return Result.success(chunks)

        except Exception as e:
            return Result.failure(f"Failed to segment by paragraphs: {str(e)}")

    def segment_by_sentences(
        self,
        text: str,
        max_chunk_size: int = 1000
    ) -> Result[List[str]]:
        """
        Segment text by sentences, combining sentences to reach target size.

        This method preserves sentence boundaries while ensuring chunks don't exceed
        the maximum size. It's ideal for maintaining semantic coherence.

        Args:
            text: The text content to segment
            max_chunk_size: Maximum size for each chunk in characters

        Returns:
            Result[List[str]]: Success with list of text chunks or failure
        """
        try:
            if not text or not text.strip():
                return Result.failure("Cannot segment empty text")

            if max_chunk_size <= 0:
                return Result.failure("Max chunk size must be positive")

            text = text.strip()

            # Split by sentence boundaries (. ! ? followed by space or newline)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return Result.failure("No sentences found in text")

            chunks = []
            current_chunk = []
            current_size = 0

            for sentence in sentences:
                sentence_size = len(sentence)

                # If single sentence exceeds max size, split it using basic segmentation
                if sentence_size > max_chunk_size:
                    # Flush current chunk if not empty
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        current_size = 0

                    # Split large sentence
                    split_result = self.segment(sentence, max_chunk_size, 50)
                    if split_result.is_success:
                        chunks.extend(split_result.value)
                    continue

                # If adding this sentence would exceed max size, start new chunk
                if current_size + sentence_size + 1 > max_chunk_size and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_size = sentence_size
                else:
                    current_chunk.append(sentence)
                    current_size += sentence_size + (1 if current_chunk else 0)

            # Add remaining chunk
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            return Result.success(chunks)

        except Exception as e:
            return Result.failure(f"Failed to segment by sentences: {str(e)}")
