"""FastAPI router for Mind Map operations."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from ..core.services.mindmap_service import MindMapService
from ..core.interfaces.repositories.i_notebook_repository import INotebookRepository
from ..core.interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ..core.interfaces.providers.i_llm_provider import ILlmProvider, LlmGenerationParameters
from ..core.commands.mindmap_commands import GenerateMindMapCommand
from .dtos import ErrorResponse
from ..infrastructure.database.connection import get_db
from ..infrastructure.repositories.postgres_notebook_repository import PostgresNotebookRepository
from ..infrastructure.providers.vector_database_factory import create_vector_database_provider
from ..infrastructure.providers.gemini_llm_provider import GeminiLlmProvider

router = APIRouter(prefix="/api/notebooks", tags=["mindmap"])

# make sure to read .env file 
from dotenv import load_dotenv
load_dotenv()


def get_collection_name(notebook) -> str:
    """
    Helper to get collection name for a notebook.
    
    Weaviate collection names must:
    - Start with uppercase letter
    - Contain only alphanumeric characters (no hyphens, underscores, etc.)
    - Be a valid class name
    
    Args:
        notebook: Notebook entity
        
    Returns:
        Valid Weaviate collection name
    """    
    collection_name = notebook.name
    # convert whole name to upper case
    collection_name = collection_name.upper()
    # Remove invalid characters
    collection_name = ''.join(char for char in collection_name if char.isalnum())
    return collection_name


# DTOs
class GenerateMindMapRequest(BaseModel):
    """Request to generate a mind map from notebook content."""
    prompt: str = Field(..., min_length=1, max_length=5000, description="Prompt or question for mind map generation")
    max_sources: int = Field(default=10, ge=1, le=50, description="Maximum number of source chunks to use")
    temperature: Optional[float] = Field(default=0.4, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: Optional[int] = Field(default=2000, ge=100, le=4000, description="Maximum tokens for LLM")


class MindMapSourceItem(BaseModel):
    """Source information in mind map response."""
    text: str
    source_id: Optional[UUID]
    chunk_index: int
    relevance_score: float
    source_name: Optional[str] = None
    source_type: Optional[str] = None


class MindMapResponse(BaseModel):
    """Response from mind map generation."""
    prompt: str
    markdown_outline: str
    sources: list[MindMapSourceItem]
    notebook_id: UUID
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None


# Dependency injection
def get_notebook_repository(db = Depends(get_db)):
    return PostgresNotebookRepository(db)

def get_vector_db_provider():
    """Get configured vector database provider using factory."""
    return create_vector_database_provider()

def get_llm_provider():
    return GeminiLlmProvider()

def get_mindmap_service(
    notebook_repository = Depends(get_notebook_repository),
    vector_db_provider = Depends(get_vector_db_provider),
    llm_provider = Depends(get_llm_provider)
):
    return MindMapService(
        notebook_repository=notebook_repository,
        vector_db_provider=vector_db_provider,
        llm_provider=llm_provider
    )


# Endpoints
@router.post(
    "/{notebook_id}/mindmap",
    response_model=MindMapResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Notebook not found"},
        400: {"model": ErrorResponse, "description": "Invalid prompt or parameters"},
        500: {"model": ErrorResponse, "description": "Mind map generation failed"}
    }
)
def generate_mindmap(
    notebook_id: UUID,
    request: GenerateMindMapRequest,
    service: MindMapService = Depends(get_mindmap_service)
):
    """
    Generate a mind map outline from notebook content using RAG.

    This endpoint:
    1. Searches for relevant content chunks in the notebook using vector similarity
    2. Uses an LLM to generate a structured markdown outline based on the retrieved context
    3. Returns the markdown outline with source citations

    The markdown outline can be visualized using markmap.js or similar tools.

    Args:
        notebook_id: UUID of the notebook to generate mind map from
        request: Mind map generation prompt and parameters
        service: Injected mind map service

    Returns:
        Mind map response with markdown outline and sources
    """
    # Get collection name for the notebook
    from ..infrastructure.database.connection import get_db
    db = next(get_db())
    notebook_repo = PostgresNotebookRepository(db)
    notebook_result = notebook_repo.get_by_id(notebook_id)
    
    if notebook_result.is_failure or not notebook_result.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Notebook not found"}
        )
    
    notebook = notebook_result.value
    collection_name = get_collection_name(notebook)
    
    # Create LLM parameters
    llm_parameters = LlmGenerationParameters(
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=0.9
    )
    
    # Create command
    command = GenerateMindMapCommand(
        notebook_id=notebook_id,
        prompt=request.prompt,
        max_sources=request.max_sources,
        collection_name=collection_name,
        llm_parameters=llm_parameters
    )

    # Execute mind map generation
    result = service.generate_mindmap(command)

    if result.is_failure:
        if "not found" in result.error.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": result.error}
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": result.error}
        )

    # Convert domain response to DTO
    mindmap_data = result.value
    return MindMapResponse(
        prompt=mindmap_data.prompt,
        markdown_outline=mindmap_data.markdown_outline,
        sources=[
            MindMapSourceItem(
                text=source.text,
                source_id=source.source_id,
                chunk_index=source.chunk_index,
                relevance_score=source.relevance_score,
                source_name=source.source_name,
                source_type=source.source_type
            )
            for source in mindmap_data.sources
        ],
        notebook_id=mindmap_data.notebook_id,
        confidence_score=mindmap_data.confidence_score,
        processing_time_ms=mindmap_data.processing_time_ms
    )


@router.get(
    "/{notebook_id}/mindmap/viewer",
    response_class=HTMLResponse,
    responses={
        200: {"description": "Mind map viewer HTML page"},
        404: {"model": ErrorResponse, "description": "Notebook not found"}
    }
)
def get_mindmap_viewer(notebook_id: UUID):
    """
    Get the mind map viewer HTML page for a notebook.

    This returns an HTML page with markmap.js integration that can display
    mind maps generated from the notebook.

    Args:
        notebook_id: UUID of the notebook

    Returns:
        HTML page with mind map viewer
    """
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mind Map Viewer - Discovery</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 0.75rem 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            font-size: 1.25rem;
            color: #333;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .controls {{
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }}
        
        .btn {{
            padding: 0.4rem 0.8rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
            transform: translateY(-1px);
        }}
        
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .btn-success {{
            background: #28a745;
            color: white;
        }}
        
        .btn-success:hover {{
            background: #218838;
        }}
        
        .input-group {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
            background: white;
            padding: 0.4rem;
            border-radius: 6px;
        }}
        
        input[type="text"], textarea {{
            padding: 0.4rem 0.6rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.85rem;
            flex: 1;
            min-width: 300px;
        }}
        
        textarea {{
            resize: vertical;
            min-height: 50px;
        }}
        
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 1rem;
            gap: 0.75rem;
        }}
        
        #mindmap-container {{
            flex: 1;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
            position: relative;
            width: 100%;
            height: 100%;
        }}
        
        #mindmap {{
            width: 1300px;
            height: 700px;
        }}
        
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #666;
        }}
        
        .loading-spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .error {{
            color: #dc3545;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 0.75rem;
            border-radius: 6px;
            margin: 0.5rem 0;
        }}
        
        .welcome {{
            text-align: center;
            color: #666;
            padding: 2rem 1rem;
        }}
        
        .welcome h2 {{
            margin-bottom: 0.75rem;
            color: #333;
            font-size: 1.5rem;
        }}
        
        .welcome p {{
            font-size: 0.9rem;
        }}
        
        .stats {{
            display: flex;
            gap: 1.5rem;
            background: rgba(255, 255, 255, 0.9);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            justify-content: center;
            align-items: center;
            font-size: 0.85rem;
            color: #666;
        }}
        
        .stat-item {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
            </svg>
            Mind Map Viewer
        </h1>
        <div class="controls">
            <div class="input-group">
                <textarea id="promptInput" placeholder="Enter your prompt or question to generate a mind map..."></textarea>
                <button class="btn btn-primary" onclick="generateMindMap()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
                    </svg>
                    Generate
                </button>
            </div>
            <button class="btn btn-success" onclick="downloadMarkdown()" id="downloadBtn" style="display: none;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download
            </button>
            <button class="btn btn-secondary" onclick="window.close()">Close</button>
        </div>
    </div>
    
    <div class="main-content">
        <div id="stats" class="stats" style="display: none;">
            <div class="stat-item">
                <strong>Processing Time:</strong>
                <span id="processingTime">-</span>
            </div>
            <div class="stat-item">
                <strong>Confidence:</strong>
                <span id="confidence">-</span>
            </div>
            <div class="stat-item">
                <strong>Sources Used:</strong>
                <span id="sourcesCount">-</span>
            </div>
        </div>
        
        <div id="mindmap-container">
            <div class="welcome">
                <h2>Welcome to Mind Map Viewer</h2>
                <p>Enter a prompt or question above to generate a mind map from your notebook content.</p>
                <p style="margin-top: 1rem; font-size: 0.9rem; color: #999;">
                    The mind map will be generated using AI and visualized here interactively.
                </p>
            </div>
            <svg id="mindmap"></svg>
        </div>
    </div>

    <!-- Load markmap libraries from CDN -->
    <script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.16"></script>
    
    <script>
        const notebookId = '{notebook_id}';
        let currentMarkdown = '';
        
        async function generateMindMap() {{
            const prompt = document.getElementById('promptInput').value.trim();
            if (!prompt) {{
                alert('Please enter a prompt or question');
                return;
            }}
            
            const container = document.getElementById('mindmap-container');
            container.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <p>Generating mind map...</p>
                </div>
                <svg id="mindmap"></svg>
            `;
            
            document.getElementById('stats').style.display = 'none';
            document.getElementById('downloadBtn').style.display = 'none';
            
            try {{
                const response = await fetch(`/api/notebooks/${{notebookId}}/mindmap`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        prompt: prompt,
                        max_sources: 10,
                        temperature: 0.4,
                        max_tokens: 2000
                    }})
                }});
                
                if (!response.ok) {{
                    const error = await response.json();
                    throw new Error(error.detail?.error || 'Failed to generate mind map');
                }}
                
                const data = await response.json();
                currentMarkdown = data.markdown_outline;
                
                // Display statistics
                document.getElementById('processingTime').textContent = `${{data.processing_time_ms}}ms`;
                document.getElementById('confidence').textContent = `${{(data.confidence_score * 100).toFixed(1)}}%`;
                document.getElementById('sourcesCount').textContent = data.sources.length;
                document.getElementById('stats').style.display = 'flex';
                document.getElementById('downloadBtn').style.display = 'flex';
                
                // Render mind map
                container.innerHTML = '<svg id="mindmap"></svg>';
                renderMindMap(currentMarkdown);
                
            }} catch (error) {{
                container.innerHTML = `
                    <div class="error">
                        <strong>Error:</strong> ${{error.message}}
                    </div>
                    <svg id="mindmap"></svg>
                `;
            }}
        }}
        
        function renderMindMap(markdown) {{
            // markmap-autoloader will automatically detect and render the SVG
            const svg = document.getElementById('mindmap');
            
            // Use markmap library to render
            if (window.markmap) {{
                const {{ Transformer, Markmap }} = window.markmap;
                const transformer = new Transformer();
                const {{ root }} = transformer.transform(markdown);
                Markmap.create(svg, {{}}, root);
            }} else {{
                // Fallback: create a temporary element with the markdown
                const pre = document.createElement('pre');
                pre.innerHTML = `<code class="language-markmap">${{markdown}}</code>`;
                svg.parentElement.insertBefore(pre, svg);
                pre.style.display = 'none';
            }}
        }}
        
        function downloadMarkdown() {{
            if (!currentMarkdown) {{
                alert('No mind map to download');
                return;
            }}
            
            const blob = new Blob([currentMarkdown], {{ type: 'text/markdown' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mindmap-${{Date.now()}}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
        
        // Allow Enter key to submit
        document.getElementById('promptInput').addEventListener('keydown', function(e) {{
            if (e.key === 'Enter' && e.ctrlKey) {{
                generateMindMap();
            }}
        }});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
