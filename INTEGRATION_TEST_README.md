# Integration Test for Discovery FastAPI

This directory contains integration tests for the Discovery FastAPI server using the `requests` library.

## Files

1. **integration_test.ipynb** - Jupyter notebook with interactive integration tests
2. **test_integration_manual.py** - Python script version of the integration tests

## Prerequisites

Before running the integration tests, ensure:

1. **FastAPI server is running**:
   ```bash
   uvicorn src.api.main:app --reload
   ```

2. **Database is initialized**:
   ```bash
   # Start PostgreSQL container
   docker-compose -f pgDockerCompose/docker-compose.yaml up -d
   
   # Run migrations
   alembic upgrade head
   ```

3. **Python dependencies are installed**:
   ```bash
   uv pip install -e .
   ```

## Running the Tests

### Option 1: Using Jupyter Notebook

If you have Jupyter installed:

```bash
# Install Jupyter if needed
pip install jupyter

# Start Jupyter
jupyter notebook

# Open integration_test.ipynb and run all cells
```

### Option 2: Using Python Script

Run the integration test script directly:

```bash
python test_integration_manual.py
```

The script will:
- Test server health check
- Create a new notebook via POST request
- Verify notebook creation via GET request
- List all notebooks via GET request
- Add a URL source via POST request (may fail if web fetch provider is not configured)
- Verify source creation via GET request
- List all sources for the notebook via GET request
- Verify the notebook's source count was updated

## What the Tests Demonstrate

These integration tests demonstrate:

1. **POST Operations (Insert)**:
   - Creating a notebook with name, description, and tags
   - Adding a URL source to a notebook

2. **GET Operations (Verify)**:
   - Retrieving a specific notebook by ID
   - Listing all notebooks
   - Retrieving a specific source by ID
   - Listing all sources for a notebook
   - Verifying relationships between notebooks and sources

3. **End-to-End Workflow**:
   - The complete lifecycle of creating resources and verifying them
   - How changes are immediately visible in subsequent GET requests
   - The API's handling of relationships between resources

## Expected Output

When all tests pass successfully, you should see output similar to:

```
============================================================
  Integration Test for Discovery FastAPI Server
============================================================

Testing API at: http://localhost:8000

============================================================
  Step 1: Health Check
============================================================
Status Code: 200
Response: {'status': 'healthy'}

✅ Server is healthy and running!

============================================================
  Step 2: Create a New Notebook (POST)
============================================================
Status Code: 201
Response: {
  "id": "...",
  "name": "Integration Test Notebook ...",
  "description": "This notebook was created by the integration test script",
  ...
}

✅ Successfully created notebook with ID: ...

[... more test output ...]

============================================================
  ✅ ALL TESTS PASSED!
============================================================
```

## Troubleshooting

### Server Connection Error

If you see `ERROR: Cannot connect to server`:
- Ensure the FastAPI server is running: `uvicorn src.api.main:app --reload`
- Check that the server is running on `http://localhost:8000`
- Verify no firewall is blocking the connection

### Source Creation Fails

The URL source creation (Step 5) may fail if:
- The web fetch provider is not properly configured
- Network access is restricted
- The example URL is not accessible

This is expected in some test environments and won't cause the overall test to fail.

### Database Errors

If you see database-related errors:
- Ensure PostgreSQL is running
- Verify database migrations are up to date: `alembic upgrade head`
- Check the `DATABASE_URL` environment variable is correctly set

## Cleanup

The test creates a notebook in your database. To clean it up:

1. Note the notebook ID printed at the end of the test
2. Use the DELETE endpoint:
   ```bash
   curl -X DELETE "http://localhost:8000/api/notebooks/{notebook_id}?cascade=true"
   ```

Or uncomment the cleanup code at the end of the Jupyter notebook.

## Notes

- The tests use the `requests` library which is already available in the project dependencies
- These tests use a live instance of the FastAPI server (not mocked)
- The tests create real data in your database (cleanup manually or use the DELETE endpoint)
- The URL source creation test may fail gracefully if external services are unavailable
