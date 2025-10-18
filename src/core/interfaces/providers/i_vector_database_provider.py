"""Vector database provider interface - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ...results.result import Result


class IVectorDatabaseProvider(ABC):
    """
    Interface for vector database operations.

    This interface abstracts vector database operations following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations using specific vector databases.
    """

    @abstractmethod
    def create_collection_if_not_exists(
        self,
        collection_name: str,
        properties: Optional[List[Dict[str, Any]]] = None
    ) -> Result[None]:
        """
        Create a collection (schema/class) if it doesn't already exist.

        Args:
            collection_name: Name of the collection/class to create
            properties: Optional list of property definitions for the collection

        Returns:
            Result[None]: Success or failure
        """
        pass

    @abstractmethod
    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> Result[List[str]]:
        """
        Add or update documents (text chunks with embeddings) in the vector database.

        Args:
            collection_name: Name of the collection/class
            documents: List of documents to upsert. Each document should contain:
                - text: The text content
                - metadata: Dict of additional metadata (notebook_id, source_id, etc.)
                - id: Optional document ID for updates

        Returns:
            Result[List[str]]: Success with list of document IDs or failure
        """
        pass

    @abstractmethod
    def query_similarity(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[Dict[str, Any]]]:
        """
        Perform a similarity search using text query.

        Args:
            collection_name: Name of the collection/class to search
            query_text: The text query to search for similar documents
            limit: Maximum number of results to return
            filters: Optional filters to apply (e.g., notebook_id, source_id)

        Returns:
            Result[List[Dict[str, Any]]]: Success with list of matching documents or failure.
                Each document contains: id, text, metadata, distance/certainty score
        """
        pass

    @abstractmethod
    def delete_documents(
        self,
        collection_name: str,
        filters: Dict[str, Any]
    ) -> Result[int]:
        """
        Delete documents matching the given filters.

        Args:
            collection_name: Name of the collection/class
            filters: Filters to identify documents to delete (e.g., notebook_id, source_id)

        Returns:
            Result[int]: Success with count of deleted documents or failure
        """
        pass

    @abstractmethod
    def collection_exists(self, collection_name: str) -> Result[bool]:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection/class

        Returns:
            Result[bool]: Success with True/False or failure
        """
        pass

    @abstractmethod
    def get_document_count(
        self,
        collection_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[int]:
        """
        Get count of documents in a collection.

        Args:
            collection_name: Name of the collection/class
            filters: Optional filters to apply

        Returns:
            Result[int]: Success with document count or failure
        """
        pass
