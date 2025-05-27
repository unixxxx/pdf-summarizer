from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "PDF Summarizer API"
    api_version: str = "1.0.0"
    api_description: str = "API for summarizing PDF documents using AI"
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=True, env="API_RELOAD")
    
    # CORS Configuration
    frontend_url: str = Field(default="http://localhost:4200", env="FRONTEND_URL")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # PDF Processing Configuration
    max_pdf_size_mb: int = Field(default=10, env="MAX_PDF_SIZE_MB")
    max_pdf_pages: int = Field(default=100, env="MAX_PDF_PAGES")
    
    # Text Processing Configuration
    chunk_size: int = Field(default=4000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    default_summary_length: int = Field(default=500, env="DEFAULT_SUMMARY_LENGTH")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def max_pdf_size_bytes(self) -> int:
        """Convert MB to bytes for PDF size limit."""
        return self.max_pdf_size_mb * 1024 * 1024
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS allowed origins based on environment."""
        if self.is_production:
            return [self.frontend_url]
        return ["*"]  # Allow all origins in development


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance.
    Using lru_cache ensures we only create one instance.
    """
    return Settings()