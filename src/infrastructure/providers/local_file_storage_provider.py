"""Local file storage provider implementation."""
import os
import shutil
from pathlib import Path

from ...core.interfaces.providers.i_file_storage_provider import IFileStorageProvider
from ...core.results.result import Result


class LocalFileStorageProvider(IFileStorageProvider):
    """
    Local filesystem implementation of IFileStorageProvider.

    Stores files in a local directory structure.
    """

    def __init__(self, base_path: str = "./storage"):
        """
        Initialize the local file storage provider.

        Args:
            base_path: Base directory for file storage (default: ./storage)
        """
        self.base_path = Path(base_path)
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure the base storage directory exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # If we can't create the base directory, we'll fail on first operation
            pass

    def store_file(self, content: bytes, destination: str) -> Result[str]:
        """
        Store a file to the local filesystem.

        Args:
            content: Raw file content as bytes
            destination: Destination path relative to base_path

        Returns:
            Result[str]: Success with the absolute stored file path or failure
        """
        try:
            # Create full path
            full_path = self.base_path / destination

            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, 'wb') as f:
                f.write(content)

            # Return absolute path as string
            return Result.success(str(full_path.absolute()))

        except Exception as e:
            return Result.failure(f"Failed to store file: {str(e)}")

    def retrieve_file(self, path: str) -> Result[bytes]:
        """
        Retrieve file content from local filesystem.

        Args:
            path: Absolute or relative path to the file

        Returns:
            Result[bytes]: Success with file content or failure
        """
        try:
            file_path = Path(path)

            # If path is not absolute, assume it's relative to base_path
            if not file_path.is_absolute():
                file_path = self.base_path / path

            if not file_path.exists():
                return Result.failure(f"File not found: {path}")

            with open(file_path, 'rb') as f:
                content = f.read()

            return Result.success(content)

        except Exception as e:
            return Result.failure(f"Failed to retrieve file: {str(e)}")

    def delete_file(self, path: str) -> Result[None]:
        """
        Delete a file from local filesystem.

        Args:
            path: Absolute or relative path to the file to delete

        Returns:
            Result[None]: Success or failure
        """
        try:
            file_path = Path(path)

            # If path is not absolute, assume it's relative to base_path
            if not file_path.is_absolute():
                file_path = self.base_path / path

            if not file_path.exists():
                return Result.failure(f"File not found: {path}")

            file_path.unlink()

            # Try to clean up empty parent directories
            try:
                parent = file_path.parent
                while parent != self.base_path and parent.exists():
                    if not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
                    else:
                        break
            except:
                # Ignore cleanup errors
                pass

            return Result.success(None)

        except Exception as e:
            return Result.failure(f"Failed to delete file: {str(e)}")

    def get_file_size(self, path: str) -> Result[int]:
        """
        Get the size of a file in bytes.

        Args:
            path: Absolute or relative path to the file

        Returns:
            Result[int]: Success with file size in bytes or failure
        """
        try:
            file_path = Path(path)

            # If path is not absolute, assume it's relative to base_path
            if not file_path.is_absolute():
                file_path = self.base_path / path

            if not file_path.exists():
                return Result.failure(f"File not found: {path}")

            size = file_path.stat().st_size
            return Result.success(size)

        except Exception as e:
            return Result.failure(f"Failed to get file size: {str(e)}")

    def file_exists(self, path: str) -> Result[bool]:
        """
        Check if a file exists at the specified path.

        Args:
            path: Absolute or relative path to check

        Returns:
            Result[bool]: Success with True/False or failure
        """
        try:
            file_path = Path(path)

            # If path is not absolute, assume it's relative to base_path
            if not file_path.is_absolute():
                file_path = self.base_path / path

            exists = file_path.exists() and file_path.is_file()
            return Result.success(exists)

        except Exception as e:
            return Result.failure(f"Failed to check file existence: {str(e)}")
