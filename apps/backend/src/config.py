import secrets
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


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

    # LLM Configuration
    llm_provider: str = Field(
        default="openai", env="LLM_PROVIDER"
    )  # "openai" or "ollama"

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434", env="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_summarizer",
        env="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")

    # Vector Database Configuration (for pgvector)
    vector_dimension: int = Field(
        default=1536, env="VECTOR_DIMENSION"
    )  # OpenAI embedding dimension

    # PDF Processing Configuration
    max_pdf_size_mb: int = Field(default=10, env="MAX_PDF_SIZE_MB")
    max_pdf_pages: int = Field(default=100, env="MAX_PDF_PAGES")

    # Text Processing Configuration
    chunk_size: int = Field(default=4000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    default_summary_length: int = Field(default=500, env="DEFAULT_SUMMARY_LENGTH")

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")

    # JWT Configuration
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")

    # OAuth2 Configuration
    oauth_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/callback", env="OAUTH_REDIRECT_URI"
    )

    # Google OAuth2
    google_client_id: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(
        default=None, env="GOOGLE_CLIENT_SECRET"
    )
    google_openid_config_url: str = Field(
        default="https://accounts.google.com/.well-known/openid-configuration",
        env="GOOGLE_OPENID_CONFIG_URL",
    )

    # GitHub OAuth2
    github_client_id: Optional[str] = Field(default=None, env="GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = Field(
        default=None, env="GITHUB_CLIENT_SECRET"
    )
    github_authorize_url: str = Field(
        default="https://github.com/login/oauth/authorize", env="GITHUB_AUTHORIZE_URL"
    )
    github_token_url: str = Field(
        default="https://github.com/login/oauth/access_token", env="GITHUB_TOKEN_URL"
    )
    github_api_url: str = Field(
        default="https://api.github.com/user", env="GITHUB_API_URL"
    )

    # Session Configuration
    session_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32), env="SESSION_SECRET_KEY"
    )
    session_cookie_name: str = Field(
        default="pdf_summarizer_session", env="SESSION_COOKIE_NAME"
    )
    session_max_age: int = Field(
        default=86400, env="SESSION_MAX_AGE"
    )  # 24 hours in seconds

    # Security
    allowed_redirect_urls: Union[str, List[str]] = Field(
        default="http://localhost:4200,http://localhost:8000",
        env="ALLOWED_REDIRECT_URLS",
    )

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

    @validator("allowed_redirect_urls")
    def parse_allowed_redirect_urls(cls, v):
        """Parse allowed redirect URLs from environment variable."""
        if isinstance(v, str):
            # Handle comma-separated string
            return [url.strip() for url in v.split(",")]
        elif isinstance(v, list):
            # Already a list, return as is
            return v
        else:
            # Use default
            return ["http://localhost:4200", "http://localhost:8000"]

    @property
    def allowed_redirect_urls_list(self) -> List[str]:
        """Get allowed redirect URLs as a list."""
        if isinstance(self.allowed_redirect_urls, str):
            return [url.strip() for url in self.allowed_redirect_urls.split(",")]
        return self.allowed_redirect_urls

    @property
    def google_oauth_enabled(self) -> bool:
        """Check if Google OAuth is configured."""
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def github_oauth_enabled(self) -> bool:
        """Check if GitHub OAuth is configured."""
        return bool(self.github_client_id and self.github_client_secret)


@lru_cache
def get_settings() -> Settings:
    """
    Create and cache settings instance.
    Using lru_cache ensures we only create one instance.
    """
    return Settings()
