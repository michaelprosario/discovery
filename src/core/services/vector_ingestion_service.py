"""Vector ingestion service - orchestrates vector database ingestion operations."""
from typing import List
from uuid import UUID

from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..interfaces.repositories.i_source_repository import ISourceRepository
from ..interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ..interfaces.providers.i_content_segmenter import IContentSegmenter
from ..commands.vector_commands import (
    IngestNotebookCommand,
    DeleteNotebookVectorsCommand
)
from ..results.result import Result


class VectorIngestionService:
    """
    Domain service for managing vector database ingestion operations.

    This service orchestrates the ingestion of notebook content into the vector database.
    It depends on repository and provider abstractions (DIP).
    """

    def __init__(
        self,
        notebook_repository: INotebookRepository,
        source_repository: ISourceRepository,
        vector_db_provider: IVectorDatabaseProvider,
        content_segmenter: IContentSegmenter
    ):
        """
        Initialize the service with its dependencies.

        Args:
            notebook_repository: Repository abstraction for notebook access
            source_repository: Repository abstraction for source access
            vector_db_provider: Provider for vector database operations
            content_segmenter: Provider for content segmentation
        """
        self._notebook_repository = notebook_repository
        self._source_repository = source_repository
        self._vector_db_provider = vector_db_provider
        self._content_segmenter = content_segmenter

    def ingest_notebook(self, command: IngestNotebookCommand) -> Result[int]:
        """
        Ingest a notebook and all its sources into the vector database.

        Business Logic:
        - Validates notebook exists
        - Creates collection if not exists
        - Retrieves all sources for the notebook
        - For each source with extracted_text:
          - Segments the text into chunks
          - Creates document entries with metadata
          - Upserts into vector database
        - Returns count of chunks ingested

        Args:
            command: IngestNotebookCommand with notebook details

        Returns:
            Result[int]: Success with count of chunks ingested or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        notebook = notebook_result.value

        # Create collection if not exists
        collection_result = self._vector_db_provider.create_collection_if_not_exists(
            command.collection_name
        )
        if collection_result.is_failure:
            return Result.failure(f"Failed to create collection: {collection_result.error}")

        # If force reingest, delete existing vectors for this notebook
        if command.force_reingest:
            delete_result = self._vector_db_provider.delete_documents(
                command.collection_name,
                {"notebook_id": str(command.notebook_id)}
            )
            if delete_result.is_failure:
                return Result.failure(f"Failed to delete existing vectors: {delete_result.error}")

        # Get all sources for the notebook
        from ..queries.source_queries import ListSourcesQuery

        list_query = ListSourcesQuery(notebook_id=command.notebook_id)
        sources_result = self._source_repository.get_by_notebook(
            command.notebook_id,
            list_query
        )

        if sources_result.is_failure:
            return Result.failure(f"Failed to retrieve sources: {sources_result.error}")

        sources = sources_result.value
        total_chunks = 0

        # Process each source
        for source in sources:
            # Skip if no extracted text
            if not source.extracted_text or not source.extracted_text.strip():
                continue

            # Segment the text
            segment_result = self._content_segmenter.segment(
                source.extracted_text,
                chunk_size=command.chunk_size,
                overlap=command.overlap
            )

            if segment_result.is_failure:
                # Log warning but continue with other sources
                continue

            chunks = segment_result.value

            # Create documents for each chunk
            documents = []
            for idx, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "metadata": {
                        "notebook_id": str(command.notebook_id),
                        "source_id": str(source.id),
                        "chunk_index": idx,
                        "source_name": source.name
                    }
                }
                documents.append(doc)

            # Upsert documents to vector database
            if documents:
                upsert_result = self._vector_db_provider.upsert_documents(
                    command.collection_name,
                    documents
                )

                if upsert_result.is_failure:
                    return Result.failure(
                        f"Failed to upsert documents for source {source.name}: {upsert_result.error}"
                    )

                total_chunks += len(documents)

        return Result.success(total_chunks)

    def delete_notebook_vectors(self, command: DeleteNotebookVectorsCommand) -> Result[int]:
        """
        Delete all vectors associated with a notebook.

        Args:
            command: DeleteNotebookVectorsCommand with notebook ID

        Returns:
            Result[int]: Success with count of deleted vectors or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {command.notebook_id} not found")

        # Delete vectors
        delete_result = self._vector_db_provider.delete_documents(
            command.collection_name,
            {"notebook_id": str(command.notebook_id)}
        )

        if delete_result.is_failure:
            return Result.failure(f"Failed to delete vectors: {delete_result.error}")

        return Result.success(delete_result.value)
