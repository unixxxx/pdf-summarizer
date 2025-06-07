from typing import Any, Optional

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.schema.language_model import BaseLanguageModel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from ..common.exceptions import OpenAIConfigError, SummarizationError
from ..config import Settings


class SummarizerService:
    """Service for text summarization using LangChain with OpenAI or Ollama."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm: BaseLanguageModel

        # Initialize LLM based on provider
        if settings.llm_provider.lower() == "ollama":
            # Use Ollama for local development
            self.provider_name = "ollama"
            self.model_name = settings.ollama_model
            self.llm = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=settings.openai_temperature,
            )
        else:
            # Use OpenAI
            if not settings.openai_api_key:
                raise OpenAIConfigError()

            self.provider_name = "openai"
            self.model_name = settings.openai_model
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
            )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        

    async def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        format: str = "paragraph",
        instructions: Optional[str] = None,
    ) -> str:
        """
        Generate a summary of the provided text.

        Args:
            text: Text to summarize
            max_length: Maximum length for summary in words
            format: Summary format ('paragraph', 'bullets', or 'keypoints')
            instructions: Additional instructions for summary generation

        Returns:
            Generated summary

        Raises:
            SummarizationError: If summarization fails
        """
        try:
            # Use default if max_length not provided
            max_length = max_length or self.settings.default_summary_length

            # Split text into chunks
            text_chunks = self.text_splitter.split_text(text)

            # Create documents from chunks
            docs = [Document(page_content=chunk) for chunk in text_chunks]

            # Choose strategy based on document size
            if len(docs) == 1:
                # For short documents, use direct prompting
                summary = await self._summarize_short_text(
                    text, max_length, format, instructions
                )
            else:
                # For longer documents, use map-reduce chain
                summary = await self._summarize_long_text(
                    docs, max_length, format, instructions
                )

            return summary

        except Exception as e:
            raise SummarizationError(f"Failed to generate summary: {str(e)}") from e

    async def _summarize_short_text(
        self, text: str, max_length: int, format: str, instructions: Optional[str]
    ) -> str:
        """Summarize short text using direct prompting."""
        # Build format-specific instructions
        format_instructions = {
            "paragraph": "Write the summary as a coherent paragraph.",
            "bullets": (
                "Format the summary as bullet points. "
                "Start each main point with '• '."
            ),
            "keypoints": (
                "Extract and list the key points. "
                "Start each point with a number (1., 2., etc.)."
            ),
        }
        
        format_instruction = format_instructions.get(
            format, format_instructions["paragraph"]
        )
        
        # Build the prompt
        prompt_parts = [
            "Please provide a comprehensive yet concise summary of the "
            "following text.",
            "The summary should capture all key points and main ideas.",
            f"Keep the summary under {max_length} words.",
            format_instruction,
        ]
        
        # Add custom instructions if provided
        if instructions:
            prompt_parts.append(f"Additional requirements: {instructions}")
        
        prompt = (
            "\n".join(prompt_parts)
            + f"\n\nText to summarize:\n{text}\n\nSummary:"
        )

        response = await self.llm.ainvoke(prompt)
        return response.content.strip()

    async def _summarize_long_text(
        self,
        docs: list[Document],
        max_length: int,
        format: str,
        instructions: Optional[str],
    ) -> str:
        """Summarize long text using map-reduce strategy."""
        # For Ollama, use a simpler approach to avoid serialization issues
        if self.settings.llm_provider.lower() == "ollama":
            # Summarize each chunk individually
            chunk_summaries = []
            for doc in docs[:10]:  # Limit to first 10 chunks to avoid timeout
                prompt = (
                    "Summarize the following text concisely, "
                    "focusing on key points:\n\n"
                    f"{doc.page_content}\n\n"
                    "Summary:"
                )
                response = await self.llm.ainvoke(prompt)
                chunk_summaries.append(response.content.strip())

            # Combine chunk summaries
            combined_text = "\n\n".join(chunk_summaries)

            # Build format-specific instructions
            format_instructions = {
                "paragraph": "Write the summary as a coherent paragraph.",
                "bullets": (
                    "Format the summary as bullet points. "
                    "Start each main point with '• '."
                ),
                "keypoints": (
                    "Extract and list the key points. "
                    "Start each point with a number (1., 2., etc.)."
                ),
            }
            
            format_instruction = format_instructions.get(
                format, format_instructions["paragraph"]
            )
            
            # Generate final summary
            final_prompt_parts = [
                f"Create a comprehensive summary of the following summaries, "
                f"keeping it under {max_length} words.",
                format_instruction,
            ]
            
            if instructions:
                final_prompt_parts.append(f"Additional requirements: {instructions}")
            
            final_prompt = (
                "\n".join(final_prompt_parts)
                + f"\n\n{combined_text}\n\nFinal summary:"
            )
            final_response = await self.llm.ainvoke(final_prompt)
            return final_response.content.strip()

        else:
            # Use map-reduce chain for OpenAI
            chain = load_summarize_chain(
                self.llm, chain_type="map_reduce", verbose=False
            )

            # Generate summary
            result = await chain.ainvoke({"input_documents": docs})
            summary = result["output_text"]

            # Apply format and check length
            summary_words = len(summary.split())
            needs_formatting = format != "paragraph"
            needs_shortening = summary_words > max_length
            
            if needs_formatting or needs_shortening or instructions:
                # Build format-specific instructions
                format_instructions = {
                    "paragraph": "Write the summary as a coherent paragraph.",
                    "bullets": (
                        "Format the summary as bullet points. "
                        "Start each main point with '• '."
                    ),
                    "keypoints": (
                        "Extract and list the key points. "
                        "Start each point with a number (1., 2., etc.)."
                    ),
                }
                
                format_instruction = format_instructions.get(
                format, format_instructions["paragraph"]
            )
                
                # Build the refinement prompt
                prompt_parts = []
                if needs_shortening:
                    prompt_parts.append(
                        f"Please condense this summary to under {max_length} "
                        f"words while keeping all essential information."
                    )
                else:
                    prompt_parts.append("Please reformat the following summary.")
                
                prompt_parts.append(format_instruction)
                
                if instructions:
                    prompt_parts.append(f"Additional requirements: {instructions}")
                
                prompt = (
                    "\n".join(prompt_parts)
                    + f"\n\n{summary}\n\nRefined summary:"
                )

                response = await self.llm.ainvoke(prompt)
                summary = response.content.strip()

            return summary

    async def summarize_pdf(
        self,
        pdf_text: str,
        max_length: Optional[int] = None,
        format: str = "paragraph",
        instructions: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Summarize PDF text and return detailed statistics.

        Args:
            pdf_text: Extracted text from PDF
            max_length: Maximum length for summary in words
            format: Summary format ('paragraph', 'bullets', or 'keypoints')
            instructions: Additional instructions for summary generation

        Returns:
            Dictionary containing summary and statistics
        """
        # Generate summary
        summary = await self.summarize_text(pdf_text, max_length, format, instructions)
        
        # Generate tags for the document
        tags = await self.generate_tags(pdf_text, summary)

        # Calculate statistics
        text_chunks = self.text_splitter.split_text(pdf_text)
        original_words = len(pdf_text.split())
        summary_words = len(summary.split())

        stats = {
            "original_length": len(pdf_text),
            "summary_length": len(summary),
            "original_words": original_words,
            "summary_words": summary_words,
            "compression_ratio": round((1 - summary_words / original_words) * 100, 2)
            if original_words > 0
            else 0,
            "chunk_count": len(text_chunks),
        }

        return {"summary": summary, "stats": stats, "tags": tags}
    
    async def generate_tags(self, text: str, summary: str) -> list[str]:
        """
        Generate relevant tags for a document based on its content.
        
        Args:
            text: Full document text
            summary: Document summary
            
        Returns:
            List of generated tags
        """
        try:
            # Use the summary and first part of text for tag generation
            # to avoid sending too much text to the LLM
            text_sample = text[:2000] if len(text) > 2000 else text
            
            prompt = f"""Based on the following document summary and text sample, generate 3-8 relevant tags that categorize this document.

Summary:
{summary}

Text sample:
{text_sample}

Guidelines for tags:
- Tags should be single words or short phrases (2-3 words max)
- Use lowercase letters only
- Separate multi-word tags with hyphens (e.g., "machine-learning")
- Be specific and relevant to the content
- Include both broad categories and specific topics
- Examples: technology, finance, machine-learning, startup, research, tutorial, api-documentation

Return only the tags as a comma-separated list without any additional text or explanation.

Tags:"""

            response = await self.llm.ainvoke(prompt)
            tags_str = response.content.strip()
            
            # Parse and clean tags
            tags = [tag.strip().lower().replace(' ', '-') for tag in tags_str.split(',')]
            # Remove empty tags and limit to 8
            tags = [tag for tag in tags if tag and len(tag) > 1][:8]
            
            return tags
            
        except Exception as e:
            # If tag generation fails, return empty list
            # We don't want to fail the entire summarization process
            print(f"Failed to generate tags: {str(e)}")
            return []

    def get_service_info(self) -> dict[str, Any]:
        """Get information about the summarization service."""
        if self.settings.llm_provider.lower() == "ollama":
            return {
                "provider": "ollama",
                "model": self.settings.ollama_model,
                "base_url": self.settings.ollama_base_url,
                "chunk_size": self.settings.chunk_size,
                "chunk_overlap": self.settings.chunk_overlap,
                "default_summary_length": self.settings.default_summary_length,
            }
        else:
            return {
                "provider": "openai",
                "model": self.settings.openai_model,
                "max_tokens": self.settings.openai_max_tokens,
                "chunk_size": self.settings.chunk_size,
                "chunk_overlap": self.settings.chunk_overlap,
                "default_summary_length": self.settings.default_summary_length,
            }
