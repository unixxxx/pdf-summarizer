"""Parallel processing utilities for faster document processing."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from .logger import logger

T = TypeVar('T')


async def process_in_parallel(
    items: list[T],
    processor: Callable[[T], Any],
    max_concurrent: int = 5,
    description: str = "Processing items"
) -> list[Any]:
    """
    Process items in parallel with concurrency control.
    
    Args:
        items: List of items to process
        processor: Async function to process each item
        max_concurrent: Maximum number of concurrent operations
        description: Description for logging
        
    Returns:
        List of results in the same order as input
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(item: T, index: int) -> tuple[int, Any]:
        async with semaphore:
            try:
                result = await processor(item)
                return (index, result)
            except Exception as e:
                logger.error(f"{description} failed for item {index}: {e}")
                return (index, None)
    
    # Create tasks for all items
    tasks = [
        process_with_semaphore(item, i) 
        for i, item in enumerate(items)
    ]
    
    # Process all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    # Sort results by original index
    results.sort(key=lambda x: x[0])
    
    return [result for _, result in results]