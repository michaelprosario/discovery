"""LLM provider interface - defined in Core, implemented in Infrastructure."""
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator
from dataclasses import dataclass

from ...results.result import Result


@dataclass
class LlmGenerationParameters:
    """Parameters for LLM generation."""
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: list = None


class ILlmProvider(ABC):
    """
    Interface for Large Language Model operations.

    This interface abstracts LLM operations following the Dependency Inversion Principle.
    Infrastructure layer will provide concrete implementations using specific LLM providers.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        parameters: LlmGenerationParameters = None
    ) -> Result[str]:
        """
        Generate text completion for the given prompt.

        Args:
            prompt: The input prompt for text generation
            parameters: Optional generation parameters (temperature, max_tokens, etc.)

        Returns:
            Result[str]: Success with generated text or failure
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        parameters: LlmGenerationParameters = None
    ) -> AsyncIterator[Result[str]]:
        """
        Generate streaming text completion for the given prompt.

        Args:
            prompt: The input prompt for text generation
            parameters: Optional generation parameters

        Yields:
            Result[str]: Success with text chunks or failure
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> Result[int]:
        """
        Count the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            Result[int]: Success with token count or failure
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Result[Dict[str, Any]]:
        """
        Get information about the current model.

        Returns:
            Result[Dict[str, Any]]: Success with model info (name, max_tokens, etc.) or failure
        """
        pass