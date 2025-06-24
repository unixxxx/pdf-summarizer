"""Schemas for upload module."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UploadMethod(str, Enum):
    """Upload method options."""
    PRESIGNED_POST = "presigned_post"  # For small files < 100MB
    PRESIGNED_URL = "presigned_url"    # For multipart uploads


class PresignedUrlRequest(BaseModel):
    """Request for generating presigned upload URL."""
    
    filename: str = Field(..., description="Name of the file to upload")
    file_size: int = Field(..., gt=0, description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    file_hash: str = Field(..., description="SHA256 hash of the file content")
    folder_id: str | None = Field(None, description="ID of the folder to upload to")
    upload_method: UploadMethod = Field(
        default=UploadMethod.PRESIGNED_POST,
        description="Upload method to use"
    )


class PresignedUrlResponse(BaseModel):
    """Response with presigned URL for upload."""
    
    upload_url: str = Field(..., description="URL to upload the file to")
    fields: dict[str, Any] = Field(..., description="Form fields to include in upload")
    upload_id: str = Field(..., description="Unique identifier for this upload")
    document_id: str = Field(..., description="ID of the created document record")
    expires_at: datetime = Field(..., description="When the upload URL expires")
    method: UploadMethod = Field(..., description="Upload method to use")
    
    # For multipart uploads
    bucket: str | None = Field(None, description="S3 bucket name")
    key: str | None = Field(None, description="S3 object key")
    credentials: dict[str, str] | None = Field(None, description="Temporary AWS credentials")


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


class InitiateMultipartRequest(BaseModel):
    """Request to initiate multipart upload."""
    
    filename: str = Field(..., description="Name of the file to upload")
    file_size: int = Field(..., gt=0, description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")


class InitiateMultipartResponse(BaseModel):
    """Response for multipart upload initiation."""
    
    upload_id: str = Field(..., description="Multipart upload ID")
    key: str = Field(..., description="S3 object key")
    bucket: str = Field(..., description="S3 bucket name")
    part_size: int = Field(..., description="Recommended part size in bytes")
    total_parts: int = Field(..., description="Total number of parts")


class GetUploadPartUrlRequest(BaseModel):
    """Request for getting presigned URL for a part."""
    
    upload_id: str = Field(..., description="Multipart upload ID")
    key: str = Field(..., description="S3 object key")
    part_number: int = Field(..., ge=1, description="Part number")


class GetUploadPartUrlResponse(BaseModel):
    """Response with presigned URL for uploading a part."""
    
    url: str = Field(..., description="Presigned URL for uploading the part")
    part_number: int = Field(..., description="Part number")
    expires_at: datetime = Field(..., description="When the URL expires")


class CompleteMultipartRequest(BaseModel):
    """Request to complete multipart upload."""
    
    upload_id: str = Field(..., description="Multipart upload ID")
    key: str = Field(..., description="S3 object key")
    parts: list[dict[str, Any]] = Field(..., description="List of uploaded parts")