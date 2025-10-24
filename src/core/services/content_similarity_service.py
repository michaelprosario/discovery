"""Content similarity service - orchestrates similarity search operations."""
from typing import List

from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ..queries.vector_queries import (
    SimilaritySearchQuery,
    SimilaritySearchResult,
    GetVectorCountQuery
)
from ..results.result import Result


class ContentSimilarityService:
    """
    Domain service for managing content similarity search operations.

    This service orchestrates similarity searches in the vector database.
    It depends on repository and provider abstractions (DIP).
    """

    def __init__(
        self,
        notebook_repository: INotebookRepository,
        vector_db_provider: IVectorDatabaseProvider
    ):
        """
        Initialize the service with its dependencies.

        Args:
            notebook_repository: Repository abstraction for notebook access
            vector_db_provider: Provider for vector database operations
        """
        self._notebook_repository = notebook_repository
        self._vector_db_provider = vector_db_provider

    def search_similar_content(
        self,
        query: SimilaritySearchQuery
    ) -> Result[List[SimilaritySearchResult]]:
        """
        Search for similar content within a notebook.

        Business Logic:
        - Validates notebook exists
        - Performs similarity search in vector database
        - Filters results to only include content from the specified notebook
        - Returns formatted results

        Args:
            query: SimilaritySearchQuery with search parameters

        Returns:
            Result[List[SimilaritySearchResult]]: Success with search results or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(query.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {query.notebook_id} not found")

        # Perform similarity search with notebook filter
        search_result = self._vector_db_provider.query_similarity(
            collection_name=query.collection_name,
            query_text=query.query_text,
            limit=query.limit,
            filters={"notebook_id": str(query.notebook_id)}
        )

        if search_result.is_failure:
            return Result.failure(f"Failed to search similar content: {search_result.error}")

        # Convert results to domain objects
        results = [
            SimilaritySearchResult.from_vector_result(result)
            for result in search_result.value
        ]

        return Result.success(results)

    def get_vector_count(self, query: GetVectorCountQuery) -> Result[int]:
        """
        Get count of vectors for a notebook.

        Args:
            query: GetVectorCountQuery with notebook ID

        Returns:
            Result[int]: Success with count or failure
        """
        # Validate notebook exists
        notebook_result = self._notebook_repository.get_by_id(query.notebook_id)
        if notebook_result.is_failure:
            return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

        if notebook_result.value is None:
            return Result.failure(f"Notebook with ID {query.notebook_id} not found")

        # Get count from vector database
        count_result = self._vector_db_provider.get_document_count(
            collection_name=query.collection_name,
            filters={"notebook_id": str(query.notebook_id)}
        )

        if count_result.is_failure:
            return Result.failure(f"Failed to get vector count: {count_result.error}")

        return Result.success(count_result.value)
