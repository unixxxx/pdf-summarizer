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
        self.provider_name: str
        self.model_name: str

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

    async def summarize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Generate a summary of the provided text.

        Args:
            text: Text to summarize
            max_length: Maximum length for summary in words

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
                summary = await self._summarize_short_text(text, max_length)
            else:
                # For longer documents, use map-reduce chain
                summary = await self._summarize_long_text(docs, max_length)

            return summary

        except Exception as e:
            raise SummarizationError(f"Failed to generate summary: {str(e)}") from e

    async def _summarize_short_text(self, text: str, max_length: int) -> str:
        """Summarize short text using direct prompting."""
        prompt = (
            f"""Please provide a comprehensive yet concise summary of the """
            f"""following text. The summary should capture all key points and main ideas.
        Keep the summary under {max_length} words.
        
        Text to summarize:
        {text}
        
        Summary:"""
        )

        response = await self.llm.ainvoke(prompt)
        return response.content.strip()

    async def _summarize_long_text(self, docs: list[Document], max_length: int) -> str:
        """Summarize long text using map-reduce strategy."""
        # For Ollama, use a simpler approach to avoid serialization issues
        if self.settings.llm_provider.lower() == "ollama":
            # Summarize each chunk individually
            chunk_summaries = []
            for doc in docs[:10]:  # Limit to first 10 chunks to avoid timeout
                prompt = f"""Summarize the following text concisely, focusing on key points:

{doc.page_content}

Summary:"""
                response = await self.llm.ainvoke(prompt)
                chunk_summaries.append(response.content.strip())

            # Combine chunk summaries
            combined_text = "\n\n".join(chunk_summaries)

            # Generate final summary
            final_prompt = f"""Create a comprehensive summary of the following summaries, keeping it under {max_length} words:

{combined_text}

Final summary:"""
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

            # Check if summary needs to be shortened
            summary_words = len(summary.split())
            if summary_words > max_length:
                # Further condense the summary
                prompt = f"""Please condense this summary to under {max_length} words 
                while keeping all essential information:
                
                {summary}
                
                Condensed summary:"""

                response = await self.llm.ainvoke(prompt)
                summary = response.content.strip()

            return summary

    async def summarize_pdf(
        self, pdf_text: str, max_length: Optional[int] = None
    ) -> dict[str, Any]:
        """
        Summarize PDF text and return detailed statistics.

        Args:
            pdf_text: Extracted text from PDF
            max_length: Maximum length for summary in words

        Returns:
            Dictionary containing summary and statistics
        """
        # Generate summary
        summary = await self.summarize_text(pdf_text, max_length)

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

        return {"summary": summary, "stats": stats}

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
