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
            if self.api_key:
                # Cloud instance - use text2vec-weaviate (default cloud vectorizer)
                # This is the built-in vectorizer for Weaviate Cloud Serverless
                vectorizer_config = Configure.Vectorizer.text2vec_weaviate(
                    vectorize_collection_name=False
                )
            else:
                # Local instance with text2vec-transformers module
                vectorizer_config = Configure.Vectorizer.text2vec_transformers(
                    vectorize_collection_name=False
                )

            client.collections.create(
                name=collection_name,
                properties=weaviate_properties,
                vectorizer_config=vectorizer_config
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

            # Build filters if provided
            where_filter = None
            if filters:
                from weaviate.classes.query import Filter
                filter_conditions = []

                for key, value in filters.items():
                    filter_conditions.append(
                        Filter.by_property(key).equal(value)
                    )

                # Combine filters with AND
                if len(filter_conditions) == 1:
                    where_filter = filter_conditions[0]
                elif len(filter_conditions) > 1:
                    where_filter = filter_conditions[0]
                    for condition in filter_conditions[1:]:
                        where_filter = where_filter & condition

            # Execute query with filters and request metadata
            from weaviate.classes.query import MetadataQuery

            if where_filter:
                response = collection.query.near_text(
                    query=query_text,
                    limit=limit,
                    filters=where_filter,
                    return_metadata=MetadataQuery(distance=True, certainty=True)
                )
            else:
                response = collection.query.near_text(
                    query=query_text,
                    limit=limit,
                    return_metadata=MetadataQuery(distance=True, certainty=True)
                )

            # Format results
            results = []
            for obj in response.objects:
                # Get distance and certainty from metadata
                distance = obj.metadata.distance if hasattr(obj.metadata, 'distance') else None
                certainty = obj.metadata.certainty if hasattr(obj.metadata, 'certainty') else None

                # If certainty is None but distance exists, calculate it
                # Certainty = 1 - (distance / 2) for cosine distance
                if certainty is None and distance is not None:
                    certainty = 1.0 - (distance / 2.0)

                results.append({
                    "id": str(obj.uuid),
                    "text": obj.properties.get("text", ""),
                    "metadata": {
                        k: v for k, v in obj.properties.items() if k != "text"
                    },
                    "distance": distance,
                    "certainty": certainty
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
            
            # Check if collection exists first
            if not client.collections.exists(collection_name):
                return Result.success(0)
            
            collection = client.collections.get(collection_name)

            if filters:
                from weaviate.classes.query import Filter

                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(
                        Filter.by_property(key).equal(value)
                    )

                if len(filter_conditions) == 1:
                    combined = filter_conditions[0]
                else:
                    combined = filter_conditions[0]
                    for condition in filter_conditions[1:]:
                        combined = combined & condition

                # Use a simple query approach that works across Weaviate client versions
                try:
                    # Try the newer API first
                    response = collection.query.fetch_objects(
                        where=combined,
                        limit=10000  # Reasonable limit for counting
                    )
                    count = len(response.objects)
                except (AttributeError, TypeError) as e:
                    # Fall back to counting via near_text with empty query
                    try:
                        response = collection.query.near_text(
                            query="test",  # Use a simple query instead of empty
                            where=combined,
                            limit=10000
                        )
                        count = len(response.objects)
                    except Exception as e2:
                        # Debug: try to fetch all and filter manually
                        try:
                            all_response = collection.query.fetch_objects(limit=10000)
                            count = 0
                            for obj in all_response.objects:
                                match = True
                                for key, value in filters.items():
                                    if str(obj.properties.get(key, "")) != str(value):
                                        match = False
                                        break
                                if match:
                                    count += 1
                        except Exception:
                            count = 0
                    
            else:
                # Get total count without filter using aggregate
                try:
                    result = collection.aggregate.over_all(total_count=True)
                    count = result.total_count if hasattr(result, 'total_count') else 0
                except Exception:
                    # If aggregate fails, try to get objects and count them
                    try:
                        response = collection.query.fetch_objects(limit=10000)
                        count = len(response.objects)
                    except (AttributeError, TypeError):
                        # Final fallback
                        try:
                            response = collection.query.near_text(
                                query="",
                                limit=10000
                            )
                            count = len(response.objects)
                        except Exception:
                            count = 0

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
