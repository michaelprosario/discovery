#!/usr/bin/env python3
"""
Demonstration script for Weaviate integration and content ingestion.

This script:
1. Creates a new notebook with a random name
2. Imports two Wikipedia articles about Pixar movies
3. Ingests the content into the vector database using Weaviate
4. Performs a sample similarity search query
"""
import sys
import os
import random
import time
import requests
from uuid import UUID

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Wikipedia URLs to import
WIKIPEDIA_URLS = [
    "https://en.wikipedia.org/wiki/Monsters,_Inc.",
    "https://en.wikipedia.org/wiki/Monsters_University"
]


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_status(message: str, success: bool = True):
    """Print a status message."""
    icon = "✓" if success else "✗"
    print(f"{icon} {message}")


def create_notebook() -> dict:
    """Create a new notebook with a random name."""
    print_section("Step 1: Create Notebook")

    # Generate a random name
    adjectives = ["Amazing", "Incredible", "Fantastic", "Wonderful", "Spectacular"]
    nouns = ["Movies", "Films", "Stories", "Adventures", "Tales"]
    notebook_name = f"{random.choice(adjectives)} {random.choice(nouns)} - {random.randint(1000, 9999)}"

    print(f"Creating notebook: '{notebook_name}'")

    response = requests.post(
        f"{API_BASE_URL}/notebooks",
        json={
            "name": notebook_name,
            "description": "A collection of Pixar's Monsters, Inc. universe content",
            "tags": ["pixar", "movies", "demo"]
        }
    )

    if response.status_code == 201:
        notebook = response.json()
        print_status(f"Notebook created successfully: {notebook['id']}")
        print(f"  Name: {notebook['name']}")
        print(f"  Tags: {', '.join(notebook['tags'])}")
        return notebook
    else:
        print_status(f"Failed to create notebook: {response.text}", success=False)
        sys.exit(1)


def import_url_sources(notebook_id: UUID) -> list:
    """Import Wikipedia URL sources."""
    print_section("Step 2: Import Wikipedia Articles")

    sources = []
    for url in WIKIPEDIA_URLS:
        print(f"Importing: {url}")

        response = requests.post(
            f"{API_BASE_URL}/sources/url",
            json={
                "notebook_id": str(notebook_id),
                "url": url
            }
        )

        if response.status_code == 201:
            source = response.json()
            print_status(f"Imported: {source['name']}")
            print(f"  Source ID: {source['id']}")
            print(f"  Content length: {len(source.get('extracted_text', ''))} characters")
            sources.append(source)
        else:
            print_status(f"Failed to import {url}: {response.text}", success=False)

    print(f"\nTotal sources imported: {len(sources)}")
    return sources


def ingest_into_vector_db(notebook_id: UUID):
    """Ingest notebook content into vector database."""
    print_section("Step 3: Ingest into Vector Database")

    print("Starting vector database ingestion...")
    print("  Chunk size: 1000 characters")
    print("  Overlap: 200 characters")

    response = requests.post(
        f"{API_BASE_URL}/notebooks/{notebook_id}/ingest",
        json={
            "chunk_size": 1000,
            "overlap": 200,
            "force_reingest": False
        }
    )

    if response.status_code == 200:
        result = response.json()
        print_status("Ingestion completed successfully")
        print(f"  Chunks created: {result['chunks_ingested']}")
        print(f"  Message: {result['message']}")
        return result
    else:
        print_status(f"Failed to ingest content: {response.text}", success=False)
        sys.exit(1)


def perform_similarity_search(notebook_id: UUID):
    """Perform sample similarity search queries."""
    print_section("Step 4: Similarity Search Demo")

    # Sample queries
    queries = [
        "What is Monsters University about?",
        "Tell me about the main characters",
        "What happens in the plot?"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)

        response = requests.get(
            f"{API_BASE_URL}/notebooks/{notebook_id}/similar",
            params={
                "query": query,
                "limit": 3
            }
        )

        if response.status_code == 200:
            result = response.json()
            print_status(f"Found {result['total']} similar chunks")

            for idx, item in enumerate(result['results'], 1):
                print(f"\n  Result {idx}:")
                print(f"    Source: {item.get('source_name', 'Unknown')}")
                print(f"    Certainty: {item.get('certainty', 0):.2f}")
                print(f"    Text preview: {item['text'][:150]}...")
        else:
            print_status(f"Search failed: {response.text}", success=False)


def get_vector_count(notebook_id: UUID):
    """Get the count of vectors in the database."""
    print_section("Step 5: Vector Statistics")

    response = requests.get(
        f"{API_BASE_URL}/notebooks/{notebook_id}/vectors/count"
    )

    if response.status_code == 200:
        result = response.json()
        print_status("Vector count retrieved")
        print(f"  Total vectors: {result['vector_count']}")
    else:
        print_status(f"Failed to get vector count: {response.text}", success=False)


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("  Weaviate Integration & Content Ingestion Demo")
    print("  Discovery API - Vector Search Demonstration")
    print("="*60)

    # Check API is accessible
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health")
        if response.status_code != 200:
            print_status("API is not accessible. Please start the API server.", success=False)
            print(f"Expected API at: {API_BASE_URL}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to API. Please start the API server.", success=False)
        print(f"Expected API at: {API_BASE_URL}")
        sys.exit(1)

    try:
        # Execute workflow
        notebook = create_notebook()
        notebook_id = UUID(notebook['id'])

        sources = import_url_sources(notebook_id)

        # Wait a moment for sources to be fully processed
        print("\nWaiting for sources to be processed...")
        time.sleep(2)

        ingest_into_vector_db(notebook_id)

        perform_similarity_search(notebook_id)

        get_vector_count(notebook_id)

        # Summary
        print_section("Summary")
        print_status("Demo completed successfully!")
        print(f"\nNotebook ID: {notebook_id}")
        print(f"You can now query this notebook using the API:")
        print(f"  GET {API_BASE_URL}/notebooks/{notebook_id}/similar?query=your+query")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_status(f"Error: {str(e)}", success=False)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
