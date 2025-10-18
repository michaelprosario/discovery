# Discovery API

A local NotebookLM-like research application following Clean Architecture principles.

## Overview

This project is a FastAPI-based application that allows users to create notebooks, add sources (files and URLs), and generate summaries and other outputs from the sources in a notebook. The architecture is based on the Clean Architecture principles, with a clear separation between the Core domain logic, the infrastructure concerns, and the API layer.

### Core Concepts

- **Notebooks**: A collection of related sources for a specific project or topic.
- **Sources**: Research materials imported into a notebook, such as files (PDF, DOCX, TXT, MD) and URLs.
- **Outputs**: Generated content, such as summaries or blog posts, created from the sources in a notebook.

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
    uv pip install -r requirements.txt
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

## Project Structure

The project follows the Clean Architecture principles, with the following structure:

-   `src/api`: Contains the FastAPI application, including routers and data transfer objects (DTOs).
-   `src/core`: Contains the core business logic, including entities, services, repositories interfaces, and provider interfaces.
-   `src/infrastructure`: Contains the implementation of the repositories and providers defined in the Core layer, as well as database models and migrations.
-   `tests`: Contains the unit and integration tests.
-   `specs`: Contains the project specifications, including the domain model and user stories.
