"""Mind Map service - orchestrates mind map generation using retrieval-augmented generation."""
import time
from typing import List, Optional
from uuid import UUID

from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ..interfaces.providers.i_llm_provider import ILlmProvider, LlmGenerationParameters
from ..commands.mindmap_commands import GenerateMindMapCommand
from ..queries.mindmap_queries import MindMapResponse, MindMapSource
from ..queries.vector_queries import SimilaritySearchQuery
from ..results.result import Result


class MindMapService:
    """
    Domain service for generating mind maps using RAG (Retrieval-Augmented Generation).

    This service orchestrates the mind map generation process by:
    1. Retrieving relevant content chunks using vector similarity search
    2. Generating a structured markdown outline using an LLM with the retrieved context
    3. Formatting responses with source citations

    It depends on repository and provider abstractions (DIP).
    """

    def __init__(
        self,
        notebook_repository: INotebookRepository,
        vector_db_provider: IVectorDatabaseProvider,
        llm_provider: ILlmProvider
    ):
        """
        Initialize the service with its dependencies.

        Args:
            notebook_repository: Repository abstraction for notebook operations
            vector_db_provider: Vector database abstraction for similarity search
            llm_provider: LLM abstraction for text generation
        """
        self._notebook_repository = notebook_repository
        self._vector_db_provider = vector_db_provider
        self._llm_provider = llm_provider

    def generate_mindmap(self, command: GenerateMindMapCommand) -> Result[MindMapResponse]:
        """
        Generate a mind map outline from notebook content using RAG.

        Business Logic:
        - Validates notebook exists
        - Performs similarity search to find relevant content
        - Generates structured markdown outline using LLM with retrieved context
        - Returns formatted response with sources

        Args:
            command: GenerateMindMapCommand with prompt and parameters

        Returns:
            Result[MindMapResponse]: Success with mind map response or failure
        """
        start_time = time.time()

        try:
            # Validate notebook exists
            notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
            if notebook_result.is_failure:
                return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

            if notebook_result.value is None:
                return Result.failure(f"Notebook with ID {command.notebook_id} not found")

            # Perform similarity search to get relevant context
            search_query = SimilaritySearchQuery(
                notebook_id=command.notebook_id,
                query_text=command.prompt,
                collection_name=command.collection_name,
                limit=command.max_sources
            )

            search_result = self._vector_db_provider.query_similarity(
                collection_name=search_query.collection_name,
                query_text=search_query.query_text,
                limit=search_query.limit,
                filters={"notebook_id": str(search_query.notebook_id)}
            )

            if search_result.is_failure:
                return Result.failure(f"Failed to search for relevant content: {search_result.error}")

            if not search_result.value:
                return Result.failure("No relevant content found for the prompt")

            # Convert search results to mind map sources
            mindmap_sources = []
            context_chunks = []
            
            for search_item in search_result.value:
                mindmap_source = MindMapSource(
                    text=search_item.get("text", ""),
                    source_id=UUID(search_item["metadata"]["source_id"]) if search_item.get("metadata", {}).get("source_id") else None,
                    chunk_index=search_item.get("metadata", {}).get("chunk_index", 0),
                    relevance_score=search_item.get("certainty", 0.0),
                    source_name=search_item.get("metadata", {}).get("source_name"),
                    source_type=search_item.get("metadata", {}).get("source_type")
                )
                mindmap_sources.append(mindmap_source)
                context_chunks.append(mindmap_source.text)

            # Generate markdown outline using LLM with context
            outline_result = self._generate_outline(
                prompt=command.prompt,
                context_chunks=context_chunks,
                llm_parameters=command.llm_parameters
            )
            
            if outline_result.is_failure:
                return Result.failure(f"Failed to generate outline: {outline_result.error}")

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create mind map response
            mindmap_response = MindMapResponse(
                prompt=command.prompt,
                markdown_outline=outline_result.value,
                sources=mindmap_sources,
                notebook_id=command.notebook_id,
                confidence_score=self._calculate_confidence_score(mindmap_sources),
                processing_time_ms=processing_time_ms
            )

            return Result.success(mindmap_response)

        except Exception as e:
            return Result.failure(f"Mind map generation failed: {str(e)}")

    def _generate_outline(
        self,
        prompt: str,
        context_chunks: List[str],
        llm_parameters: Optional[LlmGenerationParameters] = None
    ) -> Result[str]:
        """
        Generate a markdown outline using LLM with provided context.

        Args:
            prompt: The user's prompt/question
            context_chunks: List of relevant content chunks
            llm_parameters: Optional LLM generation parameters

        Returns:
            Result[str]: Success with generated markdown outline or failure
        """
        try:
            # Build the prompt with context
            full_prompt = self._build_mindmap_prompt(prompt, context_chunks)

            # Set default LLM parameters if not provided
            llm_params = llm_parameters or LlmGenerationParameters(
                temperature=0.4,  # Slightly higher for creative structuring
                max_tokens=2000,
                top_p=0.9
            )

            # Generate outline
            result = self._llm_provider.generate(full_prompt, llm_params)
            if result.is_failure:
                return Result.failure(f"LLM generation failed: {result.error}")

            return Result.success(result.value)

        except Exception as e:
            return Result.failure(f"Outline generation failed: {str(e)}")

    def _build_mindmap_prompt(self, prompt: str, context_chunks: List[str]) -> str:
        """
        Build a mind map generation prompt with question and context.

        Args:
            prompt: The user's prompt/question
            context_chunks: List of relevant content chunks

        Returns:
            str: Formatted prompt for the LLM
        """
        context_section = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(context_chunks)])
        
        full_prompt = f"""You are an expert at creating structured, hierarchical mind maps from information. 
Your task is to create a comprehensive markdown outline that can be visualized as a mind map.

IMPORTANT FORMATTING RULES:
1. Use markdown heading syntax (# for main topic, ## for subtopics, ### for details, etc.)
2. Create a clear hierarchy with proper indentation
3. Start with a single main topic (# heading)
4. Break down into 3-7 main branches (## headings)
5. Add detailed sub-branches as needed (### and #### headings)
6. Keep each point concise (1-2 lines maximum)
7. Use bullet points (-) under headings for additional details when needed
8. Ensure logical flow and relationships between concepts

Based on the provided context, create a mind map outline that addresses: {prompt}

Context from sources:
{context_section}

Generate a well-structured markdown outline suitable for mind map visualization. Focus on:
- Hierarchical organization of information
- Clear relationships between concepts
- Comprehensive coverage of the topic
- Logical grouping of related ideas

Markdown Outline:"""

        return full_prompt

    def _calculate_confidence_score(self, sources: List[MindMapSource]) -> float:
        """
        Calculate a confidence score based on source relevance.

        Args:
            sources: List of mind map sources with relevance scores

        Returns:
            float: Confidence score between 0 and 1
        """
        if not sources:
            return 0.0

        # Calculate weighted average of relevance scores
        total_score = sum(source.relevance_score for source in sources)
        avg_score = total_score / len(sources)
        
        # Apply additional weighting based on number of sources
        source_count_factor = min(len(sources) / 5.0, 1.0)  # More sources = higher confidence
        
        return min(avg_score * source_count_factor, 1.0)
