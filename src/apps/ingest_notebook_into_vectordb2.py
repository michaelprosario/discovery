#!/usr/bin/env python3
"""
Command-line application to create a notebook and ingest content into the vector database.

This script:
1. Creates a new notebook with a GUID as the name
2. Imports a URL source (Ben Franklin autobiography from Project Gutenberg)
3. Segments the source content into smaller chunks
4. Stores segments in the vector database with embeddings
5. Demonstrates similarity search on the ingested content
6. Ensures traceability of notebook_id and source_id on each segment

Usage:
    python src/apps/ingest_notebook_into_vectordb2.py

No command-line arguments required - the script runs a complete demo workflow.
"""
import sys
import os
import uuid
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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
GUTENBERG_URL = "https://www.gutenberg.org/files/20203/20203-8.txt"
COLLECTION_NAME = "ben_franklin"
CHUNK_SIZE = 1000
OVERLAP = 200


def create_notebook_with_guid() -> UUID:
    """
    Create a new notebook with a GUID as its name.

    Returns:
        UUID: The ID of the created notebook
    """
    db = None
    try:
        db = SessionLocal()
        notebook_repository = PostgresNotebookRepository(db)

        from src.core.commands.notebook_commands import CreateNotebookCommand
        from src.core.services.notebook_management_service import NotebookManagementService

        # Generate GUID for notebook name
        notebook_guid = str(uuid.uuid4())

        service = NotebookManagementService(notebook_repository)
        command = CreateNotebookCommand(
            name=notebook_guid,
            description="Ben Franklin Autobiography - Project Gutenberg",
            tags=["ben_franklin", "autobiography", "demo", "gutenberg"]
        )

        result = service.create_notebook(command)

        if result.is_failure:
            raise Exception(f"Failed to create notebook: {result.error}")

        notebook_id = result.value.id
        print(f"[SUCCESS] Created notebook with GUID name")
        print(f"          Notebook Name: {notebook_guid}")
        print(f"          Notebook ID: {notebook_id}")
        print(f"          Description: Ben Franklin Autobiography - Project Gutenberg")
        print(f"          Tags: ben_franklin, autobiography, demo, gutenberg")
        print()

        return notebook_id

    finally:
        if db:
            db.close()


def import_gutenberg_source(notebook_id: UUID, url: str) -> UUID:
    """
    Import a source from Project Gutenberg URL.

    Args:
        notebook_id: ID of the notebook
        url: URL to import

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
        from src.core.commands.source_commands import ImportUrlSourceCommand
        from src.core.services.source_ingestion_service import SourceIngestionService

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

        print(f"[*] Importing source from: {url}")
        print(f"    This may take a moment...")

        # Create command
        command = ImportUrlSourceCommand(
            notebook_id=notebook_id,
            url=url,
            title="The Autobiography of Benjamin Franklin"
        )

        # Import source
        result = service.import_url_source(command)

        if result.is_failure:
            raise Exception(f"Failed to import source: {result.error}")

        source = result.value
        source_id = source.id
        print(f"[SUCCESS] Imported source: {source.name}")
        print(f"          Source ID: {source_id}")
        print(f"          Source Type: {source.source_type}")
        if source.extracted_text:
            print(f"          Content length: {len(source.extracted_text)} characters")
        print()

        return source_id

    finally:
        if db:
            db.close()


def ingest_notebook(
    notebook_id: UUID,
    collection_name: str = COLLECTION_NAME,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP
):
    """
    Ingest a notebook and all its sources into the vector database.

    Args:
        notebook_id: UUID of the notebook to ingest
        collection_name: Name of the collection in vector database
        chunk_size: Target size for each text chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        int: Number of chunks ingested
    """
    db = None
    vector_db_provider = None

    try:
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

        print(f"[*] Starting vector database ingestion")
        print(f"    Notebook ID: {notebook_id}")
        print(f"    Collection: {collection_name}")
        print(f"    Chunk size: {chunk_size} characters")
        print(f"    Overlap: {overlap} characters")
        print()

        # Create ingestion command
        command = IngestNotebookCommand(
            notebook_id=notebook_id,
            collection_name=collection_name,
            chunk_size=chunk_size,
            overlap=overlap,
            force_reingest=False
        )

        # Execute ingestion
        print(f"[*] Segmenting text and creating embeddings...")
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
            print(f"[VERIFIED] {count_result.value} vectors stored in collection '{collection_name}'")
            print()
            print("Traceability Information:")
            print(f"  ✓ Each segment includes notebook_id: {notebook_id}")
            print(f"  ✓ Each segment includes source_id (parent source)")
            print(f"  ✓ Each segment includes chunk_index (position)")
            print(f"  ✓ Each segment has vector embedding for similarity search")
            print()

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


def demo_similarity_searches(notebook_id: UUID, collection_name: str = COLLECTION_NAME):
    """
    Demonstrate similarity search on the ingested content.

    Args:
        notebook_id: UUID of the notebook
        collection_name: Name of the collection
    """
    vector_db_provider = None

    try:
        # Create vector database provider
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        weaviate_key = os.getenv("WEAVIATE_KEY")
        vector_db_provider = WeaviateVectorDatabaseProvider(url=weaviate_url, api_key=weaviate_key)

        print("="*70)
        print("  SIMILARITY SEARCH DEMONSTRATION")
        print("="*70)
        print()

        # Sample queries about Ben Franklin
        queries = [
            "What were Franklin's key accomplishments?",
            "Tell me about Franklin's early life and education",
            "What was Franklin's role in politics and government?",
            "Describe Franklin's scientific experiments and discoveries"
        ]

        for idx, query in enumerate(queries, 1):
            print(f"\n{'='*70}")
            print(f"Query {idx}: \"{query}\"")
            print('='*70)

            # Perform similarity search
            search_result = vector_db_provider.query_similarity(
                collection_name=collection_name,
                query_text=query,
                limit=3,
                filters={"notebook_id": str(notebook_id)}
            )

            if search_result.is_failure:
                print(f"[ERROR] Search failed: {search_result.error}")
                continue

            results = search_result.value
            print(f"\nFound {len(results)} similar chunks:\n")

            for i, result in enumerate(results, 1):
                certainty = result.get('certainty')
                distance = result.get('distance')

                print(f"Result {i}:")
                if certainty is not None:
                    print(f"  Certainty: {certainty:.4f} (higher = more similar)")
                if distance is not None:
                    print(f"  Distance:  {distance:.4f} (lower = more similar)")
                print(f"  Source ID: {result['metadata'].get('source_id', 'N/A')}")
                print(f"  Chunk:     {result['metadata'].get('chunk_index', 'N/A')}")
                print(f"\n  Text Preview:")
                text = result['text']
                # Show first 300 characters
                preview = text[:300] + "..." if len(text) > 300 else text
                # Indent each line
                for line in preview.split('\n'):
                    if line.strip():
                        print(f"    {line}")
                print()

        print("\n" + "="*70)
        print("  Similarity Search Demo Complete")
        print("="*70)
        print()

    except Exception as e:
        print(f"[ERROR] Exception during similarity search: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if vector_db_provider:
            vector_db_provider.close()


def main():
    """Main entry point for the demo script."""
    print("\n" + "="*70)
    print("  BEN FRANKLIN VECTOR DATABASE DEMO")
    print("  Create, Import, Ingest, and Search")
    print("="*70 + "\n")

    try:
        # Step 1: Create notebook with GUID name
        print("[STEP 1] Creating new notebook with GUID name...")
        notebook_id = create_notebook_with_guid()

        # Step 2: Import Project Gutenberg source
        print("[STEP 2] Importing Ben Franklin autobiography from Project Gutenberg...")
        source_id = import_gutenberg_source(notebook_id, GUTENBERG_URL)

        # Step 3: Ingest into vector database
        print("[STEP 3] Ingesting content into vector database...")
        chunks = ingest_notebook(notebook_id, COLLECTION_NAME, CHUNK_SIZE, OVERLAP)

        if chunks == 0:
            print("[ERROR] No chunks ingested, cannot proceed with demo")
            sys.exit(1)

        # Step 4: Demo similarity searches
        print("[STEP 4] Demonstrating similarity searches...")
        demo_similarity_searches(notebook_id, COLLECTION_NAME)

        # Summary
        print("\n" + "="*70)
        print("  DEMO COMPLETE!")
        print("="*70)
        print()
        print(f"Summary:")
        print(f"  ✓ Created notebook: {notebook_id}")
        print(f"  ✓ Imported source: {source_id}")
        print(f"  ✓ Ingested {chunks} chunks")
        print(f"  ✓ Demonstrated similarity search")
        print()
        print(f"Vector database collection: '{COLLECTION_NAME}'")
        print(f"Each segment includes traceability:")
        print(f"  - notebook_id: {notebook_id}")
        print(f"  - source_id: {source_id}")
        print(f"  - chunk_index: 0, 1, 2, ...")
        print(f"  - embedding: Vector representation")
        print()

    except KeyboardInterrupt:
        print("\n\n[*] Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
