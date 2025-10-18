- follow standards at specs/clean_architecture.md
- setup core services for  vector database services , content segmentation for RAG, and apis for content similarity queries. 
- at core level, make sure core services have unit tests and all unit tests pass.
- implement infra code for vector database providers using weaviate
- write a program that does the following
    - create a notebook with a random name
    - import the following urls as content sources 
        - https://en.wikipedia.org/wiki/Monsters,_Inc.
        - https://en.wikipedia.org/wiki/Monsters_University
- Ingest the notebook and related sources into our vector database that uses weaviate on the infra level

===

# Plan for Weaviate Integration and Content Ingestion

This document outlines the plan to integrate Weaviate as a vector database, set up content ingestion services, and create a script to demonstrate the process, following the project's Clean Architecture standards.

## 1. Infrastructure Setup: Weaviate via Docker Compose

-   **Action:** Create a new `docker-compose.weaviate.yml` file.
-   **Details:**
    -   This file will define the Weaviate service and a text-embedding module (e.g., `text2vec-transformers`).
    -   It will include volume configuration to persist the vector database data on the local disk.
    -   Environment variables will be set to enable the desired modules and configure basic settings.
-   **Outcome:** A self-contained local Weaviate instance that can be started with a single `docker-compose` command.

## 2. Core Layer: Define New Abstractions

To keep the core business logic independent of Weaviate, we will define generic interfaces in the `src/core/interfaces/providers/` directory.

-   **Action:** Create `i_vector_database_provider.py`.
    -   **Methods:**
        -   `create_class_if_not_exists(class_name: str, properties: list)`: To ensure a schema/collection exists.
        -   `upsert_documents(class_name: str, documents: list)`: To add or update text chunks.
        -   `query_similarity(class_name: str, query_embedding: list, limit: int) -> list`: To perform a vector search.
-   **Action:** Create `i_content_segmenter.py`.
    -   **Methods:**
        -   `segment(text: str, chunk_size: int, overlap: int) -> list[str]`: To break down large texts into smaller, manageable chunks for embedding.

## 3. Infrastructure Layer: Implement Weaviate Provider

This layer will contain the concrete implementation for the interfaces defined above.

-   **Action:** Create `src/infrastructure/providers/weaviate_vector_database_provider.py`.
    -   **Details:** This class will implement `IVectorDatabaseProvider` and use the `weaviate-client` Python library to interact with the Weaviate instance running in Docker. It will handle the specifics of Weaviate's API.
-   **Action:** Create `src/infrastructure/providers/simple_content_segmenter.py`.
    -   **Details:** This class will implement `IContentSegmenter` with a straightforward text-splitting strategy (e.g., splitting by paragraphs or a fixed character count with overlap).

## 4. Core Layer: Create New Domain Services

New services will be added to `src/core/services/` to orchestrate the ingestion and querying logic.

-   **Action:** Create `vector_ingestion_service.py`.
    -   **Responsibilities:**
        1.  Fetch a notebook and its sources using the existing repositories.
        2.  For each source, use the `IContentSegmenter` to split its `extracted_text` into chunks.
        3.  Use the `IVectorDatabaseProvider` to `upsert` these chunks into Weaviate.
    -   **Dependencies:** `INotebookRepository`, `ISourceRepository`, `IContentSegmenter`, `IVectorDatabaseProvider`.
-   **Action:** Create `content_similarity_service.py`.
    -   **Responsibilities:**
        1.  Accept a search query and notebook context.
        2.  Use the `IVectorDatabaseProvider` to perform a similarity search.
        3.  Return the relevant content chunks.
    -   **Dependencies:** `IVectorDatabaseProvider`.

## 5. API Layer: Expose New Endpoints

New endpoints will be created in a new router file to make the services accessible via HTTP.

-   **Action:** Create `src/api/vector_search_router.py`.
-   **Endpoints:**
    -   `POST /api/notebooks/{notebook_id}/ingest`: A route to trigger the `VectorIngestionService` for a specific notebook.
    -   `GET /api/notebooks/{notebook_id}/similar`: A route that accepts a `query` parameter and uses the `ContentSimilarityService` to find and return similar content.

## 6. Create Demonstration Script

A script will be created to automate the workflow requested in the prompt.

-   **Action:** Create `scripts/ingest_wikipedia_notebook.py`.
-   **Workflow:**
    1.  Use the existing API client to `POST /api/notebooks` to create a new notebook with a random name.
    2.  For the new notebook's ID, `POST` to the `/api/sources/url` endpoint twice to import the two Wikipedia articles (`Monsters, Inc.` and `Monsters University`).
    3.  Call the new `POST /api/notebooks/{notebook_id}/ingest` endpoint to trigger the segmentation and ingestion into Weaviate.
    4.  Perform a sample query using the `GET /api/notebooks/{notebook_id}/similar?query=...` endpoint to verify the process worked.
    5.  Print status messages to the console at each step.

## 7. Documentation

-   **Action:** Update `README2.md`.
-   **Details:** Add a new section explaining how to start the Weaviate service using `docker-compose.weaviate.yml` and how to run the new `ingest_wikipedia_notebook.py` script.

