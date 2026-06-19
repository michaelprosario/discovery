"""Unit tests for WeaviateVectorDatabaseProvider and its factory."""
import os
import pytest
from unittest.mock import MagicMock, patch

from src.infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
from src.infrastructure.providers.vector_database_factory import create_vector_database_provider


def test_weaviate_provider_init_default():
    """Test that WeaviateVectorDatabaseProvider initializes with default hnsw index type."""
    provider = WeaviateVectorDatabaseProvider(url="http://localhost:8080")
    assert provider.url == "http://localhost:8080"
    assert provider.api_key is None
    assert provider.vector_index_type == "hnsw"


def test_weaviate_provider_init_custom():
    """Test that WeaviateVectorDatabaseProvider initializes with custom index type."""
    provider = WeaviateVectorDatabaseProvider(
        url="https://cloud.weaviate.io",
        api_key="secret-key",
        vector_index_type="hfresh"
    )
    assert provider.url == "https://cloud.weaviate.io"
    assert provider.api_key == "secret-key"
    assert provider.vector_index_type == "hfresh"


@patch.dict(os.environ, {"VECTOR_DB_PROVIDER": "weaviate", "WEAVIATE_VECTOR_INDEX_TYPE": "flat"})
def test_factory_creates_with_env_var():
    """Test that the factory reads WEAVIATE_VECTOR_INDEX_TYPE from environment."""
    provider = create_vector_database_provider()
    assert isinstance(provider, WeaviateVectorDatabaseProvider)
    assert provider.vector_index_type == "flat"


@pytest.mark.parametrize("index_type,expected_method", [
    ("hfresh", "hfresh"),
    ("flat", "flat"),
    ("dynamic", "dynamic"),
    ("hnsw", "hnsw"),
    ("invalid_fallback_to_hnsw", "hnsw"),
])
@patch("weaviate.connect_to_local")
def test_create_collection_calls_correct_index_config(mock_connect_local, index_type, expected_method):
    """Test that create_collection_if_not_exists configures the correct vector index type."""
    # Setup mock client and collections
    mock_client = MagicMock()
    mock_client.collections.exists.return_value = False
    mock_connect_local.return_value = mock_client

    provider = WeaviateVectorDatabaseProvider(
        url="http://localhost:8080",
        vector_index_type=index_type
    )

    # Mock the Configure class helper methods
    from weaviate.classes.config import Configure
    
    with patch.object(Configure.VectorIndex, expected_method) as mock_config_method:
        mock_config_method.return_value = MagicMock()
        
        provider.create_collection_if_not_exists("TestCollection")
        
        # Verify Weaviate's create was called
        mock_client.collections.create.assert_called_once()
        _, kwargs = mock_client.collections.create.call_args
        
        # Verify the appropriate Configure.VectorIndex method was called
        mock_config_method.assert_called_once()
        assert "vector_index_config" in kwargs
