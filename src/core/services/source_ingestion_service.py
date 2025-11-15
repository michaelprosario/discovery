"""Source ingestion service - orchestrates source import and processing operations."""
from typing import List
from uuid import UUID
import os

from ..entities.source import Source
from ..entities.notebook import Notebook
from ..interfaces.repositories.i_source_repository import ISourceRepository
from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..interfaces.providers.i_file_storage_provider import IFileStorageProvider
from ..interfaces.providers.i_content_extraction_provider import IContentExtractionProvider
from ..interfaces.providers.i_web_fetch_provider import IWebFetchProvider
from ..commands.source_commands import (
    ImportFileSourceCommand,
    ImportUrlSourceCommand,
    ImportTextSourceCommand,
    DeleteSourceCommand,
    RestoreSourceCommand,
    RenameSourceCommand,
    ExtractContentCommand
)
from ..queries.source_queries import (
    GetSourceByIdQuery,
    ListSourcesQuery,
    CheckSourceExistsQuery,
    CheckDuplicateSourceQuery,
    GetSourceCountQuery,
    SourceSummary
)
from ..results.result import Result
from ..results.validation_error import ValidationError


class SourceIngestionService:
    """
    Domain service for managing source lifecycle operations.

    This service orchestrates operations for importing and processing sources
    from various origins. It depends on repository and provider abstractions (DIP).
    """

    def __init__(
        self,
        source_repository: ISourceRepository,
        notebook_repository: INotebookRepository,
        file_storage_provider: IFileStorageProvider,
        content_extraction_provider: IContentExtractionProvider,
        web_fetch_provider: IWebFetchProvider
    ):
        """
        Initialize the service with its dependencies.

        Args:
            source_repository: Repository abstraction for source persistence
            notebook_repository: Repository abstraction for notebook validation
            file_storage_provider: Provider for file storage operations
            content_extraction_provider: Provider for text extraction
            web_fetch_provider: Provider for web content fetching
        """
        self._source_repository = source_repository
        self._notebook_repository = notebook_repository
        self._file_storage_provider = file_storage_provider
        self._content_extraction_provider = content_extraction_provider
        self._web_fetch_provider = web_fetch_provider

    def import_file_source(self, command: ImportFileSourceCommand) -> Result[Source]:
        """
        Import a file source into a notebook.

        Business Logic:
        - Validates notebook exists
        - Validates file type supported
        - Validates file size within limits
        - Calculates content hash
        - Checks for duplicates (same hash in notebook)
        - Stores original file via IFileStorageProvider
        - Extracts text via IContentExtractionProvider
        - Creates Source entity
        - Persists via repository
        - Updates notebook source count

        Args:
            command: ImportFileSourceCommand with file details

        Returns:
            Result[Source]: Success with created source or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = notebook_result.value

        # Get file size
        file_size = len(command.file_content)

        # Create source entity (with validation)
        create_result = Source.create_file_source(
            notebook_id=command.notebook_id,
            name=command.file_name,
            file_type=command.file_type,
            file_size=file_size,
            content=command.file_content,
            metadata=command.metadata
        )

        if create_result.is_failure:
            return create_result

        source = create_result.value

        # Check for duplicates (same content hash in notebook)
        duplicate_result = self._source_repository.get_by_content_hash(
            command.notebook_id,
            source.content_hash
        )
        if duplicate_result.is_failure:
            return Result.failure(f"Failed to check for duplicates: {duplicate_result.error}")

        if duplicate_result.value is not None:
            return Result.validation_failure([
                ValidationError(
                    field="file_content",
                    message=f"A source with identical content already exists: '{duplicate_result.value.name}'",
                    code="DUPLICATE_CONTENT"
                )
            ])

        # Store file via provider
        storage_path = self._generate_storage_path(source)
        store_result = self._file_storage_provider.store_file(command.file_content, storage_path)
        if store_result.is_failure:
            return Result.failure(f"Failed to store file: {store_result.error}")

        source.file_path = store_result.value

        # Extract text content
        extract_result = self._content_extraction_provider.extract_text(
            source.file_path,
            command.file_type
        )
        if extract_result.is_failure:
            # Log warning but don't fail - extraction is optional
            source.extracted_text = ""
        else:
            source.extracted_text = extract_result.value

        # Persist source
        add_result = self._source_repository.add(source)
        if add_result.is_failure:
            # Try to cleanup stored file
            self._file_storage_provider.delete_file(source.file_path)
            return Result.failure(f"Failed to save source: {add_result.error}")

        # Update notebook source count
        notebook.increment_source_count()
        self._notebook_repository.update(notebook)

        return Result.success(add_result.value)

    def import_url_source(self, command: ImportUrlSourceCommand) -> Result[Source]:
        """
        Import a URL source into a notebook.

        Business Logic:
        - Validates notebook exists
        - Validates URL format
        - Fetches content via IWebFetchProvider
        - Extracts main content (remove ads/navigation)
        - Calculates content hash
        - Checks for duplicates
        - Creates Source entity with URL metadata
        - Persists via repository
        - Updates notebook source count

        Args:
            command: ImportUrlSourceCommand with URL details

        Returns:
            Result[Source]: Success with created source or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = notebook_result.value

        # Fetch content from URL using enhanced retry logic for better success rates
        if hasattr(self._web_fetch_provider, 'fetch_url_safe'):
            fetch_result = self._web_fetch_provider.fetch_url_safe(command.url)
        elif hasattr(self._web_fetch_provider, 'fetch_with_retry'):
            fetch_result = self._web_fetch_provider.fetch_with_retry(command.url)
        else:
            fetch_result = self._web_fetch_provider.fetch_url(command.url)
        if fetch_result.is_failure:
            return Result.failure(f"Failed to fetch URL: {fetch_result.error}")

        web_content = fetch_result.value

        # Determine name (use provided title or extracted title)
        name = command.title if command.title else web_content.title
        if not name:
            name = command.url  # Fallback to URL

        # Create source entity (with validation)
        create_result = Source.create_url_source(
            notebook_id=command.notebook_id,
            name=name,
            url=command.url,
            content=web_content.text,
            metadata=web_content.metadata
        )

        if create_result.is_failure:
            return create_result

        source = create_result.value

        # Set extracted text
        source.extracted_text = web_content.text

        # Check for duplicates (same content hash in notebook)
        duplicate_result = self._source_repository.get_by_content_hash(
            command.notebook_id,
            source.content_hash
        )
        if duplicate_result.is_failure:
            return Result.failure(f"Failed to check for duplicates: {duplicate_result.error}")

        if duplicate_result.value is not None:
            return Result.validation_failure([
                ValidationError(
                    field="url",
                    message=f"A source with identical content already exists: '{duplicate_result.value.name}'",
                    code="DUPLICATE_CONTENT"
                )
            ])

        # Persist source
        add_result = self._source_repository.add(source)
        if add_result.is_failure:
            return Result.failure(f"Failed to save source: {add_result.error}")

        # Update notebook source count
        notebook.increment_source_count()
        self._notebook_repository.update(notebook)

        return Result.success(add_result.value)

    def import_text_source(self, command: ImportTextSourceCommand) -> Result[Source]:
        """
        Import a text source into a notebook.

        Business Logic:
        - Validates notebook exists
        - Validates text content (not empty, within length limits)
        - Calculates content hash
        - Checks for duplicates (same hash in notebook)
        - Creates Source entity with TEXT type
        - Stores text directly in extracted_text field
        - Persists via repository
        - Updates notebook source count

        Args:
            command: ImportTextSourceCommand with text details

        Returns:
            Result[Source]: Success with created source or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = notebook_result.value

        # Create source entity (with validation)
        create_result = Source.create_text_source(
            notebook_id=command.notebook_id,
            name=command.title,
            content=command.content,
            metadata=command.metadata
        )

        if create_result.is_failure:
            return create_result

        source = create_result.value

        # Check for duplicates (same content hash in notebook)
        duplicate_result = self._source_repository.get_by_content_hash(
            command.notebook_id,
            source.content_hash
        )
        if duplicate_result.is_failure:
            return Result.failure(f"Failed to check for duplicates: {duplicate_result.error}")

        if duplicate_result.value is not None:
            return Result.validation_failure([
                ValidationError(
                    field="content",
                    message=f"A source with identical content already exists: '{duplicate_result.value.name}'",
                    code="DUPLICATE_CONTENT"
                )
            ])

        # Persist source
        add_result = self._source_repository.add(source)
        if add_result.is_failure:
            return Result.failure(f"Failed to save source: {add_result.error}")

        # Update notebook source count
        notebook.increment_source_count()
        self._notebook_repository.update(notebook)

        return Result.success(add_result.value)

    def delete_source(self, command: DeleteSourceCommand) -> Result[None]:
        """
        Delete a source (soft delete).

        Business Logic:
        - Validates source exists and belongs to notebook
        - Checks if used in active output generation (to be implemented)
        - Soft deletes source
        - Updates notebook's updated_at timestamp and source count

        Args:
            command: DeleteSourceCommand with source and notebook IDs

        Returns:
            Result[None]: Success or failure
        """
        # Get source
        get_result = self._source_repository.get_by_id(command.source_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve source: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Source with ID {command.source_id} not found")

        source = get_result.value

        # Validate source belongs to notebook
        if source.notebook_id != command.notebook_id:
            return Result.failure(f"Source does not belong to notebook {command.notebook_id}")

        # Check if already deleted
        if source.is_deleted():
            return Result.failure("Source is already deleted")

        # TODO: Check if used in active output generation

        # Soft delete source
        delete_result = source.soft_delete()
        if delete_result.is_failure:
            return delete_result

        # Update source in repository
        update_result = self._source_repository.update(source)
        if update_result.is_failure:
            return Result.failure(f"Failed to delete source: {update_result.error}")

        # Update notebook
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_success and notebook_result.value:
            notebook = notebook_result.value
            notebook.decrement_source_count()
            notebook.touch()
            self._notebook_repository.update(notebook)

        return Result.success(None)

    def restore_source(self, command: RestoreSourceCommand) -> Result[Source]:
        """
        Restore a soft-deleted source.

        Args:
            command: RestoreSourceCommand with source and notebook IDs

        Returns:
            Result[Source]: Success with restored source or failure
        """
        # Get source (including deleted)
        get_result = self._source_repository.get_by_id(command.source_id, include_deleted=True)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve source: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Source with ID {command.source_id} not found")

        source = get_result.value

        # Validate source belongs to notebook
        if source.notebook_id != command.notebook_id:
            return Result.failure(f"Source does not belong to notebook {command.notebook_id}")

        # Restore source
        restore_result = source.restore()
        if restore_result.is_failure:
            return restore_result

        # Update source in repository
        update_result = self._source_repository.update(source)
        if update_result.is_failure:
            return Result.failure(f"Failed to restore source: {update_result.error}")

        # Update notebook
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_success and notebook_result.value:
            notebook = notebook_result.value
            notebook.increment_source_count()
            notebook.touch()
            self._notebook_repository.update(notebook)

        return Result.success(update_result.value)

    def rename_source(self, command: RenameSourceCommand) -> Result[Source]:
        """
        Rename a source.

        Args:
            command: RenameSourceCommand with source ID, notebook ID, and new name

        Returns:
            Result[Source]: Success with renamed source or failure
        """
        # Get source
        get_result = self._source_repository.get_by_id(command.source_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve source: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Source with ID {command.source_id} not found")

        source = get_result.value

        # Validate source belongs to notebook
        if source.notebook_id != command.notebook_id:
            return Result.failure(f"Source does not belong to notebook {command.notebook_id}")

        # Rename source
        rename_result = source.rename(command.new_name)
        if rename_result.is_failure:
            return rename_result

        # Update source in repository
        update_result = self._source_repository.update(source)
        if update_result.is_failure:
            return Result.failure(f"Failed to rename source: {update_result.error}")

        return Result.success(update_result.value)

    def extract_content(self, command: ExtractContentCommand) -> Result[Source]:
        """
        Extract content from a source.

        Business Logic:
        - Validates source exists and belongs to notebook
        - Determines extraction strategy based on file type
        - Delegates to IContentExtractionProvider
        - Updates source extracted_text
        - Handles extraction failures gracefully

        Args:
            command: ExtractContentCommand with source and notebook IDs

        Returns:
            Result[Source]: Success with updated source or failure
        """
        # Get source
        get_result = self._source_repository.get_by_id(command.source_id)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve source: {get_result.error}")

        if get_result.value is None:
            return Result.failure(f"Source with ID {command.source_id} not found")

        source = get_result.value

        # Validate source belongs to notebook
        if source.notebook_id != command.notebook_id:
            return Result.failure(f"Source does not belong to notebook {command.notebook_id}")

        # Check if already extracted and not forcing re-extract
        if source.extracted_text and not command.force_reextract:
            return Result.success(source)

        # Only file sources can have content extracted
        if source.source_type.value != "file":
            return Result.failure("Content extraction is only supported for file sources")

        if source.file_type is None:
            return Result.failure("Source file type is not set")

        # Extract content
        extract_result = self._content_extraction_provider.extract_text(
            source.file_path,
            source.file_type
        )
        if extract_result.is_failure:
            return Result.failure(f"Failed to extract content: {extract_result.error}")

        # Update source with extracted text
        source.update_extracted_text(extract_result.value)
        update_result = self._source_repository.update(source)
        
        if update_result.is_failure:
            return Result.failure(f"Failed to update source: {update_result.error}")

        return Result.success(update_result.value)

    def get_source_by_id(self, query: GetSourceByIdQuery) -> Result[Source]:
        """
        Get a source by its ID.

        Args:
            query: GetSourceByIdQuery with source ID

        Returns:
            Result[Source]: Success with source or failure if not found
        """
        result = self._source_repository.get_by_id(query.source_id, query.include_deleted)

        if result.is_failure:
            return Result.failure(f"Failed to retrieve source: {result.error}")

        if result.value is None:
            return Result.failure(f"Source with ID {query.source_id} not found")

        return Result.success(result.value)

    def list_sources(self, query: ListSourcesQuery) -> Result[List[SourceSummary]]:
        """
        List sources in a notebook with optional filtering and sorting.

        Args:
            query: ListSourcesQuery with filter and sort parameters

        Returns:
            Result[List[SourceSummary]]: Success with source summaries or failure
        """
        # Get sources from repository
        get_result = self._source_repository.get_by_notebook(query.notebook_id, query)
        if get_result.is_failure:
            return Result.failure(f"Failed to retrieve sources: {get_result.error}")

        sources = get_result.value

        # Convert to summaries
        summaries = [SourceSummary.from_source(src) for src in sources]

        return Result.success(summaries)

    def check_exists(self, query: CheckSourceExistsQuery) -> Result[bool]:
        """
        Check if a source exists.

        Args:
            query: CheckSourceExistsQuery with source ID

        Returns:
            Result[bool]: Success with True/False or failure
        """
        return self._source_repository.exists(query.source_id, query.include_deleted)

    def check_duplicate(self, query: CheckDuplicateSourceQuery) -> Result[bool]:
        """
        Check if a source with the same content hash exists in a notebook.

        Args:
            query: CheckDuplicateSourceQuery with notebook ID and content hash

        Returns:
            Result[bool]: Success with True if duplicate exists, False otherwise, or failure
        """
        result = self._source_repository.get_by_content_hash(
            query.notebook_id,
            query.content_hash
        )
        if result.is_failure:
            return Result.failure(f"Failed to check for duplicate: {result.error}")

        return Result.success(result.value is not None)

    def get_count(self, query: GetSourceCountQuery) -> Result[int]:
        """
        Get count of sources in a notebook.

        Args:
            query: GetSourceCountQuery with notebook ID

        Returns:
            Result[int]: Success with count or failure
        """
        return self._source_repository.count(query.notebook_id, query.include_deleted)

    def _generate_storage_path(self, source: Source) -> str:
        """
        Generate a storage path for a source file.

        Args:
            source: The source entity

        Returns:
            str: Storage path
        """
        # Create path: notebooks/{notebook_id}/sources/{source_id}.{extension}
        extension = source.file_type.value if source.file_type else "bin"
        return f"notebooks/{source.notebook_id}/sources/{source.id}.{extension}"
