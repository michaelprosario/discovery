"""Blog generation service - orchestrates creation of blog posts from notebook sources."""
import time
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..interfaces.repositories.i_notebook_repository import INotebookRepository
from ..interfaces.repositories.i_source_repository import ISourceRepository
from ..interfaces.repositories.i_output_repository import IOutputRepository
from ..interfaces.providers.i_llm_provider import ILlmProvider, LlmGenerationParameters
from ..interfaces.providers.i_content_extraction_provider import IContentExtractionProvider
from ..entities.output import Output
from ..commands.output_commands import GenerateBlogPostCommand
from ..results.result import Result
from ..value_objects.enums import OutputStatus, SourceType


class BlogGenerationService:
    """
    Domain service for generating blog posts from notebook sources.

    This service orchestrates the blog post generation process by:
    1. Validating the notebook exists and has sources
    2. Extracting and aggregating content from all sources
    3. Generating a blog post using an LLM with the aggregated content
    4. Creating and managing the output entity
    
    It depends on repository and provider abstractions (DIP).
    """

    def __init__(
        self,
        notebook_repository: INotebookRepository,
        source_repository: ISourceRepository,
        output_repository: IOutputRepository,
        llm_provider: ILlmProvider,
        content_extraction_provider: IContentExtractionProvider
    ):
        """
        Initialize the service with its dependencies.

        Args:
            notebook_repository: Repository abstraction for notebook operations
            source_repository: Repository abstraction for source operations
            output_repository: Repository abstraction for output operations
            llm_provider: LLM abstraction for text generation
            content_extraction_provider: Content extraction abstraction
        """
        self._notebook_repository = notebook_repository
        self._source_repository = source_repository
        self._output_repository = output_repository
        self._llm_provider = llm_provider
        self._content_extraction_provider = content_extraction_provider

    def generate_blog_post(self, command: GenerateBlogPostCommand) -> Result[Output]:
        """
        Generate a blog post from notebook sources.

        Business Logic:
        - Validates notebook exists and has sources
        - Creates output entity and marks as generating
        - Extracts content from all sources in the notebook
        - Generates blog post using LLM with extracted content
        - Updates output entity with generated content and references

        Args:
            command: GenerateBlogPostCommand with generation parameters

        Returns:
            Result[Output]: Success with completed output or failure
        """
        start_time = time.time()

        try:
            print(f"DEBUG: Starting blog generation for notebook {command.notebook_id}")
            
            # Validate notebook exists
            notebook_result = self._notebook_repository.get_by_id(command.notebook_id)
            if notebook_result.is_failure:
                print(f"DEBUG: Failed to retrieve notebook: {notebook_result.error}")
                return Result.failure(f"Failed to retrieve notebook: {notebook_result.error}")

            if notebook_result.value is None:
                print(f"DEBUG: Notebook not found: {command.notebook_id}")
                return Result.failure(f"Notebook with ID {command.notebook_id} not found")

            notebook = notebook_result.value
            print(f"DEBUG: Found notebook: {notebook.name}, sources: {notebook.source_count}")

            # Check if notebook has sources
            if notebook.source_count == 0:
                print("DEBUG: Notebook has no sources")
                return Result.failure("Cannot generate blog post: notebook has no sources")

            # Create output entity
            print(f"DEBUG: Creating output entity with title: {command.title}")
            output_result = Output.create(
                notebook_id=command.notebook_id,
                title=command.title,
                created_by=command.created_by,
                prompt=command.prompt,
                template_name=command.template_name
            )
            if output_result.is_failure:
                print(f"DEBUG: Failed to create output: {output_result.error}")
                return output_result

            output = output_result.value
            print(f"DEBUG: Created output entity: {output.id}")

            # Add generation metadata
            output.add_metadata("target_word_count", command.target_word_count)
            output.add_metadata("tone", command.tone)
            output.add_metadata("include_references", command.include_references)

            # Save output and mark as generating
            print("DEBUG: Saving output to repository")
            add_result = self._output_repository.add(output)
            if add_result.is_failure:
                print(f"DEBUG: Failed to save output: {add_result.error}")
                return Result.failure(f"Failed to create output: {add_result.error}")

            output = add_result.value
            print(f"DEBUG: Output saved, now marking as generating")
            output.start_generation()

            # Update to mark as generating
            update_result = self._output_repository.update(output)
            if update_result.is_failure:
                print(f"DEBUG: Failed to update output status: {update_result.error}")
                return Result.failure(f"Failed to update output status: {update_result.error}")

            print("DEBUG: Starting content extraction")
            # Extract content from all sources
            content_result = self._extract_notebook_content(command.notebook_id)
            if content_result.is_failure:
                print(f"DEBUG: Content extraction failed: {content_result.error}")
                # Mark as failed
                output.fail_generation(f"Content extraction failed: {content_result.error}")
                self._output_repository.update(output)
                return Result.failure(content_result.error)

            source_content, source_references = content_result.value
            print(f"DEBUG: Content extracted, {len(source_references)} sources, content length: {len(source_content)}")

            # Generate blog post using LLM
            print("DEBUG: Starting blog content generation")
            blog_result = self._generate_blog_content(
                title=command.title,
                source_content=source_content,
                prompt=command.prompt,
                target_word_count=command.target_word_count,
                tone=command.tone,
                template_name=command.template_name
            )

            if blog_result.is_failure:
                print(f"DEBUG: Blog generation failed: {blog_result.error}")
                # Mark as failed
                output.fail_generation(f"Blog generation failed: {blog_result.error}")
                self._output_repository.update(output)
                return Result.failure(blog_result.error)

            blog_content = blog_result.value
            print(f"DEBUG: Blog content generated, length: {len(blog_content)}")

            # Add references if requested
            if command.include_references and source_references:
                blog_content = self._add_references_to_blog(blog_content, source_references)
                print("DEBUG: References added to blog content")

            # Complete the generation
            print("DEBUG: Completing generation")
            completion_result = output.complete_generation(blog_content, source_references)
            if completion_result.is_failure:
                print(f"DEBUG: Failed to complete generation: {completion_result.error}")
                return completion_result

            # Add processing time metadata
            processing_time_ms = int((time.time() - start_time) * 1000)
            output.add_metadata("processing_time_ms", processing_time_ms)

            # Save final output
            print("DEBUG: Saving final output")
            final_result = self._output_repository.update(output)
            if final_result.is_failure:
                print(f"DEBUG: Failed to save final output: {final_result.error}")
                return Result.failure(f"Failed to save final output: {final_result.error}")

            # Update notebook output count
            notebook.increment_output_count()
            self._notebook_repository.update(notebook)
            
            print(f"DEBUG: Blog generation completed successfully")
            return Result.success(final_result.value)

        except Exception as e:
            print(f"DEBUG: Exception in blog generation: {str(e)}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return Result.failure(f"Blog generation failed: {str(e)}")

    def _extract_notebook_content(self, notebook_id: UUID) -> Result[tuple[str, List[str]]]:
        """
        Extract and aggregate content from all sources in a notebook.

        Args:
            notebook_id: UUID of the notebook

        Returns:
            Result[tuple[str, List[str]]]: Success with (aggregated_content, source_references) or failure
        """
        # Get all sources for the notebook
        sources_result = self._source_repository.get_by_notebook(notebook_id)
        if sources_result.is_failure:
            return Result.failure(f"Failed to retrieve sources: {sources_result.error}")

        sources = sources_result.value
        if not sources:
            return Result.failure("No sources found in notebook")

        content_sections = []
        source_references = []

        for source in sources:
            try:
                # Extract content based on source type
                if source.source_type == SourceType.FILE:
                    # Use content extraction provider for files
                    if source.file_path and source.file_type:
                        content_result = self._content_extraction_provider.extract_text(
                            source.file_path, source.file_type
                        )
                        if content_result.is_failure:
                            content_text = f"[Unable to extract content from {source.name}: {content_result.error}]"
                        else:
                            content_text = content_result.value
                    else:
                        content_text = f"[File source {source.name} missing file path or type]"
                
                elif source.source_type == SourceType.URL:
                    # For URL sources, use the extracted content if available
                    content_text = source.extracted_text or f"[No content available for URL: {source.url}]"
                
                else:
                    content_text = f"[Unsupported source type: {source.source_type}]"

                # Add section with source attribution
                section = f"## Source: {source.name}\n\n{content_text}\n\n"
                content_sections.append(section)
                
                # Add to references
                if source.source_type == SourceType.URL and source.url:
                    reference = f"{source.name} - {source.url}"
                else:
                    reference = source.name
                
                source_references.append(reference)

            except Exception as e:
                # Add error note and continue
                error_section = f"## Source: {source.name}\n\n[Error extracting content: {str(e)}]\n\n"
                content_sections.append(error_section)
                
                # Include URL in reference for URL sources, even when extraction fails
                if source.source_type == SourceType.URL and source.url:
                    source_references.append(f"{source.name} - {source.url}")
                else:
                    source_references.append(f"{source.name} (content extraction failed)")

        # Combine all content
        aggregated_content = "\n".join(content_sections)
        
        return Result.success((aggregated_content, source_references))

    def _generate_blog_content(
        self,
        title: str,
        source_content: str,
        prompt: Optional[str],
        target_word_count: int,
        tone: str,
        template_name: Optional[str]
    ) -> Result[str]:
        """
        Generate blog post content using LLM.

        Args:
            title: Blog post title
            source_content: Aggregated source content
            prompt: Optional custom prompt
            target_word_count: Target word count (500-600 words)
            tone: Tone of the blog post
            template_name: Optional template name

        Returns:
            Result[str]: Success with generated blog content or failure
        """
        try:
            # Build the generation prompt
            blog_prompt = self._build_blog_prompt(
                title=title,
                source_content=source_content,
                custom_prompt=prompt,
                target_word_count=target_word_count,
                tone=tone,
                template_name=template_name
            )

            # Set LLM parameters for blog generation
            llm_params = LlmGenerationParameters(
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=2000,  # Allow for longer content
                top_p=0.9
            )

            # Generate blog content
            result = self._llm_provider.generate(blog_prompt, llm_params)
            if result.is_failure:
                return Result.failure(f"LLM generation failed: {result.error}")

            return Result.success(result.value)

        except Exception as e:
            return Result.failure(f"Blog content generation failed: {str(e)}")

    def _build_blog_prompt(
        self,
        title: str,
        source_content: str,
        custom_prompt: Optional[str],
        target_word_count: int,
        tone: str,
        template_name: Optional[str]
    ) -> str:
        """
        Build a prompt for blog post generation.

        Args:
            title: Blog post title
            source_content: Source content to base the blog on
            custom_prompt: Optional custom instructions
            target_word_count: Target word count
            tone: Desired tone
            template_name: Optional template name

        Returns:
            str: Formatted prompt for the LLM
        """
        # Template-specific instructions
        template_instruction = ""
        if template_name:
            template_instruction = f"\nUse the '{template_name}' structure for organizing the content."

        # Custom prompt handling
        custom_instruction = ""
        if custom_prompt:
            custom_instruction = f"\n\nAdditional instructions: {custom_prompt}"

        prompt = f"""You are a skilled content writer creating a blog post. Write a well-structured, engaging blog post with the following requirements:

TITLE: {title}

REQUIREMENTS:
- Target length: {target_word_count} words (aim for 500-600 words)
- Tone: {tone}
- Create engaging, well-structured content
- Use proper headings and paragraphs
- Make it informative and readable
- Include an introduction, main body sections, and conclusion{template_instruction}{custom_instruction}

SOURCE CONTENT:
{source_content}

Please write the blog post based on the source content provided above. Synthesize the information into a cohesive, engaging narrative that flows well and provides value to readers. Do not simply copy the source content - transform it into an original blog post.

BLOG POST:"""

        return prompt

    def _add_references_to_blog(self, blog_content: str, source_references: List[str]) -> str:
        """
        Add reference links/titles to the bottom of the blog post.

        Args:
            blog_content: Generated blog content
            source_references: List of source references

        Returns:
            str: Blog content with references added
        """
        if not source_references:
            return blog_content

        references_section = "\n\n## References\n\n"
        for i, reference in enumerate(source_references, 1):
            references_section += f"{i}. {reference}\n"

        return blog_content + references_section