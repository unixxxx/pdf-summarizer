"""Worker configuration settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class WorkerSettings(BaseSettings):
    """Worker configuration settings."""
    
    # Worker identification
    worker_name: str = Field(default="doculearn-worker", env="WORKER_NAME")
    
    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Database configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/doculearn",
        env="DATABASE_URL"
    )
    
    # LLM configuration
    llm_provider: str = Field(default="ollama", env="LLM_PROVIDER")
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama2", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", env="OLLAMA_EMBEDDING_MODEL")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-ada-002", env="EMBEDDING_MODEL")
    
    # Worker settings
    max_jobs: int = Field(default=2, env="MAX_JOBS")  # Reduced from 10 to prevent CPU overload
    job_timeout: int = Field(default=600, env="JOB_TIMEOUT")  # 10 minutes
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    retry_jobs: bool = Field(default=True, env="RETRY_JOBS")
    max_tries: int = Field(default=3, env="MAX_TRIES")
    retry_failed_on_startup: bool = Field(default=False, env="RETRY_FAILED_ON_STARTUP")
    
    # Performance settings
    cpu_throttle_delay: float = Field(default=0.1, env="CPU_THROTTLE_DELAY")  # Delay between intensive operations
    batch_size: int = Field(default=5, env="BATCH_SIZE")  # Process embeddings in smaller batches
    embedding_concurrency: int = Field(default=2, env="EMBEDDING_CONCURRENCY")  # Limit concurrent embedding operations
    
    # S3 configuration
    aws_access_key_id: str | None = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    s3_bucket_name: str | None = Field(default=None, env="S3_BUCKET_NAME")
    s3_endpoint_url: str | None = Field(default=None, env="S3_ENDPOINT_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or console
    log_http_requests: bool = Field(default=False, env="LOG_HTTP_REQUESTS")  # Enable/disable HTTP request logging
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> WorkerSettings:
    """Get cached worker settings."""
    return WorkerSettings()