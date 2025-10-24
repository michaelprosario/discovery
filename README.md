# Discovery API

A local NotebookLM-like research application following Clean Architecture principles.

## Overview

This project is a FastAPI-based application that allows users to create notebooks, add sources (files and URLs), and generate summaries and other outputs from the sources in a notebook. The architecture is based on the Clean Architecture principles, with a clear separation between the Core domain logic, the infrastructure concerns, and the API layer.

### Core Concepts

- **Notebooks**: A collection of related sources for a specific project or topic.
- **Sources**: Research materials imported into a notebook, such as files (PDF, DOCX, TXT, MD) and URLs.
- **Outputs**: Generated content, such as summaries or blog posts, created from the sources in a notebook.
- **Vector Search**: Semantic similarity search powered by Weaviate vector database for finding relevant content chunks within notebooks.

## Getting Started

### Prerequisites

- Python 3.12+
- Docker
- `uv` (recommended, for python environment and package management)

### Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd discovery
    ```

2.  **Create and activate the virtual environment:**

    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    uv pip install -e .
    ```

### Database Setup

This project uses PostgreSQL as its database. A Docker Compose setup is provided for convenience.

1.  **Start the PostgreSQL container:**

    ```bash
    docker-compose -f pgDockerCompose/docker-compose.yaml up -d
    ```

2.  **Run database migrations:**

    The project uses Alembic for database migrations. To apply the latest migrations, run:

    ```bash
    alembic upgrade head
    ```

### Vector Database Setup (Weaviate)

The project includes vector search capabilities powered by Weaviate for semantic similarity search.

1.  **Start the Weaviate container:**

    ```bash
    docker-compose -f docker-compose.weaviate.yml up -d
    ```

    This will start:
    - Weaviate vector database on port 8080
    - Text-to-vector transformer service for generating embeddings

2.  **Set environment variable (optional):**

    By default, the API connects to Weaviate at `http://localhost:8080`. To use a different URL:

    ```bash
    export WEAVIATE_URL="http://your-weaviate-host:8080"
    ```

### Running the Application

To run the FastAPI application, use the following command:

```bash
./scripts/dev.sh
```

The API will be available at `http://localhost:8000`.

### Running Tests

To run the test suite, use the following command:

```bash
./scripts/test.sh
```

### Vector Search Demo

A demonstration script is provided to showcase the vector search capabilities:

```bash
python scripts/ingest_wikipedia_notebook.py
```

This script will:
1. Create a new notebook with a random name
2. Import two Wikipedia articles (Monsters, Inc. and Monsters University)
3. Ingest the content into the vector database
4. Perform sample similarity search queries
5. Display the results

Make sure both the API server and Weaviate are running before executing the demo.

## Project Structure

The project follows the Clean Architecture principles, with the following structure:

-   `src/api`: Contains the FastAPI application, including routers and data transfer objects (DTOs).
-   `src/core`: Contains the core business logic, including entities, services, repositories interfaces, and provider interfaces.
    -   `interfaces/providers/i_vector_database_provider.py`: Interface for vector database operations
    -   `interfaces/providers/i_content_segmenter.py`: Interface for content segmentation
    -   `services/vector_ingestion_service.py`: Service for ingesting content into vector database
    -   `services/content_similarity_service.py`: Service for similarity search
-   `src/infrastructure`: Contains the implementation of the repositories and providers defined in the Core layer, as well as database models and migrations.
    -   `providers/weaviate_vector_database_provider.py`: Weaviate implementation of vector database
    -   `providers/simple_content_segmenter.py`: Content segmentation implementation
-   `tests`: Contains the unit and integration tests.
-   `specs`: Contains the project specifications, including the domain model and user stories.
-   `scripts`: Contains utility scripts including the vector search demo.

## Vector Search API Endpoints

The following vector search endpoints are available:

-   `POST /api/notebooks/{notebook_id}/ingest`: Ingest notebook content into vector database
-   `GET /api/notebooks/{notebook_id}/similar`: Search for similar content using semantic search
-   `GET /api/notebooks/{notebook_id}/vectors/count`: Get count of vectors stored for a notebook
-   `DELETE /api/notebooks/{notebook_id}/vectors`: Delete all vectors for a notebook

See `/docs` for interactive API documentation.
