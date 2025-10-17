# Database Migrations Guide

This guide explains how to set up and run database migrations for the Discovery application using Alembic.

## Prerequisites

1. PostgreSQL database running (see docker-compose.yml)
2. Python virtual environment activated
3. All dependencies installed via `uv sync` or `pip install`

## Initial Setup

### 1. Start PostgreSQL Database

Using docker-compose:

```bash
docker-compose up -d
```

Or if you have an existing PostgreSQL container, ensure it's running and note the credentials.

### 2. Configure Database Connection

Set the `DATABASE_URL` environment variable with your PostgreSQL connection string:

```bash
export DATABASE_URL="postgresql://postgres:Foobar321@localhost:5432/postgres"
```

The format is: `postgresql://username:password@host:port/database`

For the Docker setup in this project, the default is:
```bash
export DATABASE_URL="postgresql://discovery_user:discovery_pass@localhost:5432/discovery_db"
```

### 3. Run Initial Migration

Run the migration to create the `notebooks` and `sources` tables:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run migrations
alembic upgrade head
```

This will:
- Create the `notebooks` table with columns: id, name, description, tags, created_at, updated_at, source_count, output_count
- Create the `sources` table with columns: id, notebook_id, name, source_type, file_type, url, file_path, file_size, content_hash, extracted_text, source_metadata, created_at, updated_at, deleted_at
- Create necessary indexes and foreign key constraints

## Verifying the Migration

Connect to your database and verify the tables were created:

```bash
# Using docker exec
docker exec -it discovery_postgres psql -U discovery_user -d discovery_db

# Or using psql directly
psql -h localhost -U discovery_user -d discovery_db
```

Then run:
```sql
-- List all tables
\dt

-- Describe notebooks table
\d notebooks

-- Describe sources table
\d sources

-- List indexes
\di
```

## Common Migration Commands

### Check Current Migration Version
```bash
alembic current
```

### View Migration History
```bash
alembic history --verbose
```

### Upgrade to Latest Version
```bash
alembic upgrade head
```

### Downgrade One Version
```bash
alembic downgrade -1
```

### Downgrade to Specific Version
```bash
alembic downgrade <revision_id>
```

### Downgrade to Base (Remove All Tables)
```bash
alembic downgrade base
```

## Creating New Migrations

### Auto-generate Migration from Model Changes

When you modify the SQLAlchemy models in `src/infrastructure/database/models.py`:

```bash
# Generate migration script (requires database connection)
alembic revision --autogenerate -m "Description of changes"
```

Note: Autogenerate requires a connection to the database to compare the current schema with your models.

### Create Empty Migration Template

```bash
alembic revision -m "Description of changes"
```

Then manually edit the generated file in `src/infrastructure/migrations/versions/`.

## Migration File Structure

```
src/infrastructure/migrations/
├── env.py                 # Alembic environment configuration
├── script.py.mako        # Template for new migration files
├── README                # Alembic README
└── versions/             # Migration version files
    └── 913390ba554c_initial_migration_create_notebooks_and_.py
```

## Troubleshooting

### Connection Refused

If you get "connection refused" errors:

1. Verify PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```

2. Check if the correct port is exposed:
   ```bash
   docker port discovery_postgres
   ```

3. Verify your DATABASE_URL is correct

### Authentication Failed

If you get "password authentication failed":

1. Check your credentials in the DATABASE_URL
2. For Docker containers, verify the environment variables in docker-compose.yml
3. You may need to restart the PostgreSQL container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Alembic Can't Find Models

If migrations can't find your models:

1. Ensure `src/infrastructure/migrations/env.py` correctly imports your Base:
   ```python
   from src.infrastructure.database.models import Base
   target_metadata = Base.metadata
   ```

2. Make sure all model files are imported before Alembic runs
3. Check that your PYTHONPATH includes the project root

### Migration Already Applied

If you get "already applied" errors when running upgrade:

```bash
# Check current version
alembic current

# View history
alembic history

# If needed, stamp the database at a specific revision
alembic stamp <revision_id>
```

## Database Schema Overview

### Notebooks Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Notebook name (unique) |
| description | TEXT | Optional description |
| tags | ARRAY[STRING] | Tags for categorization |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| source_count | INTEGER | Number of sources (cached) |
| output_count | INTEGER | Number of outputs (cached) |

**Indexes:**
- Primary key on `id`
- Index on `name`
- Index on `created_at`
- Unique constraint on `name`

### Sources Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| notebook_id | UUID | Foreign key to notebooks |
| name | VARCHAR(500) | Source name |
| source_type | VARCHAR(20) | 'file' or 'url' |
| file_type | VARCHAR(20) | 'pdf', 'docx', 'txt', etc. |
| url | TEXT | URL for URL sources |
| file_path | TEXT | File path for file sources |
| file_size | BIGINT | File size in bytes |
| content_hash | VARCHAR(64) | SHA256 hash for deduplication |
| extracted_text | TEXT | Extracted content |
| source_metadata | JSON | Additional metadata |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| deleted_at | DATETIME | Soft delete timestamp (NULL if not deleted) |

**Indexes:**
- Primary key on `id`
- Index on `notebook_id`
- Index on `content_hash`
- Index on `deleted_at`
- Index on `created_at`
- Composite index on `(notebook_id, content_hash)` for duplicate detection

**Constraints:**
- Foreign key: `notebook_id` references `notebooks(id)` with CASCADE delete

## Best Practices

1. **Always review autogenerated migrations** before applying them
2. **Test migrations** on a development database first
3. **Backup production data** before running migrations
4. **Use descriptive migration messages** that explain what changed
5. **Never modify existing migration files** once they're committed
6. **Keep migrations small and focused** on a single change
7. **Document complex migrations** with comments in the migration file

## Integration with Application

The application uses the repository pattern to interact with the database:

- `PostgresNotebookRepository` - CRUD operations for notebooks
- `PostgresSourceRepository` - CRUD operations for sources

These repositories are located in `src/infrastructure/repositories/` and implement the interfaces defined in `src/core/interfaces/repositories/`.

## Running Tests

The infrastructure layer has comprehensive unit tests using SQLite in-memory databases:

```bash
# Run all tests
pytest tests/unit/ -v

# Run only repository tests
pytest tests/unit/test_postgres_notebook_repository.py -v
pytest tests/unit/test_postgres_source_repository.py -v

# Run tests with coverage
pytest tests/unit/ --cov=src/infrastructure --cov-report=html
```

All 113 unit tests should pass, including 26 tests for PostgresSourceRepository.
