"""Factory for creating vector database providers based on configuration."""
import os
from typing import Optional

from ...core.interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from .weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
from .chroma_vector_database_provider import ChromaVectorDatabaseProvider


def create_vector_database_provider() -> IVectorDatabaseProvider:
    """
    Create a vector database provider based on environment configuration.

    Reads VECTOR_DB_PROVIDER environment variable to determine which provider to use.
    Supported values:
    - "weaviate" (default): Use WeaviateVectorDatabaseProvider
    - "chroma": Use ChromaVectorDatabaseProvider

    For Weaviate:
    - WEAVIATE_URL: URL of the Weaviate instance (default: http://localhost:8080)
    - WEAVIATE_KEY: Optional API key for cloud instances

    For ChromaDB:
    - CHROMA_HOST: Host for client-server mode (if not set, uses persistent local mode)
    - CHROMA_PORT: Port for client-server mode (default: 8000)
    - CHROMA_PERSIST_DIR: Directory to persist data (default: ./chroma_data)

    Returns:
        IVectorDatabaseProvider: Configured vector database provider instance

    Raises:
        ValueError: If an unsupported provider type is specified
    """
    provider_type = os.getenv("VECTOR_DB_PROVIDER", "weaviate").lower()

    if provider_type == "weaviate":
        # Create Weaviate provider
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        weaviate_key = os.getenv("WEAVIATE_KEY")
        
        return WeaviateVectorDatabaseProvider(
            url=weaviate_url,
            api_key=weaviate_key
        )

    elif provider_type == "chroma":
        # Create ChromaDB provider
        chroma_host = os.getenv("CHROMA_HOST")
        chroma_port = os.getenv("CHROMA_PORT", "8000")
        chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

        if chroma_host:
            # Client-server mode
            return ChromaVectorDatabaseProvider(
                host=chroma_host,
                port=int(chroma_port)
            )
        else:
            # Persistent local mode
            return ChromaVectorDatabaseProvider(
                persist_directory=chroma_persist_dir
            )

    else:
        raise ValueError(
            f"Unsupported vector database provider: {provider_type}. "
            f"Supported providers: 'weaviate', 'chroma'"
        )


def get_vector_db_provider_type() -> str:
    """
    Get the configured vector database provider type.

    Returns:
        str: The provider type ("weaviate" or "chroma")
    """
    return os.getenv("VECTOR_DB_PROVIDER", "weaviate").lower()
