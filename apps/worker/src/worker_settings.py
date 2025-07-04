"""arq worker settings and configuration."""

from arq import cron
from arq.connections import RedisSettings

from src.chat.processor import process_chat_message
from src.common.config import get_settings
from src.common.cpu_monitor import cpu_monitor
from src.common.database import close_db, init_db
from src.common.logger import logger
from src.document.processor import process_document
from src.embeddings.processor import (
    generate_document_embeddings,
    generate_tag_embeddings,
    update_all_tag_embeddings,
)
from src.flashcard.processor import generate_flashcards
from src.maintenance.tasks import cleanup_orphaned_files
from src.quiz.processor import generate_quiz
from src.summarization.processor import generate_document_summary, summarize_text

settings = get_settings()


async def retry_failed_jobs(ctx):
    """Retry failed jobs from previous runs."""
    from arq import create_pool
    from arq.connections import RedisSettings
    
    logger.info("Checking for failed jobs to retry...")
    
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    async with create_pool(redis_settings) as redis:
        # Get all job keys
        job_keys = await redis.keys("arq:job:*")
        
        failed_count = 0
        retried_count = 0
        
        for key in job_keys:
            job_data = await redis.hgetall(key.decode())
            
            # Check if job failed
            if job_data.get(b'success') == b'false':
                failed_count += 1
                job_id = key.decode().replace('arq:job:', '')
                function = job_data.get(b'function', b'').decode()
                
                # Only retry document processing jobs for now
                if job_id.startswith('doc:') and function == 'process_document':
                    try:
                        # Extract document_id from job_id
                        parts = job_id.split(':')
                        if len(parts) >= 2:
                            document_id = parts[1]
                            
                            # Get job args (stored as msgpack)
                            import msgpack
                            args_data = job_data.get(b'args', b'')
                            if args_data:
                                args = msgpack.unpackb(args_data, raw=False)
                                if len(args) >= 2:
                                    user_id = args[1]
                                    
                                    logger.info(f"Retrying failed job: {job_id}")
                                    
                                    # Delete the old job record
                                    await redis.delete(key.decode())
                                    
                                    # Re-enqueue
                                    job = await redis.enqueue_job(
                                        "process_document",
                                        document_id,
                                        user_id,
                                        _job_id=job_id,
                                        _queue_name="doculearn:queue"
                                    )
                                    retried_count += 1
                    except Exception as e:
                        logger.error(f"Failed to retry job {job_id}: {e}")
        
        if failed_count > 0:
            logger.info(f"Found {failed_count} failed jobs, retried {retried_count}")
        else:
            logger.info("No failed jobs found")


async def startup(ctx):
    """Initialize worker resources on startup."""
    logger.info("Starting DocuLearn worker...")
    
    # Initialize database connection
    await init_db()
    
    # Start CPU monitoring
    await cpu_monitor.start()
    
    # Check for failed jobs and optionally retry them
    if settings.retry_failed_on_startup:
        await retry_failed_jobs(ctx)
    
    logger.info("Worker startup complete")


async def shutdown(ctx):
    """Cleanup worker resources on shutdown."""
    logger.info("Shutting down DocuLearn worker...")
    
    # Stop CPU monitoring
    await cpu_monitor.stop()
    
    # Close database connection
    await close_db()
    
    logger.info("Worker shutdown complete")


class WorkerSettings:
    """arq worker settings."""
    
    # Task functions
    functions = [
        # Document processing
        process_document,
        generate_document_embeddings,
        generate_document_summary,
        summarize_text,
        
        # Content generation
        generate_quiz,
        generate_flashcards,
        
        # Chat
        process_chat_message,
        
        # Tag processing
        generate_tag_embeddings,
        update_all_tag_embeddings,
        
        # Maintenance
        cleanup_orphaned_files,
    ]
    
    # Cron jobs
    cron_jobs = [
        cron(cleanup_orphaned_files, hour=2, minute=0),  # Run at 2 AM daily
    ]
    
    # Redis settings
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    
    # Queue configuration
    queue_name = "doculearn:queue"  # Single queue for all tasks
    # Job IDs will be prefixed to indicate task type:
    # - doc:* for document processing
    # - embed:* for embeddings
    # - summary:* for summarization
    # - quiz:* for quiz generation
    # - flashcard:* for flashcard generation
    # - chat:* for chat processing
    # - maint:* for maintenance
    
    # Worker configuration
    max_jobs = settings.max_jobs
    job_timeout = settings.job_timeout
    health_check_interval = settings.health_check_interval
    retry_jobs = settings.retry_jobs
    max_tries = settings.max_tries
    
    # Keep result for 24 hours
    keep_result = 86400
    
    # Custom settings
    ctx = {
        "settings": settings,
    }
    
    # Startup and shutdown hooks
    on_startup = startup
    on_shutdown = shutdown