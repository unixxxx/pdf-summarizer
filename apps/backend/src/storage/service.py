"""Storage service for handling file uploads to S3 or local storage."""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

import aioboto3
from botocore.exceptions import ClientError

from ..common.exceptions import StorageError
from ..config import Settings


class StorageService:
    """Service for handling file storage operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_s3 = settings.s3_enabled
        
        if self.is_s3:
            # Create aioboto3 session for async S3 operations
            self.session = aioboto3.Session(
                aws_access_key_id=settings.s3_access_key_id,
                aws_secret_access_key=settings.s3_secret_access_key,
                region_name=settings.s3_region,
            )
        else:
            # Ensure local storage directory exists
            self.local_path = Path(settings.storage_local_path)
            self.local_path.mkdir(parents=True, exist_ok=True)
    
    async def store_file(
        self,
        content: bytes,
        user_id: str,
        file_type: str,
        original_filename: Optional[str] = None,
    ) -> str:
        """
        Store a file and return its storage path.
        
        Args:
            content: File content as bytes
            user_id: User ID for organizing files
            file_type: Type of file ('pdf' or 'txt')
            original_filename: Original filename for reference
            
        Returns:
            Storage path/key for the file
            
        Raises:
            StorageError: If storage operation fails
        """
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = file_type if file_type in ['pdf', 'txt'] else 'bin'
        filename = f"{file_id}.{extension}"
        
        if self.is_s3:
            # S3 key structure: user_id/file_type/filename
            storage_key = f"{user_id}/{file_type}/{filename}"
            
            try:
                async with self.session.client(
                    's3',
                    endpoint_url=self.settings.s3_endpoint_url
                ) as s3_client:
                    # Upload to S3
                    await s3_client.put_object(
                        Bucket=self.settings.s3_bucket_name,
                        Key=storage_key,
                        Body=content,
                        ContentType=self._get_content_type(extension),
                        Metadata={
                            'original_filename': original_filename or '',
                            'user_id': user_id,
                        }
                    )
                return storage_key
                
            except ClientError as e:
                raise StorageError(f"Failed to upload to S3: {str(e)}")
        else:
            # Local storage: storage_path/user_id/file_type/filename
            user_dir = self.local_path / user_id / file_type
            user_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = user_dir / filename
            storage_key = str(file_path.relative_to(self.local_path))
            
            try:
                # Write file to local storage
                with open(file_path, 'wb') as f:
                    f.write(content)
                return storage_key
                
            except IOError as e:
                raise StorageError(f"Failed to write file locally: {str(e)}")
    
    async def retrieve_file(self, storage_key: str) -> bytes:
        """
        Retrieve a file from storage.
        
        Args:
            storage_key: Storage path/key for the file
            
        Returns:
            File content as bytes
            
        Raises:
            StorageError: If retrieval fails
        """
        if self.is_s3:
            try:
                async with self.session.client(
                    's3',
                    endpoint_url=self.settings.s3_endpoint_url
                ) as s3_client:
                    response = await s3_client.get_object(
                        Bucket=self.settings.s3_bucket_name,
                        Key=storage_key
                    )
                    content = await response['Body'].read()
                    return content
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise StorageError(f"File not found: {storage_key}")
                raise StorageError(f"Failed to retrieve from S3: {str(e)}")
        else:
            file_path = self.local_path / storage_key
            
            if not file_path.exists():
                raise StorageError(f"File not found: {storage_key}")
            
            try:
                with open(file_path, 'rb') as f:
                    return f.read()
            except IOError as e:
                raise StorageError(f"Failed to read file locally: {str(e)}")
    
    async def delete_file(self, storage_key: str) -> None:
        """
        Delete a file from storage.
        
        Args:
            storage_key: Storage path/key for the file
            
        Raises:
            StorageError: If deletion fails
        """
        if self.is_s3:
            try:
                async with self.session.client(
                    's3',
                    endpoint_url=self.settings.s3_endpoint_url
                ) as s3_client:
                    await s3_client.delete_object(
                        Bucket=self.settings.s3_bucket_name,
                        Key=storage_key
                    )
            except ClientError as e:
                # Don't raise error if file doesn't exist
                if e.response['Error']['Code'] != 'NoSuchKey':
                    raise StorageError(f"Failed to delete from S3: {str(e)}")
        else:
            file_path = self.local_path / storage_key
            
            try:
                if file_path.exists():
                    file_path.unlink()
            except IOError as e:
                raise StorageError(f"Failed to delete file locally: {str(e)}")
    
    async def get_file_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """
        Get a presigned URL for file access (S3 only).
        
        Args:
            storage_key: Storage path/key for the file
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL for S3, or local path for local storage
            
        Raises:
            StorageError: If URL generation fails
        """
        if self.is_s3:
            try:
                async with self.session.client(
                    's3',
                    endpoint_url=self.settings.s3_endpoint_url
                ) as s3_client:
                    url = await s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': self.settings.s3_bucket_name,
                            'Key': storage_key
                        },
                        ExpiresIn=expires_in
                    )
                    return url
            except ClientError as e:
                raise StorageError(f"Failed to generate presigned URL: {str(e)}")
        else:
            # For local storage, return the relative path
            # In production, you'd serve these through a proper endpoint
            return f"/api/v1/storage/{storage_key}"
    
    def _get_content_type(self, extension: str) -> str:
        """Get content type for file extension."""
        content_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'bin': 'application/octet-stream',
        }
        return content_types.get(extension, 'application/octet-stream')
    
    async def store_text_as_file(
        self,
        text: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> Tuple[str, int]:
        """
        Store text content as a .txt file.
        
        Args:
            text: Text content to store
            user_id: User ID for organizing files
            title: Optional title for the text file
            
        Returns:
            Tuple of (storage_key, file_size)
            
        Raises:
            StorageError: If storage operation fails
        """
        # Convert text to bytes with UTF-8 encoding
        content = text.encode('utf-8')
        
        # Generate filename from title if provided
        if title:
            # Clean title for use as filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))[:50]
            filename = safe_title.strip() or "text_document"
        else:
            filename = "text_document"
        
        # Store the file
        storage_key = await self.store_file(
            content=content,
            user_id=user_id,
            file_type='txt',
            original_filename=f"{filename}.txt"
        )
        
        return storage_key, len(content)