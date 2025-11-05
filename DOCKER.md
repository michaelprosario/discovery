# Docker Setup for Discovery API

This document explains how to run the Discovery API using Docker and Docker Compose.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- `.env` file with required environment variables

## Quick Start

### 1. Build and Start Services

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL database on port 5432
- Build and start the FastAPI application on port 8000

### 2. Check Service Status

```bash
docker-compose ps
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# PostgreSQL only
docker-compose logs -f postgres
```

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **API Alternative Docs**: http://localhost:8000/redoc
- **Main UI**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health

## Environment Variables

The docker-compose.yml file uses environment variables from your `.env` file:

- `DATABASE_URL` - PostgreSQL connection string (defaults to internal Docker network)
- `WEAVIATE_URL` - Weaviate instance URL
- `WEAVIATE_KEY` - Weaviate API key
- `GEMINI_API_KEY` - Google Gemini API key
- `GOOGLE_CUSTOM_SEARCH_API_KEY` - Google Custom Search API key
- `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` - Google Custom Search Engine ID

## Common Commands

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Slate)

```bash
docker-compose down -v
```

### Rebuild API Service

```bash
docker-compose build api
docker-compose up -d api
```

### Run Database Migrations

```bash
docker-compose exec api alembic upgrade head
```

### Access PostgreSQL Database

```bash
docker-compose exec postgres psql -U discovery_user -d discovery_db
```

### Shell Access to API Container

```bash
docker-compose exec api bash
```

## Troubleshooting

### API Won't Start

1. Check if PostgreSQL is healthy:
   ```bash
   docker-compose ps
   ```

2. View API logs:
   ```bash
   docker-compose logs api
   ```

### Database Connection Issues

Ensure the `DATABASE_URL` environment variable uses the internal Docker network:
```
DATABASE_URL=postgresql://discovery_user:discovery_pass@postgres:5432/discovery_db
```

### Port Conflicts

If ports 5432 or 8000 are already in use, you can change them in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Use host port 5433 instead of 5432
```

### Rebuild from Scratch

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Development vs Production

### Development Mode (with hot reload)

For development with code hot-reloading, you can mount the source code:

```yaml
volumes:
  - ./src:/app/src
  - ./storage:/app/storage
```

Then restart with:
```bash
docker-compose restart api
```

### Production Mode

The current setup is production-ready. For production:

1. Remove CORS wildcard in `src/api/main.py`
2. Use proper secrets management instead of `.env`
3. Configure proper logging
4. Set up reverse proxy (nginx/traefik)
5. Enable HTTPS

## Network Architecture

```
┌─────────────────────┐
│   Host Machine      │
│   localhost:8000    │
└──────────┬──────────┘
           │
    ┌──────▼──────────────────────┐
    │  discovery-network (bridge) │
    │                             │
    │  ┌─────────────────────┐   │
    │  │  discovery_api      │   │
    │  │  port: 8000         │   │
    │  └──────────┬──────────┘   │
    │             │               │
    │  ┌──────────▼──────────┐   │
    │  │  discovery_postgres │   │
    │  │  port: 5432         │   │
    │  └─────────────────────┘   │
    └─────────────────────────────┘
```

## Storage

- **PostgreSQL Data**: Persisted in Docker volume `postgres_data`
- **Notebooks**: Stored in `./storage` directory (mounted to container)

## Health Checks

Both services include health checks:

- **PostgreSQL**: Checks if database is ready to accept connections
- **API**: Checks if the `/health` endpoint responds successfully
