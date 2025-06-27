#!/usr/bin/env python
"""Script to retry failed jobs in the worker queue."""

import asyncio
import sys
from datetime import datetime
from arq import create_pool
from arq.connections import RedisSettings

sys.path.append('.')
from src.common.config import get_settings


async def retry_failed_jobs():
    """Retry all failed jobs in the queue."""
    settings = get_settings()
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
                
                # Get job details
                function = job_data.get(b'function', b'').decode()
                args = job_data.get(b'args', b'').decode()
                
                print(f"\nFailed job found: {job_id}")
                print(f"  Function: {function}")
                print(f"  Args: {args[:100]}...")  # Show first 100 chars
                
                # Ask for confirmation
                retry = input("  Retry this job? (y/n): ").lower().strip() == 'y'
                
                if retry:
                    # Parse the function and args to re-enqueue
                    # This is a simplified version - you might need to adjust based on your job structure
                    if function == "process_document":
                        # Extract document_id and user_id from the job_id or args
                        parts = job_id.split(':')
                        if len(parts) >= 2:
                            document_id = parts[1]
                            # You'll need to parse args properly or store user_id in job metadata
                            print(f"  Re-enqueueing document {document_id}...")
                            
                            # Re-enqueue the job
                            job = await redis.enqueue_job(
                                function,
                                document_id,
                                # Add other required args
                                _job_id=job_id,
                                _queue_name="doculearn:queue"
                            )
                            retried_count += 1
                            print(f"  ✓ Job re-enqueued: {job.job_id}")
        
        print(f"\nSummary:")
        print(f"  Failed jobs found: {failed_count}")
        print(f"  Jobs retried: {retried_count}")


async def retry_specific_job(job_id: str):
    """Retry a specific job by ID."""
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    
    async with create_pool(redis_settings) as redis:
        job_key = f"arq:job:{job_id}"
        job_data = await redis.hgetall(job_key)
        
        if not job_data:
            print(f"Job {job_id} not found")
            return
        
        if job_data.get(b'success') != b'false':
            print(f"Job {job_id} did not fail (success={job_data.get(b'success')})")
            return
        
        # Extract job details and re-enqueue
        function = job_data.get(b'function', b'').decode()
        
        # You'll need to properly parse the args based on your job structure
        # This is a simplified example
        if "doc:" in job_id:
            document_id = job_id.split(':')[1]
            user_id = "4f046ab1-2772-42cd-aefb-a9afc5d1d035"  # You'll need to get this properly
            
            job = await redis.enqueue_job(
                "process_document",
                document_id,
                user_id,
                _job_id=job_id,
                _queue_name="doculearn:queue"
            )
            print(f"✓ Job re-enqueued: {job.job_id}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Retry specific job
        job_id = sys.argv[1]
        asyncio.run(retry_specific_job(job_id))
    else:
        # Interactive retry for all failed jobs
        asyncio.run(retry_failed_jobs())