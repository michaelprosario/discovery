"""Command objects for QA operations following CQRS pattern."""
from typing import List, Optional
from dataclasses import dataclass
from uuid import UUID

from ..interfaces.providers.i_llm_provider import LlmGenerationParameters


@dataclass
class AskQuestionCommand:
    """Command to ask a question about notebook content using RAG."""
    
    notebook_id: UUID
    question: str
    max_sources: int = 5
    collection_name: str = "discovery_content"
    llm_parameters: Optional[LlmGenerationParameters] = None
    
    def __post_init__(self):
        """Validate command parameters."""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        if self.max_sources <= 0:
            raise ValueError("max_sources must be positive")
        if not self.collection_name:
            raise ValueError("collection_name cannot be empty")


@dataclass
class GenerateAnswerCommand:
    """Command to generate an answer using LLM with context."""
    
    question: str
    context_chunks: List[str]
    notebook_id: UUID
    llm_parameters: Optional[LlmGenerationParameters] = None
    include_citations: bool = True
    
    def __post_init__(self):
        """Validate command parameters."""
        if not self.question or not self.question.strip():
            raise ValueError("Question cannot be empty")
        if not self.context_chunks:
            raise ValueError("Context chunks cannot be empty")