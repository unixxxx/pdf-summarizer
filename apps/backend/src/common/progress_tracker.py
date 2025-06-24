"""
Redis-based progress tracking system for async tasks.
"""
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Callable

import redis
from redis import asyncio as aioredis

from ..config import get_settings

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Track task progress in Redis with pub/sub notifications.
    
    Progress data structure in Redis:
    - Key: progress:{task_type}:{task_id}
    - Value: JSON with {progress, stage, message, started_at, updated_at, metadata}
    - TTL: 1 hour after completion
    """
    
    def __init__(self, redis_url: str = None):
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self._async_redis: aioredis.Redis | None = None
        self._sync_redis: redis.Redis | None = None
        self._pubsub_channel = "document_progress"
        
    async def get_async_redis(self) -> aioredis.Redis:
        """Get or create async Redis connection."""
        if not self._async_redis:
            self._async_redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True
            )
        return self._async_redis
    
    @property
    def sync_redis(self) -> redis.Redis:
        """Get or create sync Redis connection for use in sync contexts."""
        if not self._sync_redis:
            self._sync_redis = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
        return self._sync_redis
    
    def _get_key(self, task_type: str, task_id: str) -> str:
        """Generate Redis key for progress tracking."""
        return f"progress:{task_type}:{task_id}"
    
    async def start_progress(
        self,
        task_type: str,
        task_id: str,
        total_steps: int = 100,
        metadata: dict[str, Any] = None
    ) -> None:
        """Initialize progress tracking for a task."""
        redis = await self.get_async_redis()
        key = self._get_key(task_type, task_id)
        
        progress_data = {
            "task_type": task_type,
            "task_id": task_id,
            "progress": 0,
            "total_steps": total_steps,
            "stage": "started",
            "message": "Task started",
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "status": "in_progress"
        }
        
        await redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(progress_data)
        )
        
        # Publish update
        await self._publish_update(progress_data)
    
    async def update_progress(
        self,
        task_type: str,
        task_id: str,
        progress: int,
        stage: str = None,
        message: str = None,
        metadata_update: dict[str, Any] = None
    ) -> None:
        """Update progress for a task."""
        logger.info(f"[PROGRESS_TRACKER] update_progress called: {task_type}/{task_id} - {stage} ({progress}%)")
        redis = await self.get_async_redis()
        key = self._get_key(task_type, task_id)
        
        # Get current data
        current_data = await redis.get(key)
        if not current_data:
            # Initialize if not exists
            await self.start_progress(task_type, task_id)
            current_data = await redis.get(key)
        
        progress_data = json.loads(current_data)
        progress_data.update({
            "progress": min(progress, progress_data.get("total_steps", 100)),
            "updated_at": datetime.utcnow().isoformat(),
        })
        
        if stage:
            progress_data["stage"] = stage
        if message:
            progress_data["message"] = message
        if metadata_update:
            progress_data["metadata"].update(metadata_update)
        
        # Update Redis
        await redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(progress_data)
        )
        
        # Publish update
        await self._publish_update(progress_data)
    
    async def complete_progress(
        self,
        task_type: str,
        task_id: str,
        message: str = "Task completed successfully",
        metadata_update: dict[str, Any] = None
    ) -> None:
        """Mark a task as completed."""
        await self.update_progress(
            task_type,
            task_id,
            progress=100,
            stage="completed",
            message=message,
            metadata_update=metadata_update
        )
        
        # Update status
        redis = await self.get_async_redis()
        key = self._get_key(task_type, task_id)
        current_data = await redis.get(key)
        if current_data:
            progress_data = json.loads(current_data)
            progress_data["status"] = "completed"
            progress_data["completed_at"] = datetime.utcnow().isoformat()
            await redis.setex(
                key,
                timedelta(hours=1),
                json.dumps(progress_data)
            )
            await self._publish_update(progress_data)
    
    async def fail_progress(
        self,
        task_type: str,
        task_id: str,
        error: str,
        metadata_update: dict[str, Any] = None
    ) -> None:
        """Mark a task as failed."""
        redis = await self.get_async_redis()
        key = self._get_key(task_type, task_id)
        
        current_data = await redis.get(key)
        if not current_data:
            await self.start_progress(task_type, task_id)
            current_data = await redis.get(key)
        
        progress_data = json.loads(current_data)
        progress_data.update({
            "status": "failed",
            "stage": "failed",
            "message": f"Task failed: {error}",
            "error": error,
            "updated_at": datetime.utcnow().isoformat(),
            "failed_at": datetime.utcnow().isoformat()
        })
        
        if metadata_update:
            progress_data["metadata"].update(metadata_update)
        
        await redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(progress_data)
        )
        
        await self._publish_update(progress_data)
    
    async def get_progress(
        self,
        task_type: str,
        task_id: str
    ) -> dict[str, Any] | None:
        """Get current progress for a task."""
        redis = await self.get_async_redis()
        key = self._get_key(task_type, task_id)
        
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def get_all_progress(
        self,
        task_type: str = None
    ) -> list[dict[str, Any]]:
        """Get progress for all tasks of a type."""
        redis = await self.get_async_redis()
        pattern = f"progress:{task_type}:*" if task_type else "progress:*"
        
        progress_list = []
        async for key in redis.scan_iter(match=pattern):
            data = await redis.get(key)
            if data:
                progress_list.append(json.loads(data))
        
        return progress_list
    
    async def _publish_update(self, progress_data: dict[str, Any]) -> None:
        """Publish progress update to Redis pub/sub."""
        # Format message for WebSocket connection manager
        user_id = progress_data.get("metadata", {}).get("user_id")
        if not user_id:
            return
        
        # Convert to WebSocket format
        ws_message = {
            "user_id": user_id,
            "data": {
                "type": "document_processing",
                "document_id": progress_data.get("task_id"),
                "stage": progress_data.get("stage", "unknown"),
                "progress": progress_data.get("progress", 0),
                "message": progress_data.get("message", "")
            }
        }
        
        # Add error if present
        if progress_data.get("status") == "failed":
            ws_message["data"]["error"] = progress_data.get("error", "Unknown error")
        
        redis = await self.get_async_redis()
        await redis.publish(
            self._pubsub_channel,
            json.dumps(ws_message)
        )
        
        logger.info(
            f"[PROGRESS_TRACKER] Published: task={progress_data.get('task_type')}/{progress_data.get('task_id')} "
            f"stage={progress_data.get('stage')} progress={progress_data.get('progress')}% "
            f"user={user_id}"
        )
    
    @asynccontextmanager
    async def subscribe_to_updates(self, callback: Callable[[dict[str, Any]], None]):
        """Subscribe to progress updates."""
        redis = await self.get_async_redis()
        pubsub = redis.pubsub()
        
        try:
            await pubsub.subscribe(self._pubsub_channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        progress_data = json.loads(message["data"])
                        await callback(progress_data)
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"Error in progress callback: {e}")
        finally:
            await pubsub.unsubscribe(self._pubsub_channel)
            await pubsub.close()
    
    def _sync_publish_update(self, progress_data: dict[str, Any]) -> None:
        """Sync version of publish update for Celery workers."""
        # Format message for WebSocket connection manager
        user_id = progress_data.get("metadata", {}).get("user_id")
        if not user_id:
            return
        
        # Convert to WebSocket format
        ws_message = {
            "user_id": user_id,
            "data": {
                "type": "document_processing",
                "document_id": progress_data.get("task_id"),
                "stage": progress_data.get("stage", "unknown"),
                "progress": progress_data.get("progress", 0),
                "message": progress_data.get("message", "")
            }
        }
        
        # Add error if present
        if progress_data.get("status") == "failed":
            ws_message["data"]["error"] = progress_data.get("error", "Unknown error")
        
        self.sync_redis.publish(
            self._pubsub_channel,
            json.dumps(ws_message)
        )
        
        logger.info(
            f"[PROGRESS_TRACKER] Published: task={progress_data.get('task_type')}/{progress_data.get('task_id')} "
            f"stage={progress_data.get('stage')} progress={progress_data.get('progress')}% "
            f"user={user_id}"
        )
    
    # Sync methods for use in sync contexts (like Celery workers)
    
    def sync_start_progress(
        self,
        task_type: str,
        task_id: str,
        total_steps: int = 100,
        metadata: dict[str, Any] = None
    ) -> None:
        """Sync version of start_progress for use in sync contexts."""
        key = self._get_key(task_type, task_id)
        
        progress_data = {
            "task_type": task_type,
            "task_id": task_id,
            "progress": 0,
            "total_steps": total_steps,
            "stage": "started",
            "message": "Task started",
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "status": "in_progress"
        }
        
        self.sync_redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(progress_data)
        )
        
        # Publish update
        self._sync_publish_update(progress_data)
    
    def sync_update_progress(
        self,
        task_type: str,
        task_id: str,
        progress: int,
        stage: str = None,
        message: str = None,
        metadata_update: dict[str, Any] = None
    ) -> None:
        """Sync version of update_progress for use in sync contexts."""
        key = self._get_key(task_type, task_id)
        
        # Get current data
        current_data = self.sync_redis.get(key)
        if not current_data:
            self.sync_start_progress(task_type, task_id)
            current_data = self.sync_redis.get(key)
        
        progress_data = json.loads(current_data)
        progress_data.update({
            "progress": min(progress, progress_data.get("total_steps", 100)),
            "updated_at": datetime.utcnow().isoformat(),
        })
        
        if stage:
            progress_data["stage"] = stage
        if message:
            progress_data["message"] = message
        if metadata_update:
            progress_data["metadata"].update(metadata_update)
        
        # Update Redis
        self.sync_redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(progress_data)
        )
        
        # Publish update
        self._sync_publish_update(progress_data)
    
    def sync_complete_progress(
        self,
        task_type: str,
        task_id: str,
        message: str = "Task completed successfully",
        metadata_update: dict[str, Any] = None
    ) -> None:
        """Sync version of complete_progress."""
        self.sync_update_progress(
            task_type,
            task_id,
            progress=100,
            stage="completed",
            message=message,
            metadata_update=metadata_update
        )
        
        # Update status
        key = self._get_key(task_type, task_id)
        current_data = self.sync_redis.get(key)
        if current_data:
            progress_data = json.loads(current_data)
            progress_data["status"] = "completed"
            progress_data["completed_at"] = datetime.utcnow().isoformat()
            self.sync_redis.setex(
                key,
                timedelta(hours=1),
                json.dumps(progress_data)
            )
            self.sync_redis.publish(
                self._pubsub_channel,
                json.dumps(progress_data)
            )
    
    def sync_fail_progress(
        self,
        task_type: str,
        task_id: str,
        error: str,
        metadata_update: dict[str, Any] = None
    ) -> None:
        """Sync version of fail_progress."""
        key = self._get_key(task_type, task_id)
        
        current_data = self.sync_redis.get(key)
        if not current_data:
            self.sync_start_progress(task_type, task_id)
            current_data = self.sync_redis.get(key)
        
        progress_data = json.loads(current_data)
        progress_data.update({
            "status": "failed",
            "stage": "failed",
            "message": f"Task failed: {error}",
            "error": error,
            "updated_at": datetime.utcnow().isoformat(),
            "failed_at": datetime.utcnow().isoformat()
        })
        
        if metadata_update:
            progress_data["metadata"].update(metadata_update)
        
        self.sync_redis.setex(
            key,
            timedelta(hours=1),
            json.dumps(progress_data)
        )
        
        self.sync_redis.publish(
            self._pubsub_channel,
            json.dumps(progress_data)
        )
    
    async def cleanup(self) -> None:
        """Clean up Redis connections."""
        if self._async_redis:
            await self._async_redis.close()
        if self._sync_redis:
            self._sync_redis.close()


# Global instance
progress_tracker = ProgressTracker()