"""QA/RAG service - orchestrates question answering using retrieval-augmented generation."""
import time
from typing import List, Optional
from uuid import UUID

from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..interfaces.providers.i_vector_database_provider import IVectorDatabaseProvider
from ..interfaces.providers.i_llm_provider import ILlmProvider, LlmGenerationParameters
from ..commands.qa_commands import AskQuestionCommand, GenerateAnswerCommand
from ..queries.qa_queries import QaResponse, QaSource
from ..queries.vector_queries import SimilaritySearchQuery
from ..results.result import Result


class QaRagService:
    """
    Domain service for managing question-answering using RAG (Retrieval-Augmented Generation).

    This service orchestrates the RAG process by:
    1. Retrieving relevant content chunks using vector similarity search
    2. Generating answers using an LLM with the retrieved context
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

    def ask_question(self, command: AskQuestionCommand) -> Result[QaResponse]:
        """
        Ask a question about notebook content using RAG.

        Business Logic:
        - Validates notebook exists
        - Performs similarity search to find relevant content
        - Generates answer using LLM with retrieved context
        - Returns formatted response with sources

        Args:
            command: AskQuestionCommand with question and parameters

        Returns:
            Result[QaResponse]: Success with QA response or failure
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
                query_text=command.question,
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
                return Result.failure("No relevant content found for the question")

            # Convert search results to QA sources
            qa_sources = []
            context_chunks = []
            
            for search_item in search_result.value:
                qa_source = QaSource(
                    text=search_item.get("text", ""),
                    source_id=UUID(search_item["metadata"]["source_id"]) if search_item.get("metadata", {}).get("source_id") else None,
                    chunk_index=search_item.get("metadata", {}).get("chunk_index", 0),
                    relevance_score=search_item.get("certainty", 0.0),
                    source_name=search_item.get("metadata", {}).get("source_name"),
                    source_type=search_item.get("metadata", {}).get("source_type")
                )
                qa_sources.append(qa_source)
                context_chunks.append(qa_source.text)

            # Generate answer using LLM with context
            answer_command = GenerateAnswerCommand(
                question=command.question,
                context_chunks=context_chunks,
                notebook_id=command.notebook_id,
                llm_parameters=command.llm_parameters,
                include_citations=True
            )

            answer_result = self._generate_answer(answer_command)
            if answer_result.is_failure:
                return Result.failure(f"Failed to generate answer: {answer_result.error}")

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create QA response
            qa_response = QaResponse(
                question=command.question,
                answer=answer_result.value,
                sources=qa_sources,
                notebook_id=command.notebook_id,
                confidence_score=self._calculate_confidence_score(qa_sources),
                processing_time_ms=processing_time_ms
            )

            return Result.success(qa_response)

        except Exception as e:
            return Result.failure(f"QA operation failed: {str(e)}")

    def _generate_answer(self, command: GenerateAnswerCommand) -> Result[str]:
        """
        Generate an answer using LLM with provided context.

        Args:
            command: GenerateAnswerCommand with question and context

        Returns:
            Result[str]: Success with generated answer or failure
        """
        try:
            # Build the prompt with context
            prompt = self._build_rag_prompt(command.question, command.context_chunks, command.include_citations)

            # Set default LLM parameters if not provided
            llm_params = command.llm_parameters or LlmGenerationParameters(
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1500,
                top_p=0.9
            )

            # Generate answer
            result = self._llm_provider.generate(prompt, llm_params)
            if result.is_failure:
                return Result.failure(f"LLM generation failed: {result.error}")

            return Result.success(result.value)

        except Exception as e:
            return Result.failure(f"Answer generation failed: {str(e)}")

    def _build_rag_prompt(self, question: str, context_chunks: List[str], include_citations: bool = True) -> str:
        """
        Build a RAG prompt with question and context.

        Args:
            question: The user's question
            context_chunks: List of relevant content chunks
            include_citations: Whether to include citation instructions

        Returns:
            str: Formatted prompt for the LLM
        """
        context_section = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(context_chunks)])
        
        citation_instruction = ""
        if include_citations:
            citation_instruction = """
When referencing information from the context, please cite the source using the format [1], [2], etc. to indicate which context chunk the information came from."""

        prompt = f"""You are a helpful assistant that answers questions based on the provided context. Provide answers around 400 words.  Use only the information from the context to answer the question. If the context doesn't contain enough information to answer the question completely, say so.{citation_instruction}

Context:
{context_section}

Question: {question}

Answer:"""

        return prompt

    def _calculate_confidence_score(self, sources: List[QaSource]) -> float:
        """
        Calculate a confidence score based on source relevance.

        Args:
            sources: List of QA sources with relevance scores

        Returns:
            float: Confidence score between 0 and 1
        """
        if not sources:
            return 0.0

        # Calculate weighted average of relevance scores
        total_score = sum(source.relevance_score for source in sources)
        avg_score = total_score / len(sources)
        
        # Apply additional weighting based on number of sources
        source_count_factor = min(len(sources) / 3.0, 1.0)  # More sources = higher confidence
        
        return min(avg_score * source_count_factor, 1.0)