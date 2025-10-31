"""Gemini LLM provider implementation using Google Gen AI SDK."""
import os
import asyncio
from typing import Dict, Any, AsyncIterator, Optional

from google import genai
from google.genai import types

from ...core.interfaces.providers.i_llm_provider import ILlmProvider, LlmGenerationParameters
from ...core.results.result import Result


class GeminiLlmProvider(ILlmProvider):
    """
    Concrete implementation of ILlmProvider using Google's Gemini API.

    This provider uses the Google Gen AI SDK to interact with Gemini models.
    """

    def __init__(
        self, 
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash-001"
    ):
        """
        Initialize the Gemini LLM provider.

        Args:
            api_key: Gemini API key (if None, uses environment variable)
            model_name: Name of the Gemini model to use
        """
        self._model_name = model_name
        self._client = None
        
        # Use provided API key or get from environment
        if api_key:
            self._api_key = api_key
        else:
            self._api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            
        if not self._api_key:
            raise ValueError("Gemini API key must be provided via parameter or GEMINI_API_KEY/GOOGLE_API_KEY environment variable")

    def _get_client(self):
        """Get or create Gemini client instance."""
        if self._client is None:
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                raise RuntimeError(f"Failed to create Gemini client: {str(e)}")
        return self._client

    def _convert_parameters(self, parameters: LlmGenerationParameters) -> Dict[str, Any]:
        """Convert LlmGenerationParameters to Gemini config format."""
        if parameters is None:
            parameters = LlmGenerationParameters()
            
        config = {
            "temperature": parameters.temperature,
            "max_output_tokens": parameters.max_tokens,
            "top_p": parameters.top_p,
        }
        
        # Add stop sequences if provided
        if parameters.stop_sequences:
            config["stop_sequences"] = parameters.stop_sequences
            
        return config

    def generate(
        self,
        prompt: str,
        parameters: LlmGenerationParameters = None
    ) -> Result[str]:
        """
        Generate text completion for the given prompt.

        Args:
            prompt: The input prompt for text generation
            parameters: Optional generation parameters

        Returns:
            Result[str]: Success with generated text or failure
        """
        try:
            client = self._get_client()
            config = self._convert_parameters(parameters)
            
            response = client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config)
            )
            
            if not response.text:
                return Result.failure("No text generated from Gemini API")
                
            return Result.success(response.text)
            
        except Exception as e:
            return Result.failure(f"Gemini generation failed: {str(e)}")

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
        try:
            client = self._get_client()
            config = self._convert_parameters(parameters)
            
            # Run the streaming generation in a thread since Gemini SDK is sync
            def _stream_sync():
                return client.models.generate_content_stream(
                    model=self._model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config)
                )
            
            # Execute the sync streaming in a thread pool
            loop = asyncio.get_event_loop()
            stream = await loop.run_in_executor(None, _stream_sync)
            
            for chunk in stream:
                if chunk.text:
                    yield Result.success(chunk.text)
                else:
                    yield Result.failure("Empty chunk received from Gemini stream")
                    
        except Exception as e:
            yield Result.failure(f"Gemini streaming failed: {str(e)}")

    def count_tokens(self, text: str) -> Result[int]:
        """
        Count the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            Result[int]: Success with token count or failure
        """
        try:
            client = self._get_client()
            
            # Use Gemini's count_tokens method
            response = client.models.count_tokens(
                model=self._model_name,
                contents=text
            )
            
            return Result.success(response.total_tokens)
            
        except Exception as e:
            # Fallback: rough estimation (4 chars per token)
            estimated_tokens = len(text) // 4
            return Result.success(estimated_tokens)

    def get_model_info(self) -> Result[Dict[str, Any]]:
        """
        Get information about the current model.

        Returns:
            Result[Dict[str, Any]]: Success with model info or failure
        """
        try:
            # Return basic model information
            model_info = {
                "name": self._model_name,
                "provider": "google_gemini",
                "max_tokens": 1048576,  # Gemini 2.0 Flash context window
                "max_output_tokens": 8192,  # Gemini 2.0 Flash output limit
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_multimodal": True
            }
            
            return Result.success(model_info)
            
        except Exception as e:
            return Result.failure(f"Failed to get model info: {str(e)}")

    def close(self):
        """Close the client connection."""
        if self._client:
            # The Gemini client doesn't require explicit closing
            self._client = None