"""Command objects for Mind Map operations following CQRS pattern."""
from typing import Optional
from dataclasses import dataclass
from uuid import UUID

from ..interfaces.providers.i_llm_provider import LlmGenerationParameters


@dataclass
class GenerateMindMapCommand:
    """Command to generate a mind map from notebook content using RAG."""
    
    notebook_id: UUID
    prompt: str
    max_sources: int = 10
    collection_name: str = "discovery_content"
    llm_parameters: Optional[LlmGenerationParameters] = None
    
    def __post_init__(self):
        """Validate command parameters."""
        if not self.prompt or not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if self.max_sources <= 0:
            raise ValueError("max_sources must be positive")
        if not self.collection_name:
            raise ValueError("collection_name cannot be empty")
