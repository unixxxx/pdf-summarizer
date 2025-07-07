"""Storage service for handling file uploads to S3 or local storage."""

import logging
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import UUID

import aioboto3
import aiofiles
import aiofiles.os
from botocore.exceptions import ClientError
from shared.models import Document
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import StorageError
from ..config import Settings

logger = logging.getLogger(__name__)


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
        original_filename: str | None = None,
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
                            'original_filename': self._safe_ascii_encode(original_filename or ''),
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
                # Write file to local storage asynchronously
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
                return storage_key
                
            except OSError as e:
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
                async with aiofiles.open(file_path, 'rb') as f:
                    return await f.read()
            except OSError as e:
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
                    await aiofiles.os.remove(str(file_path))
            except OSError as e:
                raise StorageError(f"Failed to delete file locally: {str(e)}")
    
    async def delete_files_batch(self, storage_keys: list[str]) -> dict[str, bool]:
        """
        Delete multiple files from storage in batch.
        
        Args:
            storage_keys: List of storage paths/keys for the files
            
        Returns:
            Dict mapping storage_key to success status
        """
        if not storage_keys:
            return {}
            
        results = {}
        
        if self.is_s3:
            try:
                async with self.session.client(
                    's3',
                    endpoint_url=self.settings.s3_endpoint_url
                ) as s3_client:
                    # S3 allows batch deletion of up to 1000 objects at once
                    for i in range(0, len(storage_keys), 1000):
                        batch = storage_keys[i:i+1000]
                        delete_objects = [{'Key': key} for key in batch]
                        
                        response = await s3_client.delete_objects(
                            Bucket=self.settings.s3_bucket_name,
                            Delete={
                                'Objects': delete_objects,
                                'Quiet': True  # Only return errors
                            }
                        )
                        
                        # Mark all as successful initially
                        for key in batch:
                            results[key] = True
                            
                        # Mark failures
                        if 'Errors' in response:
                            for error in response['Errors']:
                                key = error['Key']
                                # Ignore "not found" errors
                                if error['Code'] != 'NoSuchKey':
                                    results[key] = False
                                    logger.error(f"Failed to delete {key}: {error['Message']}")
                                    
            except ClientError as e:
                logger.error(f"Batch delete failed: {str(e)}")
                # Mark all as failed
                for key in storage_keys:
                    results[key] = False
        else:
            # For local storage, use asyncio to delete files concurrently
            import asyncio
            
            async def delete_local_file(key: str) -> tuple[str, bool]:
                file_path = self.local_path / key
                try:
                    if file_path.exists():
                        await aiofiles.os.remove(str(file_path))
                    return key, True
                except OSError as e:
                    logger.error(f"Failed to delete {key}: {str(e)}")
                    return key, False
            
            # Delete files concurrently with a limit
            tasks = [delete_local_file(key) for key in storage_keys]
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed:
                if isinstance(result, Exception):
                    logger.error(f"Batch delete error: {result}")
                else:
                    key, success = result
                    results[key] = success
                    
        return results
    
    async def get_file_url(self, storage_key: str, expires_in: int = 3600, filename: str | None = None) -> str:
        """
        Get a presigned URL for file access (S3 only).
        
        Args:
            storage_key: Storage path/key for the file
            expires_in: URL expiration time in seconds
            filename: Optional filename for Content-Disposition header
            
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
                    params = {
                        'Bucket': self.settings.s3_bucket_name,
                        'Key': storage_key
                    }
                    
                    # Add Content-Disposition header to force download
                    if filename:
                        params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
                    
                    url = await s3_client.generate_presigned_url(
                        'get_object',
                        Params=params,
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
    
    def _safe_ascii_encode(self, text: str) -> str:
        """
        Safely encode text to ASCII for S3 metadata.
        Non-ASCII characters are encoded using Unicode escape sequences.
        """
        if not text:
            return ''
        
        # Use unicode-escape encoding and then decode to get ASCII-safe string
        # This converts non-ASCII characters to \\uXXXX format
        encoded = text.encode('unicode-escape').decode('ascii')
        
        # Limit length to ensure it fits in S3 metadata (max 2KB)
        return encoded[:1024]
    
    async def store_text_as_file(
        self,
        text: str,
        user_id: str,
        title: str | None = None,
    ) -> tuple[str, int]:
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
    
    async def create_presigned_post(
        self,
        key: str,
        expires_in: int = 3600,
        content_type: str | None = None,
        max_size: int | None = None,
    ) -> dict:
        """
        Generate a presigned POST URL for direct upload to S3.
        
        Args:
            key: S3 key where the file will be uploaded
            expires_in: URL expiration time in seconds
            content_type: Optional content type restriction
            max_size: Optional maximum file size in bytes
            
        Returns:
            Dictionary with 'url' and 'fields' for the presigned POST
            
        Raises:
            StorageError: If presigned POST generation fails or S3 is not enabled
        """
        if not self.is_s3:
            raise StorageError("Presigned POST URLs are only available with S3 storage")
        
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.settings.s3_endpoint_url
            ) as s3_client:
                # Build conditions for the presigned POST
                conditions = []
                fields = {}
                
                if content_type:
                    conditions.append({"Content-Type": content_type})
                    fields["Content-Type"] = content_type
                
                if max_size:
                    conditions.append(["content-length-range", 0, max_size])
                
                # Generate presigned POST
                response = await s3_client.generate_presigned_post(
                    Bucket=self.settings.s3_bucket_name,
                    Key=key,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expires_in
                )
                
                return response
                
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned POST: {str(e)}")
    
    async def get_document_download_info(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """
        Get download information for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            db: Database session
            
        Returns:
            Dictionary with download_url, filename, and is_text_document flag
            
        Raises:
            StorageError: If document not found or access denied
        """
        # Get document from database
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise StorageError("Document not found")
        
        if not document.storage_path:
            # For text documents, we need a different approach
            if document.extracted_text:
                # Ensure filename has .txt extension for text documents
                filename = document.filename
                if not filename.endswith('.txt'):
                    filename = filename.rsplit('.', 1)[0] + '.txt'
                
                # Return JSON with a special flag for text documents
                return {
                    "download_url": f"/api/v1/storage/text/{document_id}",
                    "filename": filename,
                    "is_text_document": True
                }
            else:
                raise StorageError("Document content not available")
        
        # For S3, generate presigned URL
        if self.is_s3:
            try:
                presigned_url = await self.get_file_url(
                    document.storage_path,
                    expires_in=3600,  # 1 hour
                    filename=document.filename
                )
                return {
                    "download_url": presigned_url,
                    "filename": document.filename
                }
            except Exception as e:
                raise StorageError(f"Failed to generate download URL: {str(e)}")
        
        # For local storage, return the file path as URL
        return {
            "download_url": f"/api/v1/storage/{document.storage_path}",
            "filename": document.filename
        }
    
    async def stream_download(
        self,
        storage_key: str,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream download file from storage in chunks.
        
        Args:
            storage_key: Storage path/key for the file
            chunk_size: Size of each chunk to yield
            
        Yields:
            File content in chunks
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
                    
                    # Stream body
                    async for chunk in response['Body'].iter_chunks(chunk_size):
                        yield chunk
                        
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise StorageError(f"File not found: {storage_key}")
                raise StorageError(f"Failed to stream from S3: {str(e)}")
        else:
            file_path = self.local_path / storage_key
            
            if not file_path.exists():
                raise StorageError(f"File not found: {storage_key}")
            
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    while True:
                        chunk = await f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            except OSError as e:
                raise StorageError(f"Failed to stream file locally: {str(e)}")
    
    async def get_text_document_content(
        self,
        document_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> tuple[bytes, str]:
        """
        Get text document content as bytes with filename.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            db: Database session
            
        Returns:
            Tuple of (content_bytes, filename)
            
        Raises:
            StorageError: If document not found or content not available
        """
        # Get document from database
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise StorageError("Document not found")
        
        if not document.extracted_text:
            raise StorageError("Document content not available")
        
        # Generate text file content
        content = document.extracted_text.encode('utf-8')
        
        # Ensure filename has .txt extension
        filename = document.filename
        if not filename.endswith('.txt'):
            filename = filename.rsplit('.', 1)[0] + '.txt'
        
        return content, filename
    
    async def get_file_with_access_check(
        self,
        storage_path: str,
        user_id: UUID,
    ) -> bytes:
        """
        Retrieve a file from storage with access control.
        
        Args:
            storage_path: Storage path/key for the file
            user_id: User ID for access control
            
        Returns:
            File content as bytes
            
        Raises:
            StorageError: If access denied or file not found
        """
        # Security: Ensure the user can only access their own files
        if not storage_path.startswith(str(user_id)):
            raise StorageError("Access denied")
        
        # Retrieve the file using existing method
        return await self.retrieve_file(storage_path)
    
    def get_content_type_for_path(self, storage_path: str) -> str:
        """
        Determine content type based on file path.
        
        Args:
            storage_path: Storage path/key for the file
            
        Returns:
            MIME content type string
        """
        if storage_path.endswith('.pdf'):
            return "application/pdf"
        elif storage_path.endswith('.txt'):
            return "text/plain; charset=utf-8"
        else:
            return "application/octet-stream"