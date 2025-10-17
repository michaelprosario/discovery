"""File storage provider interface - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod

from ...results.result import Result


class IFileStorageProvider(ABC):
    """
    Interface for file storage operations.

    This interface abstracts file system operations following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations (local filesystem, cloud storage, etc.).
    """

    @abstractmethod
    def store_file(self, content: bytes, destination: str) -> Result[str]:
        """
        Store a file to the specified destination.

        Args:
            content: Raw file content as bytes
            destination: Destination path where file should be stored

        Returns:
            Result[str]: Success with the stored file path or failure
        """
        pass

    @abstractmethod
    def retrieve_file(self, path: str) -> Result[bytes]:
        """
        Retrieve file content from storage.

        Args:
            path: Path to the file

        Returns:
            Result[bytes]: Success with file content or failure
        """
        pass

    @abstractmethod
    def delete_file(self, path: str) -> Result[None]:
        """
        Delete a file from storage.

        Args:
            path: Path to the file to delete

        Returns:
            Result[None]: Success or failure
        """
        pass

    @abstractmethod
    def get_file_size(self, path: str) -> Result[int]:
        """
        Get the size of a file in bytes.

        Args:
            path: Path to the file

        Returns:
            Result[int]: Success with file size in bytes or failure
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> Result[bool]:
        """
        Check if a file exists at the specified path.

        Args:
            path: Path to check

        Returns:
            Result[bool]: Success with True/False or failure
        """
        pass
