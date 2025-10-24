#!/usr/bin/env python3
"""
Command-line application to ingest an existing notebook into the vector database.

This script works with an existing notebook (finds by name, e.g., Ben Franklin notes) and:
1. Searches for notebook by name pattern
2. Retrieves all sources for the notebook
3. Segments each source content into smaller chunks
4. Stores segments in the vector database with embeddings
5. Ensures traceability of notebook_id and source_id on each segment

Usage:
    python src/apps/ingest_notebook_into_vectordb2.py [options]

Options:
    --notebook-name TEXT    Name pattern to search for (default: searches for "franklin")
    --collection-name TEXT  Name of the vector database collection (default: ben_franklin)
    --chunk-size INT        Size of text chunks in characters (default: 1000)
    --overlap INT          Overlap between chunks in characters (default: 200)
    --force-reingest       Force re-ingestion even if already ingested

Example:
    python src/apps/ingest_notebook_into_vectordb2.py --notebook-name "Ben Franklin"
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
from src.core.queries.notebook_queries import GetNotebookByIdQuery
from src.core.queries.source_queries import ListSourcesQuery

# Load environment variables
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

    return db, service, vector_db_provider, notebook_repository, source_repository


def find_notebook_by_name(name_pattern: str = "franklin"):
    """
    Find a notebook by name pattern.

    Args:
        name_pattern: Name pattern to search for (case-insensitive)

    Returns:
        UUID: notebook_id or exits if not found
    """
    db = None
    try:
        db = SessionLocal()
        notebook_repository = PostgresNotebookRepository(db)

        # Search for notebooks
        from src.core.services.notebook_management_service import NotebookManagementService
        from src.core.queries.notebook_queries import ListNotebooksQuery

        notebook_service = NotebookManagementService(notebook_repository)

        query = ListNotebooksQuery()
        result = notebook_service.list_notebooks(query)

        if result.is_failure:
            print(f"[ERROR] Failed to search notebooks: {result.error}")
            sys.exit(1)

        notebooks = result.value

        # Filter by name pattern
        matching = [nb for nb in notebooks if name_pattern.lower() in nb.name.lower()]

        if not matching:
            print(f"[ERROR] No notebooks found matching pattern: '{name_pattern}'")
            print(f"        Available notebooks:")
            for nb in notebooks[:5]:
                print(f"          - {nb.name}")
            sys.exit(1)

        if len(matching) > 1:
            print(f"[WARNING] Found {len(matching)} notebooks matching '{name_pattern}':")
            for idx, nb in enumerate(matching, 1):
                print(f"          {idx}. {nb.name} ({nb.id})")
            print(f"[*] Using first match: {matching[0].name}")
            print()

        notebook = matching[0]
        print(f"[SUCCESS] Found notebook: {notebook.name}")
        print(f"          Notebook ID: {notebook.id}")
        print(f"          Description: {notebook.description}")
        print(f"          Tags: {', '.join(notebook.tags) if notebook.tags else 'None'}")
        print()

        return notebook.id

    finally:
        if db:
            db.close()


def verify_notebook_and_sources(notebook_id: UUID):
    """
    Verify that the notebook has sources.

    Args:
        notebook_id: UUID of the notebook

    Returns:
        tuple: (notebook, sources_list) or exits if not found
    """
    db = None
    try:
        db = SessionLocal()
        notebook_repository = PostgresNotebookRepository(db)
        source_repository = PostgresSourceRepository(db)

        # Get notebook details
        from src.core.services.notebook_management_service import NotebookManagementService
        notebook_service = NotebookManagementService(notebook_repository)

        query = GetNotebookByIdQuery(notebook_id=notebook_id)
        result = notebook_service.get_notebook_by_id(query)

        if result.is_failure:
            print(f"[ERROR] Notebook not found: {result.error}")
            sys.exit(1)

        notebook = result.value

        # Get sources for the notebook
        from src.core.services.source_ingestion_service import SourceIngestionService
        from src.infrastructure.providers.local_file_storage_provider import LocalFileStorageProvider
        from src.infrastructure.providers.file_content_extraction_provider import FileContentExtractionProvider
        from src.infrastructure.providers.http_web_fetch_provider import HttpWebFetchProvider

        file_storage_provider = LocalFileStorageProvider()
        content_extraction_provider = FileContentExtractionProvider()
        web_fetch_provider = HttpWebFetchProvider()

        source_service = SourceIngestionService(
            source_repository=source_repository,
            notebook_repository=notebook_repository,
            file_storage_provider=file_storage_provider,
            content_extraction_provider=content_extraction_provider,
            web_fetch_provider=web_fetch_provider
        )

        sources_query = ListSourcesQuery(notebook_id=notebook_id)
        sources_result = source_service.list_sources(sources_query)

        if sources_result.is_failure:
            print(f"[ERROR] Failed to retrieve sources: {sources_result.error}")
            sys.exit(1)

        sources = sources_result.value
        if not sources:
            print(f"[WARNING] No sources found in notebook")
            print(f"          Please add sources before ingesting")
            sys.exit(1)

        print(f"[SUCCESS] Found {len(sources)} source(s) in notebook:")
        for idx, source in enumerate(sources, 1):
            print(f"          {idx}. {source.name}")
            print(f"             Source ID: {source.id}")
            print(f"             Type: {source.source_type}")
            if source.extracted_text:
                print(f"             Content length: {len(source.extracted_text)} characters")
            print()

        return notebook, sources

    finally:
        if db:
            db.close()


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
        db, service, vector_db_provider, _, _ = create_services()

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
            print("  1. ✓ Notebook validated")
            print("  2. ✓ Collection created/verified in vector database")
            print(f"  3. ✓ Sources segmented into {chunks_ingested} chunks")
            print("  4. ✓ Each segment stored with embeddings")
            print("  5. ✓ Traceability metadata (notebook_id, source_id, chunk_index) added")
            print()
            print(f"Vector database index: {collection_name}")
            print(f"Each segment includes:")
            print(f"  - text: The actual content chunk")
            print(f"  - notebook_id: {notebook_id}")
            print(f"  - source_id: ID of the parent source")
            print(f"  - chunk_index: Position within the source")
            print(f"  - embedding: Vector representation for similarity search")

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
            print(f"  Certainty: {result.get('certainty', 'N/A'):.4f}" if result.get('certainty') else "  Certainty: N/A")
            print(f"  Distance: {result.get('distance', 'N/A'):.4f}" if result.get('distance') else "  Distance: N/A")
            print(f"  Text preview: {result['text'][:200]}...")
            print()

    except Exception as e:
        print(f"[ERROR] Exception during query: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if vector_db_provider:
            vector_db_provider.close()


def main():
    """Main entry point for the ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest an existing notebook and its sources into the vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find and ingest Ben Franklin notebook
  python src/apps/ingest_notebook_into_vectordb2.py --notebook-name "franklin"

  # Ingest with custom collection name and chunk size
  python src/apps/ingest_notebook_into_vectordb2.py --notebook-name "Ben Franklin" --collection-name ben_franklin --chunk-size 1500

  # Force re-ingestion even if already ingested
  python src/apps/ingest_notebook_into_vectordb2.py --notebook-name "franklin" --force-reingest

  # Run with test search after ingestion
  python src/apps/ingest_notebook_into_vectordb2.py --notebook-name "franklin" --test-search
        """
    )

    parser.add_argument(
        "--notebook-name",
        type=str,
        default="franklin",
        help="Name pattern to search for (default: franklin)"
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="ben_franklin",
        help="Name of the vector database collection (default: ben_franklin)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of text chunks in characters (default: 1000)"
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=200,
        help="Overlap between chunks in characters (default: 200)"
    )
    parser.add_argument(
        "--force-reingest",
        action="store_true",
        help="Force re-ingestion even if already ingested"
    )
    parser.add_argument(
        "--test-search",
        action="store_true",
        help="Run a test similarity search after ingestion"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What were Franklin's key accomplishments?",
        help="Query text for test search (default: 'What were Franklin's key accomplishments?')"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("  Vector Database Ingestion Tool")
    print("  Ingest existing notebook with sources")
    print("="*70 + "\n")

    # Find notebook by name pattern
    notebook_id = find_notebook_by_name(args.notebook_name)

    # Verify notebook and sources exist
    notebook, sources = verify_notebook_and_sources(notebook_id)

    # Run ingestion
    chunks = ingest_notebook(
        notebook_id=notebook_id,
        collection_name=args.collection_name,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        force_reingest=args.force_reingest
    )

    # Optionally run test search
    if args.test_search and chunks > 0:
        query_sample_vectors(
            notebook_id=notebook_id,
            collection_name=args.collection_name,
            sample_query=args.query
        )

    print("\n" + "="*70)
    print("  Ingestion Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
