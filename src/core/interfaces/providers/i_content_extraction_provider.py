"""Content extraction provider interface - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod

from ...results.result import Result
from ...value_objects.enums import FileType


class IContentExtractionProvider(ABC):
    """
    Interface for extracting text content from various file formats.

    This interface abstracts content extraction operations following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations using appropriate libraries.
    """

    @abstractmethod
    def extract_text_from_pdf(self, file_path: str) -> Result[str]:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Result[str]: Success with extracted text or failure
        """
        pass

    @abstractmethod
    def extract_text_from_docx(self, file_path: str) -> Result[str]:
        """
        Extract text content from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Result[str]: Success with extracted text or failure
        """
        pass

    @abstractmethod
    def extract_text_from_doc(self, file_path: str) -> Result[str]:
        """
        Extract text content from a DOC file.

        Args:
            file_path: Path to the DOC file

        Returns:
            Result[str]: Success with extracted text or failure
        """
        pass

    @abstractmethod
    def extract_text_from_txt(self, file_path: str) -> Result[str]:
        """
        Extract text content from a plain text file.

        Args:
            file_path: Path to the text file

        Returns:
            Result[str]: Success with extracted text or failure
        """
        pass

    @abstractmethod
    def extract_text_from_markdown(self, file_path: str) -> Result[str]:
        """
        Extract text content from a Markdown file.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Result[str]: Success with extracted text or failure
        """
        pass

    def extract_text(self, file_path: str, file_type: FileType) -> Result[str]:
        """
        Extract text content based on file type.

        Args:
            file_path: Path to the file
            file_type: Type of the file

        Returns:
            Result[str]: Success with extracted text or failure
        """
        extraction_methods = {
            FileType.PDF: self.extract_text_from_pdf,
            FileType.DOCX: self.extract_text_from_docx,
            FileType.DOC: self.extract_text_from_doc,
            FileType.TXT: self.extract_text_from_txt,
            FileType.MD: self.extract_text_from_markdown,
        }

        method = extraction_methods.get(file_type)
        if method is None:
            return Result.failure(f"Unsupported file type: {file_type.value}")

        return method(file_path)
