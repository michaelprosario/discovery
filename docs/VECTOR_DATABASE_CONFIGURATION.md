# Vector Database Configuration

This application supports multiple vector database providers for storing and querying document embeddings.

## Supported Providers

### 1. Weaviate (Default)

Weaviate is a cloud-native vector search engine with built-in machine learning models.

**Configuration:**

```bash
VECTOR_DB_PROVIDER=weaviate
WEAVIATE_URL=http://localhost:8080  # or your cloud instance URL
WEAVIATE_KEY=your-api-key-here      # required for cloud instances
```

**Local Setup (Docker):**

```bash
cd weaviateDockerCompose
docker-compose up -d
```

### 2. ChromaDB

ChromaDB is a lightweight, open-source embedding database that can run in-memory, locally persisted, or in client-server mode.

**Configuration:**

#### Persistent Local Mode (Recommended for Development)

```bash
VECTOR_DB_PROVIDER=chroma
CHROMA_PERSIST_DIR=./chroma_data  # directory to store data
```

This mode stores all data locally in the specified directory. The data persists between application restarts.

#### Client-Server Mode

```bash
VECTOR_DB_PROVIDER=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

**Running ChromaDB Server (Docker):**

```bash
docker run -p 8000:8000 chromadb/chroma
```

#### In-Memory Mode (Testing Only)

If neither `CHROMA_HOST` nor `CHROMA_PERSIST_DIR` is set, ChromaDB runs in-memory mode. All data is lost when the application stops.

## Switching Between Providers

1. Set the `VECTOR_DB_PROVIDER` environment variable in your `.env` file
2. Configure the provider-specific settings
3. Restart the application

## Feature Comparison

| Feature | Weaviate | ChromaDB |
|---------|----------|----------|
| Cloud Hosting | ✅ Native | ❌ Self-hosted only |
| Local Development | ✅ Docker | ✅ Built-in |
| Persistence | ✅ Always | ✅ Optional |
| Setup Complexity | Medium | Low |
| Embedding Models | Built-in | Built-in |
| Scalability | High | Medium |
| Resource Usage | Higher | Lower |

## Implementation Details

The application uses the **Factory Pattern** to create vector database providers based on configuration:

- **Interface:** `IVectorDatabaseProvider` (defined in `src/core/interfaces/providers/`)
- **Implementations:**
  - `WeaviateVectorDatabaseProvider` (Weaviate)
  - `ChromaVectorDatabaseProvider` (ChromaDB)
- **Factory:** `create_vector_database_provider()` (in `src/infrastructure/providers/vector_database_factory.py`)

This design follows **Clean Architecture** principles, keeping the core business logic independent of specific vector database technologies.

## Collection Naming

### Weaviate
- Collection names must start with an uppercase letter
- Only alphanumeric characters allowed
- Example: `MYNOTEBOOK123`

### ChromaDB
- Collection names must be 3-63 characters
- Lowercase letters, numbers, underscores, and hyphens allowed
- Example: `mynotebook_123`

The application automatically handles these naming conventions when creating collections.

## Troubleshooting

### ChromaDB "Import could not be resolved" errors

If you see import errors, install ChromaDB:

```bash
pip install chromadb>=0.4.0
```

### Connection errors

**Weaviate:**
- Verify Weaviate is running: `curl http://localhost:8080/v1/meta`
- Check Docker containers: `docker ps`

**ChromaDB:**
- If using server mode, verify it's running: `curl http://localhost:8000/api/v1/heartbeat`
- If using persistent mode, ensure the directory is writable

### Performance considerations

**For small to medium datasets (< 1M vectors):**
- ChromaDB in persistent mode is simpler and faster to set up

**For large datasets or production:**
- Weaviate offers better scalability and performance
- Consider using Weaviate Cloud for managed hosting
