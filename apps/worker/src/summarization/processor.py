"""Document summarization tasks for the worker."""

from typing import Any

from ..common.config import get_settings
from ..common.llm_factory import UnifiedLLMFactory
from ..common.logger import logger
from ..common.retry import retry_on_llm_error

settings = get_settings()


async def summarize_text(ctx: dict, text: str, options: dict = None) -> dict[str, Any]:
    """
    Summarize arbitrary text.
    
    Args:
        ctx: arq context
        text: Text to summarize
        options: Optional summarization options
        
    Returns:
        Summary text
    """
    try:
        # Initialize LLM factory
        llm_factory = UnifiedLLMFactory(settings)
        llm = llm_factory.create_chat_model(temperature=0.3)
        
        # Create prompt
        style = options.get("style", "balanced") if options else "balanced"
        prompt = f"""Summarize the following text in a {style} style:

{text[:8000]}  # Limit to avoid token limits

Provide a clear, well-structured summary."""
        
        # Generate summary
        @retry_on_llm_error(max_attempts=3)
        async def generate_summary() -> str:
            response = await llm.ainvoke(prompt)
            return response.content
        
        summary = await generate_summary()
        
        logger.info("Text summarized", text_length=len(text), summary_length=len(summary))
        
        return {
            "success": True,
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary)
        }
        
    except Exception as e:
        logger.error("Text summarization failed", error=str(e), exc_info=True)
        raise