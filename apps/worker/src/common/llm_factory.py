"""Unified LLM Factory for creating language model and embedding instances."""

from langchain.schema.embeddings import Embeddings
from langchain.schema.language_model import BaseLanguageModel
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .config import WorkerSettings


class LLMProvider:
    """Enumeration of supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"


class EmbeddingDimensions:
    """Standard embedding dimensions for different models."""
    OPENAI_SMALL = 1536  # text-embedding-3-small
    OPENAI_LARGE = 3072  # text-embedding-3-large
    OLLAMA_DEFAULT = 4096  # Most Ollama models
    
    @staticmethod
    def get_dimension(provider: str, model: str | None = None) -> int:
        """Get the embedding dimension for a provider/model combination."""
        if provider == LLMProvider.OPENAI:
            if model and "large" in model:
                return EmbeddingDimensions.OPENAI_LARGE
            return EmbeddingDimensions.OPENAI_SMALL
        return EmbeddingDimensions.OLLAMA_DEFAULT


class UnifiedLLMFactory:
    """Unified factory for creating LLM and embedding instances based on configuration."""
    
    def __init__(self, settings: WorkerSettings):
        """Initialize with settings."""
        self.settings = settings
        self._provider = settings.llm_provider.lower()
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate the provider configuration."""
        if self._provider not in [LLMProvider.OLLAMA, LLMProvider.OPENAI]:
            raise ValueError(f"Unknown LLM provider: {self._provider}")
        
        if self._provider == LLMProvider.OPENAI and not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
    
    def create_chat_model(self, temperature: float = 0.7) -> BaseLanguageModel:
        """
        Create and return the appropriate chat model instance.
        
        Args:
            temperature: Override the default temperature setting
            
        Returns:
            Chat model instance
        """
        if self._provider == LLMProvider.OLLAMA:
            return ChatOllama(
                base_url=self.settings.ollama_base_url,
                model=self.settings.ollama_model,
                temperature=temperature,
                timeout=60,  # 60 second timeout
                request_timeout=60,
            )
        else:  # OpenAI
            return ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=temperature,
                max_tokens=4000,
                request_timeout=60,  # 60 second timeout
                max_retries=3,  # Retry up to 3 times
            )
    
    def create_embeddings_model(self) -> tuple[Embeddings, int]:
        """
        Create and return the appropriate embeddings model instance with its dimension.
        
        Returns:
            Tuple of (embeddings model, embedding dimension)
        """
        if self._provider == LLMProvider.OLLAMA:
            embeddings = OllamaEmbeddings(
                base_url=self.settings.ollama_base_url,
                model=self.settings.ollama_embedding_model,
            )
            # nomic-embed-text has 768 dimensions
            dimension = 768 if self.settings.ollama_embedding_model == "nomic-embed-text" else EmbeddingDimensions.OLLAMA_DEFAULT
        else:  # OpenAI
            embeddings = OpenAIEmbeddings(
                api_key=self.settings.openai_api_key,
                model=self.settings.embedding_model,
                request_timeout=30,  # 30 second timeout for embeddings
                max_retries=3,  # Retry up to 3 times
            )
            dimension = EmbeddingDimensions.get_dimension(
                LLMProvider.OPENAI, 
                self.settings.embedding_model
            )
        
        return embeddings, dimension
    
    def get_provider_info(self) -> dict:
        """Get information about the current LLM provider."""
        base_info = {
            "provider": self._provider,
        }
        
        if self._provider == LLMProvider.OLLAMA:
            base_info.update({
                "model": self.settings.ollama_model,
                "base_url": self.settings.ollama_base_url,
            })
        else:  # OpenAI
            base_info.update({
                "model": self.settings.openai_model,
                "embedding_model": self.settings.embedding_model,
            })
        
        return base_info
    
    @property
    def provider(self) -> str:
        """Get the current provider name."""
        return self._provider
    
    @property
    def is_ollama(self) -> bool:
        """Check if using Ollama provider."""
        return self._provider == LLMProvider.OLLAMA
    
    @property
    def is_openai(self) -> bool:
        """Check if using OpenAI provider."""
        return self._provider == LLMProvider.OPENAI