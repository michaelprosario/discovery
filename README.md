# Discovery

A local NotebookLM-like research application that helps you organize, analyze, and generate insights from your research materials. Built with Clean Architecture principles for maintainability and testability.

## Purpose & Vision

Discovery empowers researchers, students, and knowledge workers to build comprehensive research notebooks by collecting sources from various formats (PDFs, documents, web articles) and generating intelligent summaries and insights. Think of it as your personal research assistant that:

- **Organizes** your research materials into focused notebooks
- **Ingests** content from files (PDF, DOCX, TXT, MD) and web URLs  
- **Analyzes** your sources using vector-based semantic search
- **Generates** summaries, blog posts, and research outputs using AI
- **Maintains** full data privacy with local-first storage

### Future Roadmap

- **Pluggable Infrastructure**: Support for offline LLMs and embedding models for complete data sovereignty
- **Output Modules**: Generate specialized research artifacts like comparative analyses, executive briefings, and research reports
- **Enhanced Collaboration**: Export and share research notebooks while maintaining privacy controls

## Overview

This FastAPI-based application follows Clean Architecture principles, ensuring clear separation between business logic, infrastructure concerns, and API layers. All your data stays local while leveraging the power of modern AI for content analysis and generation.

### Notebook and sources

![Discovery notebooks](discovery-notebooks.png)

### Ask questions of your sources

![Discovery QA](discovery-question-answer.png)

### Core Concepts

- **Notebooks**: A collection of related sources for a specific project or topic.
- **Sources**: Research materials imported into a notebook, such as files (PDF, DOCX, TXT, MD) and URLs.
- **Outputs**: Generated content, such as summaries or blog posts, created from the sources in a notebook.
- **Vector Search**: Semantic similarity search powered by Weaviate vector database for finding relevant content chunks within notebooks.

## Getting Started for Developers

### Prerequisites

- **Python 3.12+** - Modern Python runtime
- **Docker** - For running PostgreSQL and Weaviate services  
- **uv** - Fast Python package manager (recommended)

### Quick Setup

1. **Clone and navigate to the repository:**
   ```bash
   git clone <repository-url>
   cd discovery
   ```

2. **Install uv (if not already installed):**
   ```bash
   # Unix/macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or using pip
   pip install uv
   ```

3. **Set up the Python environment:**
   ```bash
   # Creates virtual environment and installs all dependencies
   uv sync
   
   # Activate the environment  
   source .venv/bin/activate  # Unix/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

### Environment Variables

Create a `.env` file in the project root with these required variables:

```bash
# Database Configuration
DATABASE_URL="postgresql://postgres:Foobar321@localhost:5432/postgres"

# AI Services
GEMINI_API_KEY="your_gemini_api_key_here"        # For Google Gemini LLM

# Google Search Services
GOOGLE_CUSTOM_SEARCH_API_KEY="your_google_search_api_key"     # For web search features
GOOGLE_CUSTOM_SEARCH_ENGINE_ID="your_search_engine_id"        # Custom search engine ID

# Vector Database (optional - defaults to localhost)
WEAVIATE_URL="http://localhost:8080"             # Local Weaviate instance
WEAVIATE_API_KEY="your_weaviate_cloud_key"       # Only for cloud instances
```

**Environment Variable Details:**

| Variable | Purpose | Required | Default |
|----------|---------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | None |
| `GEMINI_API_KEY` | Google Gemini API access for AI features | Yes | None |
| `GOOGLE_CUSTOM_SEARCH_API_KEY` | Google Custom Search API for web search features | Yes | None |
| `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` | Custom search engine identifier for Google search | Yes | None |
| `WEAVIATE_URL` | Weaviate vector database URL | No | `http://localhost:8080` |
| `WEAVIATE_API_KEY` | Weaviate cloud authentication | No | None |

### Starting Your Discovery Instance

#### 1. Database Setup

Start the PostgreSQL database using Docker:

```bash
# Start PostgreSQL container
docker-compose -f pgDockerCompose/docker-compose.yaml up -d

# Apply database migrations
alembic upgrade head
```

#### 2. Vector Database Setup (Optional but Recommended)

For semantic search capabilities, start Weaviate:

```bash
# Start Weaviate vector database
docker-compose -f weaviateDockerCompose/docker-compose.yaml up -d
```

This provides:
- Weaviate vector database on port 8080
- Text-to-vector transformer for generating embeddings

#### 3. Launch the Application

```bash
# Start the FastAPI server
./scripts/dev.sh

# Or manually:
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Verify Installation

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Create your first notebook**: Use the interactive docs or API endpoints

#### 5. Run the Test Suite

Verify everything works correctly:

```bash
# Run all tests (should pass ~42 tests)
./scripts/test.sh

# Or using uv directly
uv run pytest tests/ -v
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

## Architecture & Clean Code Principles

Discovery follows **Clean Architecture** principles as advocated by Robert C. Martin and Steve Smith (Ardalis), ensuring maintainable, testable, and framework-independent code.

### Core Principles

- **Dependency Inversion**: Dependencies point inward toward the Core business logic
- **Framework Independence**: Core business logic has zero dependencies on external frameworks
- **Interface-Driven Design**: Inner layers define interfaces; outer layers implement them
- **Separation of Concerns**: Clear boundaries between business logic, infrastructure, and presentation

### Architecture Layers

```
┌─────────────────┐
│   API Layer     │  ← FastAPI, Routes, DTOs
│   (src/api/)    │
└────────┬────────┘
         │ depends on
┌────────▼────────┐
│   Core Layer    │  ← Entities, Services, Interfaces  
│   (src/core/)   │     (Framework Independent)
└────────┬────────┘
         │ implements
┌────────▼────────┐
│Infrastructure   │  ← Repositories, Providers, Database
│(src/infrastructure/)│
└─────────────────┘
```

### Clean Architecture Rules Applied

| Rule | Implementation |
|------|----------------|
| **Core Independence** | `src/core/` has minimal dependencies - only domain logic |
| **Interface Definition** | Core defines `INotebookRepository`, Infrastructure implements `SqlNotebookRepository` |
| **Dependency Direction** | API → Core ← Infrastructure (never Core → Infrastructure) |
| **Command/Query Pattern** | Services use structured command/query objects as inputs |
| **Result Pattern** | All services return `Result<T>` objects for consistent error handling |
| **Unit Testing** | Core services are easily testable without external dependencies |

### Project Structure

The project is organized into three main layers:

**Core Layer** (`src/core/`):
- `entities/`: Domain entities (Notebook, Source, etc.)
- `services/`: Business logic services
- `interfaces/`: Abstract interfaces for repositories and providers
- `commands/` & `queries/`: Structured input objects
- `results/`: Standardized result types

**Infrastructure Layer** (`src/infrastructure/`):
- `repositories/`: Database access implementations
- `providers/`: External service implementations (LLM, Vector DB)
- `database/`: Database models and migrations

**API Layer** (`src/api/`):
- `main.py`: FastAPI application setup
- `*_router.py`: Route definitions
- `dtos.py`: Data transfer objects for API serialization

## API Features & Endpoints

### Core Functionality

**Notebook Management:**
- `POST /api/notebooks` - Create new research notebook
- `GET /api/notebooks` - List all notebooks with metadata
- `GET /api/notebooks/{id}` - Get specific notebook details
- `PUT /api/notebooks/{id}` - Update notebook properties
- `DELETE /api/notebooks/{id}` - Delete notebook and all sources

**Source Management:**
- `POST /api/notebooks/{id}/sources/file` - Upload file source (PDF, DOCX, TXT, MD)
- `POST /api/notebooks/{id}/sources/url` - Add web URL as source
- `GET /api/notebooks/{id}/sources` - List all sources in notebook
- `DELETE /api/sources/{id}` - Remove source from notebook

**Content Generation:**
- `POST /api/notebooks/{id}/generate-summary` - Generate AI summary from selected sources
- `POST /api/notebooks/{id}/generate-output` - Create structured outputs (blog posts, briefs)

### Vector Search API

Enable semantic search across your research materials:

- `POST /api/notebooks/{id}/ingest` - Ingest content into vector database
- `GET /api/notebooks/{id}/similar` - Semantic similarity search
- `GET /api/notebooks/{id}/vectors/count` - Get vector count for notebook
- `DELETE /api/notebooks/{id}/vectors` - Clear all vectors for notebook

### Interactive Documentation

Access the full API documentation at: **http://localhost:8000/docs**

### Demo & Testing

Try the vector search capabilities:

```bash
# Run the Wikipedia demo (creates notebook with sample content)
python src/apps/ingest_notebook_into_vectordb.py

# This demonstrates:
# 1. Creating a notebook
# 2. Adding Wikipedia articles as sources  
# 3. Ingesting content for semantic search
# 4. Performing similarity queries
```

## Development & Testing

### Running Tests

The project includes comprehensive test coverage:

```bash
# Run all tests (~42 tests should pass)
./scripts/test.sh

# Or using uv directly  
uv run pytest tests/ -v

# Run specific test suites
uv run pytest tests/unit/ -v      # Unit tests (38 tests)
uv run pytest tests/integration/ -v  # Integration tests (4 tests)
```

### Development Workflow

```bash
# Start development environment
./scripts/dev.sh

# Or activate environment manually
source .venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Contributing

1. Follow Clean Architecture principles
2. Write unit tests for all core business logic
3. Use command/query objects for service inputs
4. Return Result objects from services
5. Keep core layer framework-independent

## Additional Resources

- **User Stories**: `specs/core_stories.md` - Detailed feature requirements
- **Domain Model**: `specs/domain_model.md` - Entity relationships and design
- **Clean Architecture**: `specs/clean_architecture.md` - Architecture guidelines
- **Quick Start**: `QUICK_START.md` - Minimal setup guide

## License

This project is open source. See the repository for license details.
