"""Schemas for upload module."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    """Request for generating presigned upload URL."""
    
    filename: str = Field(..., description="Name of the file to upload")
    file_size: int = Field(..., gt=0, description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    file_hash: str = Field(..., description="SHA256 hash of the file content")
    folder_id: str | None = Field(None, description="ID of the folder to upload to")


class PresignedUrlResponse(BaseModel):
    """Response with presigned POST URL and fields."""
    
    upload_id: str = Field(..., description="Unique identifier for this upload")
    document_id: str = Field(..., description="ID of the created document record")
    upload_url: str = Field(..., description="S3 presigned POST URL")
    fields: dict[str, Any] = Field(..., description="Form fields to include in the POST request")
    expires_at: datetime = Field(..., description="When the upload URL expires")


class CompleteUploadRequest(BaseModel):
    """Request to complete an upload."""
    
    upload_id: str = Field(..., description="Upload ID from presigned URL response")
    document_id: str = Field(..., description="Document ID from presigned URL response")
    key: str = Field(..., description="S3 key where file was uploaded")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., gt=0, description="Size of uploaded file")
    folder_id: str | None = Field(None, description="ID of the folder the file was uploaded to")


class CompleteUploadResponse(BaseModel):
    """Response after completing upload."""
    
    document_id: str = Field(..., description="ID of created document")
    status: str = Field(..., description="Current processing status")
    stage: str = Field(..., description="Current processing stage")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")