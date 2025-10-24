"""Weaviate vector database provider implementation."""
from typing import List, Dict, Any, Optional
import uuid

from ...core.interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ...core.results.result import Result


class WeaviateVectorDatabaseProvider(IVectorDatabaseProvider):
    """
    Concrete implementation of IVectorDatabaseProvider using Weaviate.

    This provider uses the weaviate-client library to interact with a Weaviate instance.
    """

    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None):
        """
        Initialize the Weaviate provider.

        Args:
            url: URL of the Weaviate instance
            api_key: Optional API key for cloud instances
        """
        self.url = url
        self.api_key = api_key
        self._client = None

    def _get_client(self):
        """Get or create Weaviate client instance."""
        if self._client is None:
            try:
                import weaviate
                from weaviate.classes.init import Auth

                # Determine if this is a cloud or local instance
                if self.api_key:
                    # Cloud instance with API key authentication
                    self._client = weaviate.connect_to_weaviate_cloud(
                        cluster_url=self.url,
                        auth_credentials=Auth.api_key(self.api_key)
                    )
                else:
                    # Local instance without authentication
                    self._client = weaviate.connect_to_local(
                        host=self.url.replace("http://", "").replace("https://", "").split(":")[0],
                        port=int(self.url.split(":")[-1]) if ":" in self.url.split("//")[-1] else 8080
                    )
            except ImportError:
                raise ImportError(
                    "weaviate-client library not installed. "
                    "Install with: pip install weaviate-client"
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Weaviate at {self.url}: {str(e)}")

        return self._client

    def create_collection_if_not_exists(
        self,
        collection_name: str,
        properties: Optional[List[Dict[str, Any]]] = None
    ) -> Result[None]:
        """
        Create a collection (class) if it doesn't already exist.

        Args:
            collection_name: Name of the collection/class to create
            properties: Optional list of property definitions

        Returns:
            Result[None]: Success or failure
        """
        try:
            client = self._get_client()

            # Check if collection exists
            if client.collections.exists(collection_name):
                return Result.success(None)

            # Default properties if none provided
            if properties is None:
                properties = [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "description": "The text content of the chunk"
                    },
                    {
                        "name": "notebook_id",
                        "dataType": ["text"],
                        "description": "ID of the notebook this chunk belongs to"
                    },
                    {
                        "name": "source_id",
                        "dataType": ["text"],
                        "description": "ID of the source this chunk came from"
                    },
                    {
                        "name": "chunk_index",
                        "dataType": ["int"],
                        "description": "Index of this chunk within the source"
                    }
                ]

            # Create collection with appropriate vectorizer
            from weaviate.classes.config import Configure, Property, DataType

            # Convert properties to Weaviate Property objects
            weaviate_properties = []
            for prop in properties:
                data_type = DataType.TEXT
                if prop.get("dataType") == ["int"]:
                    data_type = DataType.INT
                elif prop.get("dataType") == ["number"]:
                    data_type = DataType.NUMBER

                weaviate_properties.append(
                    Property(
                        name=prop["name"],
                        data_type=data_type,
                        description=prop.get("description", "")
                    )
                )

            # Choose vectorizer based on instance type
            # Cloud instances use text2vec-openai, local uses text2vec-transformers
            if self.api_key:
                # Cloud instance - use none vectorizer (expects pre-computed vectors or external service)
                # Weaviate Cloud Serverless comes with text2vec-openai by default
                vectorizer_config = None  # Use default vectorizer
            else:
                # Local instance with text2vec-transformers module
                vectorizer_config = Configure.Vectorizer.text2vec_transformers(
                    vectorize_collection_name=False
                )

            if vectorizer_config:
                client.collections.create(
                    name=collection_name,
                    properties=weaviate_properties,
                    vectorizer_config=vectorizer_config
                )
            else:
                # Create without explicit vectorizer (use cluster default)
                client.collections.create(
                    name=collection_name,
                    properties=weaviate_properties
                )

            return Result.success(None)

        except Exception as e:
            return Result.failure(f"Failed to create collection: {str(e)}")

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> Result[List[str]]:
        """
        Add or update documents in the vector database.

        Args:
            collection_name: Name of the collection/class
            documents: List of documents to upsert

        Returns:
            Result[List[str]]: Success with list of document IDs or failure
        """
        try:
            client = self._get_client()
            collection = client.collections.get(collection_name)

            document_ids = []

            # Batch insert for efficiency
            with collection.batch.dynamic() as batch:
                for doc in documents:
                    # Generate ID if not provided
                    doc_id = doc.get("id", str(uuid.uuid4()))

                    # Extract text and metadata
                    text = doc.get("text", "")
                    metadata = doc.get("metadata", {})

                    # Prepare properties
                    properties = {
                        "text": text,
                        **metadata
                    }

                    # Add to batch
                    batch.add_object(
                        properties=properties,
                        uuid=doc_id
                    )

                    document_ids.append(doc_id)

            return Result.success(document_ids)

        except Exception as e:
            return Result.failure(f"Failed to upsert documents: {str(e)}")

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
            query_text: The text query
            limit: Maximum number of results
            filters: Optional filters to apply

        Returns:
            Result[List[Dict[str, Any]]]: Success with matching documents or failure
        """
        try:
            client = self._get_client()
            collection = client.collections.get(collection_name)

            # Build query
            query = collection.query.near_text(
                query=query_text,
                limit=limit
            )

            # Apply filters if provided
            if filters:
                from weaviate.classes.query import Filter
                filter_conditions = []

                for key, value in filters.items():
                    filter_conditions.append(
                        Filter.by_property(key).equal(value)
                    )

                # Combine filters with AND
                if len(filter_conditions) == 1:
                    query = query.where(filter_conditions[0])
                elif len(filter_conditions) > 1:
                    combined = filter_conditions[0]
                    for condition in filter_conditions[1:]:
                        combined = combined & condition
                    query = query.where(combined)

            # Execute query
            response = query

            # Format results
            results = []
            for obj in response.objects:
                results.append({
                    "id": str(obj.uuid),
                    "text": obj.properties.get("text", ""),
                    "metadata": {
                        k: v for k, v in obj.properties.items() if k != "text"
                    },
                    "distance": obj.metadata.distance if hasattr(obj.metadata, 'distance') else None,
                    "certainty": obj.metadata.certainty if hasattr(obj.metadata, 'certainty') else None
                })

            return Result.success(results)

        except Exception as e:
            return Result.failure(f"Failed to query similarity: {str(e)}")

    def delete_documents(
        self,
        collection_name: str,
        filters: Dict[str, Any]
    ) -> Result[int]:
        """
        Delete documents matching the given filters.

        Args:
            collection_name: Name of the collection/class
            filters: Filters to identify documents to delete

        Returns:
            Result[int]: Success with count of deleted documents or failure
        """
        try:
            client = self._get_client()
            collection = client.collections.get(collection_name)

            from weaviate.classes.query import Filter

            # Build filter
            filter_conditions = []
            for key, value in filters.items():
                filter_conditions.append(
                    Filter.by_property(key).equal(value)
                )

            # Combine filters with AND
            if len(filter_conditions) == 0:
                return Result.failure("No filters provided for deletion")

            combined = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined = combined & condition

            # Delete matching objects
            result = collection.data.delete_many(where=combined)

            return Result.success(result.successful if hasattr(result, 'successful') else 0)

        except Exception as e:
            return Result.failure(f"Failed to delete documents: {str(e)}")

    def collection_exists(self, collection_name: str) -> Result[bool]:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection/class

        Returns:
            Result[bool]: Success with True/False or failure
        """
        try:
            client = self._get_client()
            exists = client.collections.exists(collection_name)
            return Result.success(exists)

        except Exception as e:
            return Result.failure(f"Failed to check collection existence: {str(e)}")

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
        try:
            client = self._get_client()
            collection = client.collections.get(collection_name)

            if filters:
                from weaviate.classes.query import Filter

                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(
                        Filter.by_property(key).equal(value)
                    )

                combined = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    combined = combined & condition

                # Use aggregate with filter
                result = collection.aggregate.over_all(
                    where=combined,
                    total_count=True
                )
                count = result.total_count if hasattr(result, 'total_count') else 0
            else:
                # Get total count without filter
                result = collection.aggregate.over_all(total_count=True)
                count = result.total_count if hasattr(result, 'total_count') else 0

            return Result.success(count)

        except Exception as e:
            return Result.failure(f"Failed to get document count: {str(e)}")

    def close(self):
        """Close the Weaviate client connection."""
        if self._client is not None:
            try:
                self._client.close()
            except:
                pass
            self._client = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
