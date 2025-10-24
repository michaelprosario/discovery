#!/usr/bin/env python3
"""
Command-line application to ingest a notebook and its sources into the vector database.

This script demonstrates the complete ingestion workflow:
1. Creates/validates a notebook exists
2. Creates/validates sources exist for the notebook
3. Segments the source content into smaller chunks
4. Stores segments in the vector database with embeddings
5. Ensures traceability of notebook_id and source_id on each segment

Usage:
    python src/apps/ingest_notebook_into_vectordb.py <notebook_id> [options]

Options:
    --collection-name TEXT  Name of the vector database collection (default: ben_franklin)
    --chunk-size INT        Size of text chunks in characters (default: 1000)
    --overlap INT          Overlap between chunks in characters (default: 200)
    --force-reingest       Force re-ingestion even if already ingested
"""
import sys
import os
import argparse
from uuid import UUID

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.infrastructure.database.connection import SessionLocal
from src.infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository
from src.infrastructure.repositories.postgres_source_repository import PostgresSourceRepository
from src.infrastructure.providers.weaviate_vector_database_provider import WeaviateVectorDatabaseProvider
from src.infrastructure.providers.simple_content_segmenter import SimpleContentSegmenter
from src.core.services.vector_ingestion_service import VectorIngestionService
from src.core.commands.vector_commands import IngestNotebookCommand

# make sure we access env variables
from dotenv import load_dotenv
load_dotenv()

def create_services():
    """
    Create and configure all required services with dependency injection.

    Returns:
        tuple: (db_session, vector_ingestion_service, vector_db_provider)
    """
    # Get database session
    db = SessionLocal()

    # Create repositories
    notebook_repository = PostgresNotebookRepository(db)
    source_repository = PostgresSourceRepository(db)

    # Create providers
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_key = os.getenv("WEAVIATE_KEY")
    vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)
    content_segmenter = SimpleContentSegmenter()

    # Create service with all dependencies
    service = VectorIngestionService(
        notebook_repository=notebook_repository,
        source_repository=source_repository,
        vector_db_provider=vector_db_provider,
        content_segmenter=content_segmenter
    )

    return db, service, vector_db_provider

def ingest_notebook(
    notebook_id: UUID,
    collection_name: str = "ben_franklin",
    chunk_size: int = 1000,
    overlap: int = 200,
    force_reingest: bool = False
):
    """
    Ingest a notebook and all its sources into the vector database.

    Args:
        notebook_id: UUID of the notebook to ingest
        collection_name: Name of the collection in vector database
        chunk_size: Target size for each text chunk in characters
        overlap: Number of characters to overlap between chunks
        force_reingest: Whether to force re-ingestion even if already exists

    Returns:
        int: Number of chunks ingested
    """
    db = None
    vector_db_provider = None

    try:
        # Create services
        db, service, vector_db_provider = create_services()

        print(f"[*] Starting ingestion for notebook: {notebook_id}")
        print(f"    Collection: {collection_name}")
        print(f"    Chunk size: {chunk_size}, Overlap: {overlap}")
        print(f"    Force reingest: {force_reingest}")
        print()

        # Create ingestion command
        command = IngestNotebookCommand(
            notebook_id=notebook_id,
            collection_name=collection_name,
            chunk_size=chunk_size,
            overlap=overlap,
            force_reingest=force_reingest
        )

        # Execute ingestion
        result = service.ingest_notebook(command)

        if result.is_failure:
            print(f"[ERROR] Ingestion failed: {result.error}")
            return 0

        chunks_ingested = result.value
        print(f"[SUCCESS] Ingested {chunks_ingested} chunks into vector database")
        print()

        # Verify ingestion by querying the collection
        count_result = vector_db_provider.get_document_count(
            collection_name,
            filters={"notebook_id": str(notebook_id)}
        )

        if count_result.is_success:
            print(f"[VERIFIED] {count_result.value} vectors stored for notebook {notebook_id}")
            print()
            print("Summary of ingestion process:")
            print("  1. [DONE] Notebook validated")
            print("  2. [DONE] Collection created/verified in vector database")
            print(f"  3. [DONE] Sources retrieved and segmented into {chunks_ingested} chunks")
            print("  4. [DONE] Each segment stored with embeddings")
            print("  5. [DONE] Traceability metadata (notebook_id, source_id) added to each segment")

        return chunks_ingested

    except Exception as e:
        print(f"[ERROR] Exception during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        # Cleanup
        if vector_db_provider:
            vector_db_provider.close()
        if db:
            db.close()

def query_sample_vectors(
    notebook_id: UUID,
    collection_name: str = "ben_franklin",
    sample_query: str = "What were Franklin's key accomplishments?"
):
    """
    Query the vector database to verify ingestion and demonstrate search.

    Args:
        notebook_id: UUID of the notebook
        collection_name: Name of the collection
        sample_query: Sample query text for similarity search
    """
    vector_db_provider = None

    try:
        # Create minimal services for querying
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        weaviate_key = os.getenv("WEAVIATE_KEY")
        vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)

        print(f"\n[*] Testing similarity search with query: '{sample_query}'")
        print()

        # Perform similarity search
        search_result = vector_db_provider.query_similarity(
            collection_name=collection_name,
            query_text=sample_query,
            limit=3,
            filters={"notebook_id": str(notebook_id)}
        )

        if search_result.is_failure:
            print(f"[ERROR] Search failed: {search_result.error}")
            return

        results = search_result.value
        print(f"[*] Found {len(results)} similar chunks:")
        print()

        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  Source ID: {result['metadata'].get('source_id', 'N/A')}")
            print(f"  Chunk Index: {result['metadata'].get('chunk_index', 'N/A')}")
            print(f"  Certainty: {result.get('certainty', 'N/A')}")
            print(f"  Text preview: {result['text'][:150]}...")
            print()

    except Exception as e:
        print(f"[ERROR] Exception during query: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if vector_db_provider:
            vector_db_provider.close()


def create_notebook_in_db(name: str, description: str, tags: list) -> UUID:
    """
    Create a new notebook directly in the database.

    Args:
        name: Name of the notebook
        description: Description of the notebook
        tags: List of tags

    Returns:
        UUID: The ID of the created notebook
    """
    db = None
    try:
        db = SessionLocal()
        notebook_repository = PostgresNotebookRepository(db)

        from src.core.commands.notebook_commands import CreateNotebookCommand
        from src.core.services.notebook_management_service import NotebookManagementService

        service = NotebookManagementService(notebook_repository)
        command = CreateNotebookCommand(
            name=name,
            description=description,
            tags=tags
        )

        result = service.create_notebook(command)

        if result.is_failure:
            raise Exception(f"Failed to create notebook: {result.error}")

        notebook_id = result.value.id
        print(f"[SUCCESS] Created notebook: {name}")
        print(f"          Notebook ID: {notebook_id}")
        return notebook_id

    finally:
        if db:
            db.close()


def add_sample_source(notebook_id: UUID, content: str, name: str) -> UUID:
    """
    Add a sample text source to a notebook by creating a temporary text file.

    Args:
        notebook_id: ID of the notebook
        content: Text content for the source
        name: Name of the source

    Returns:
        UUID: The ID of the created source
    """
    db = None
    try:
        db = SessionLocal()
        source_repository = PostgresSourceRepository(db)
        notebook_repository = PostgresNotebookRepository(db)

        from src.infrastructure.providers.local_file_storage_provider import LocalFileStorageProvider
        from src.infrastructure.providers.file_content_extraction_provider import FileContentExtractionProvider
        from src.infrastructure.providers.http_web_fetch_provider import HttpWebFetchProvider
        from src.core.commands.source_commands import ImportFileSourceCommand
        from src.core.services.source_ingestion_service import SourceIngestionService
        from src.core.value_objects.enums import FileType
        import tempfile

        # Create providers
        file_storage_provider = LocalFileStorageProvider()
        content_extraction_provider = FileContentExtractionProvider()
        web_fetch_provider = HttpWebFetchProvider()

        # Create service
        service = SourceIngestionService(
            source_repository=source_repository,
            notebook_repository=notebook_repository,
            file_storage_provider=file_storage_provider,
            content_extraction_provider=content_extraction_provider,
            web_fetch_provider=web_fetch_provider
        )

        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Read file content as bytes
            with open(tmp_path, 'rb') as f:
                file_content = f.read()

            # Create command
            command = ImportFileSourceCommand(
                notebook_id=notebook_id,
                file_path=tmp_path,
                file_name=f"{name}.txt",
                file_type=FileType.TXT,
                file_content=file_content,
                metadata={}
            )

            # Import source
            result = service.import_file_source(command)

            if result.is_failure:
                raise Exception(f"Failed to import source: {result.error}")

            source_id = result.value.id
            print(f"[SUCCESS] Added source: {name}")
            print(f"          Source ID: {source_id}")
            print(f"          Content length: {len(content)} characters")
            return source_id

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    finally:
        if db:
            db.close()


def main():
    """Main entry point for the ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest a notebook and its sources into the vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ingestion with default settings
  python src/apps/ingest_notebook_into_vectordb.py

  """
    )

    print("\n" + "="*60)
    print("  Vector Database Ingestion Demo")
    print("  Creating notebook with sample content")
    print("="*60 + "\n")

    # Create a new notebook
    import random
    adjectives = ["Amazing", "Incredible", "Fantastic", "Wonderful", "Spectacular"]
    nouns = ["Research", "Knowledge", "Learning", "Discovery", "Insights"]
    notebook_name = f"{random.choice(adjectives)} {random.choice(nouns)} - {random.randint(1000, 9999)}"

    notebook_id = create_notebook_in_db(
        name=notebook_name,
        description="A demonstration notebook with sample content for vector database ingestion",
        tags=["demo", "test", "vectordb"]
    )

    print()

    # Add sample sources to the notebook
    sample_sources = [
        {
            "name": "Introduction to AI",
            "content": """
            Artificial Intelligence (AI) is revolutionizing how we interact with technology.
            Machine learning, a subset of AI, enables computers to learn from data without being
            explicitly programmed. Deep learning, a further specialization, uses neural networks
            with multiple layers to process complex patterns in large datasets. These technologies
            are being applied across industries from healthcare to finance, transforming business
            operations and creating new opportunities for innovation.
            """
        },
        {
            "name": "Vector Databases Explained",
            "content": """
            Vector databases are specialized storage systems designed for similarity search. Unlike
            traditional databases that search for exact matches, vector databases find items that
            are similar to a query. They work by converting data into high-dimensional vectors
            (embeddings) that capture semantic meaning. This makes them ideal for applications like
            semantic search, recommendation systems, and retrieval-augmented generation (RAG).
            Popular vector databases include Weaviate, Pinecone, and Milvus.
            """
        },
        {
            "name": "The Future of Search",
            "content": """
            Search technology is evolving beyond keyword matching. Semantic search understands the
            intent and contextual meaning of queries, providing more relevant results. Vector
            embeddings enable this by representing text, images, and other data as mathematical
            vectors in a multi-dimensional space. When combined with large language models, these
            technologies enable natural language understanding and generation, creating more intuitive
            and powerful search experiences for users.
            """
        }
    ]

    for source_data in sample_sources:
        add_sample_source(
            notebook_id=notebook_id,
            content=source_data["content"].strip(),
            name=source_data["name"]
        )

    print()
    collection_name_default = "discovery_content"

    # Run ingestion
    chunks = ingest_notebook(
        notebook_id=notebook_id,
        collection_name=collection_name_default
    )

    # Run test search if ingestion was successful
    if chunks > 0:
        query_sample_vectors(
            notebook_id=notebook_id,
            collection_name=collection_name_default,
            sample_query="What is semantic search and how does it work?"
        )




if __name__ == "__main__":
    main()
