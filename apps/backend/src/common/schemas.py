from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {}
        }
    )


class HealthResponse(BaseSchema):
    """Health check response schema."""
    
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current UTC timestamp")
    services: dict[str, bool] = Field(default_factory=dict, description="Status of dependent services")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z",
                "services": {
                    "openai": True,
                    "pdf_processor": True
                }
            }
        }
    )


class ErrorResponse(BaseSchema):
    """Standard error response schema."""
    
    detail: str = Field(..., description="Error description")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "File not found",
                "status_code": 404,
                "timestamp": "2024-01-01T00:00:00Z",
                "path": "/api/v1/resource"
            }
        }
    )


class MessageResponse(BaseSchema):
    """Simple message response schema."""
    
    message: str = Field(..., description="Response message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully"
            }
        }
    )