"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .notebooks_router import router as notebooks_router
from .sources_router import router as sources_router
from .vector_search_router import router as vector_search_router
from .article_search_router import router as article_search_router

# Create FastAPI application
app = FastAPI(
    title="Discovery API",
    description="A local NotebookLM-like research application following Clean Architecture",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(notebooks_router)
app.include_router(sources_router)
app.include_router(vector_search_router)
app.include_router(article_search_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    from ..infrastructure.database.connection import init_db
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is configured correctly")


@app.get("/")
def root():
    """Serve the main UI."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/app")
def app_redirect():
    """Alternative route to the main UI."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
