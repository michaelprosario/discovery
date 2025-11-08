"""ChromaDB vector database provider implementation."""
from typing import List, Dict, Any, Optional
import uuid

from ...core.interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ...core.results.result import Result


class ChromaVectorDatabaseProvider(IVectorDatabaseProvider):
    """
    Concrete implementation of IVectorDatabaseProvider using ChromaDB.

    This provider uses the chromadb library to interact with a ChromaDB instance.
    ChromaDB can run in-memory, locally persisted, or as a client-server setup.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Initialize the ChromaDB provider.

        Args:
            persist_directory: Directory to persist data (for local mode). If None, runs in-memory.
            host: Host for client-server mode. If provided, uses HTTP client.
            port: Port for client-server mode (default: 8000)
        """
        self.persist_directory = persist_directory
        self.host = host
        self.port = port or 8000
        self._client = None

    def _get_client(self):
        """Get or create ChromaDB client instance."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                if self.host:
                    # Client-server mode
                    self._client = chromadb.HttpClient(
                        host=self.host,
                        port=self.port
                    )
                elif self.persist_directory:
                    # Persistent local mode
                    self._client = chromadb.PersistentClient(
                        path=self.persist_directory
                    )
                else:
                    # In-memory mode
                    self._client = chromadb.Client()

            except ImportError:
                raise ImportError(
                    "chromadb library not installed. "
                    "Install with: pip install chromadb"
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to ChromaDB: {str(e)}")

        return self._client

    def create_collection_if_not_exists(
        self,
        collection_name: str,
        properties: Optional[List[Dict[str, Any]]] = None
    ) -> Result[None]:
        """
        Create a collection if it doesn't already exist.

        Args:
            collection_name: Name of the collection to create
            properties: Optional list of property definitions (not used by ChromaDB, kept for interface compatibility)

        Returns:
            Result[None]: Success or failure
        """
        try:
            client = self._get_client()

            # ChromaDB collection names must be between 3-63 characters and contain only alphanumeric, underscores, or hyphens
            # Convert to lowercase and ensure it meets requirements
            safe_collection_name = collection_name.lower()
            safe_collection_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in safe_collection_name)
            
            # Ensure minimum length
            if len(safe_collection_name) < 3:
                safe_collection_name = safe_collection_name + "_collection"

            # Get or create collection
            # ChromaDB automatically creates collections if they don't exist
            client.get_or_create_collection(
                name=safe_collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
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
            collection_name: Name of the collection
            documents: List of documents to upsert. Each document should contain:
                - text: The text content
                - metadata: Dict of additional metadata
                - id: Optional document ID

        Returns:
            Result[List[str]]: Success with list of document IDs or failure
        """
        try:
            client = self._get_client()
            
            # Normalize collection name
            safe_collection_name = collection_name.lower()
            safe_collection_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in safe_collection_name)
            if len(safe_collection_name) < 3:
                safe_collection_name = safe_collection_name + "_collection"

            collection = client.get_or_create_collection(
                name=safe_collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            document_ids = []
            texts = []
            metadatas = []

            for doc in documents:
                # Generate ID if not provided
                doc_id = doc.get("id", str(uuid.uuid4()))
                document_ids.append(doc_id)

                # Extract text and metadata
                text = doc.get("text", "")
                texts.append(text)

                # Prepare metadata - ChromaDB requires all values to be strings, ints, floats, or bools
                metadata = doc.get("metadata", {})
                safe_metadata = {}
                for key, value in metadata.items():
                    # Convert all values to supported types
                    if isinstance(value, (str, int, float, bool)):
                        safe_metadata[key] = value
                    else:
                        safe_metadata[key] = str(value)
                
                metadatas.append(safe_metadata)

            # Upsert documents (ChromaDB will automatically generate embeddings)
            collection.upsert(
                ids=document_ids,
                documents=texts,
                metadatas=metadatas
            )

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
            collection_name: Name of the collection to search
            query_text: The text query
            limit: Maximum number of results
            filters: Optional filters to apply (e.g., {"notebook_id": "123"})

        Returns:
            Result[List[Dict[str, Any]]]: Success with matching documents or failure
        """
        try:
            client = self._get_client()
            
            # Normalize collection name
            safe_collection_name = collection_name.lower()
            safe_collection_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in safe_collection_name)
            if len(safe_collection_name) < 3:
                safe_collection_name = safe_collection_name + "_collection"

            collection = client.get_or_create_collection(
                name=safe_collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            # Build where clause for filtering
            where_clause = None
            if filters:
                # ChromaDB uses a dict-based query format
                # For multiple filters, we use $and
                if len(filters) == 1:
                    key, value = list(filters.items())[0]
                    where_clause = {key: {"$eq": value}}
                else:
                    conditions = []
                    for key, value in filters.items():
                        conditions.append({key: {"$eq": value}})
                    where_clause = {"$and": conditions}

            # Execute query
            results = collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=where_clause
            )

            # Format results
            formatted_results = []
            if results and results.get('ids') and len(results['ids']) > 0:
                ids = results['ids'][0]
                documents = results.get('documents', [[]])[0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]

                for i in range(len(ids)):
                    # ChromaDB returns distance (lower is better)
                    # Convert to certainty score (higher is better) for consistency
                    distance = distances[i] if i < len(distances) else 1.0
                    certainty = 1.0 - distance  # Since we use cosine distance

                    metadata = metadatas[i] if i < len(metadatas) else {}
                    
                    formatted_results.append({
                        "id": ids[i],
                        "text": documents[i] if i < len(documents) else "",
                        "metadata": metadata,
                        "distance": distance,
                        "certainty": certainty
                    })

            return Result.success(formatted_results)

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
            collection_name: Name of the collection
            filters: Filters to identify documents to delete

        Returns:
            Result[int]: Success with count of deleted documents or failure
        """
        try:
            client = self._get_client()
            
            # Normalize collection name
            safe_collection_name = collection_name.lower()
            safe_collection_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in safe_collection_name)
            if len(safe_collection_name) < 3:
                safe_collection_name = safe_collection_name + "_collection"

            collection = client.get_or_create_collection(
                name=safe_collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            if not filters:
                return Result.failure("No filters provided for deletion")

            # Build where clause
            if len(filters) == 1:
                key, value = list(filters.items())[0]
                where_clause = {key: {"$eq": value}}
            else:
                conditions = []
                for key, value in filters.items():
                    conditions.append({key: {"$eq": value}})
                where_clause = {"$and": conditions}

            # First, get the documents to count them
            results = collection.get(
                where=where_clause
            )

            count = len(results['ids']) if results and results.get('ids') else 0

            if count > 0:
                # Delete the documents
                collection.delete(
                    where=where_clause
                )

            return Result.success(count)

        except Exception as e:
            return Result.failure(f"Failed to delete documents: {str(e)}")

    def collection_exists(self, collection_name: str) -> Result[bool]:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            Result[bool]: Success with True/False or failure
        """
        try:
            client = self._get_client()
            
            # Normalize collection name
            safe_collection_name = collection_name.lower()
            safe_collection_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in safe_collection_name)
            if len(safe_collection_name) < 3:
                safe_collection_name = safe_collection_name + "_collection"

            # List all collections and check if our collection exists
            collections = client.list_collections()
            exists = any(col.name == safe_collection_name for col in collections)

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
            collection_name: Name of the collection
            filters: Optional filters to apply

        Returns:
            Result[int]: Success with document count or failure
        """
        try:
            client = self._get_client()
            
            # Normalize collection name
            safe_collection_name = collection_name.lower()
            safe_collection_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in safe_collection_name)
            if len(safe_collection_name) < 3:
                safe_collection_name = safe_collection_name + "_collection"

            # Check if collection exists
            collections = client.list_collections()
            exists = any(col.name == safe_collection_name for col in collections)
            
            if not exists:
                return Result.success(0)

            collection = client.get_collection(name=safe_collection_name)

            if filters:
                # Build where clause
                if len(filters) == 1:
                    key, value = list(filters.items())[0]
                    where_clause = {key: {"$eq": value}}
                else:
                    conditions = []
                    for key, value in filters.items():
                        conditions.append({key: {"$eq": value}})
                    where_clause = {"$and": conditions}

                # Get filtered documents
                results = collection.get(
                    where=where_clause
                )
                count = len(results['ids']) if results and results.get('ids') else 0
            else:
                # Get total count
                count = collection.count()

            return Result.success(count)

        except Exception as e:
            return Result.failure(f"Failed to get document count: {str(e)}")

    def close(self):
        """Close the ChromaDB client connection."""
        # ChromaDB doesn't require explicit closing, but we'll reset the client
        self._client = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
