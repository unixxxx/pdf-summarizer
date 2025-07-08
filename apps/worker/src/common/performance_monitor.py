"""Performance monitoring utilities for the worker."""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from .logger import logger


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.metrics: dict[str, Any] = {}
    
    def start(self):
        """Start timing the operation."""
        self.start_time = time.time()
        return self
    
    def add_metric(self, key: str, value: Any):
        """Add a custom metric."""
        self.metrics[key] = value
    
    def stop(self):
        """Stop timing and log the results."""
        if self.start_time is None:
            return
        
        duration = time.time() - self.start_time
        
        logger.info(
            f"Performance: {self.operation_name}",
            duration_seconds=round(duration, 3),
            **self.metrics
        )
        
        return duration


@asynccontextmanager
async def monitor_performance(operation_name: str, **initial_metrics):
    """
    Context manager for monitoring async operation performance.
    
    Usage:
        async with monitor_performance("embedding_generation", chunks=100) as monitor:
            # Do work
            monitor.add_metric("embeddings_created", 100)
    """
    monitor = PerformanceMonitor(operation_name)
    monitor.start()
    
    # Add initial metrics
    for key, value in initial_metrics.items():
        monitor.add_metric(key, value)
    
    try:
        yield monitor
    finally:
        monitor.stop()


class BatchPerformanceTracker:
    """Track performance across multiple batches."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.batch_times: list[float] = []
        self.batch_sizes: list[int] = []
        self.start_time = time.time()
    
    def record_batch(self, batch_size: int, batch_time: float):
        """Record a batch completion."""
        self.batch_times.append(batch_time)
        self.batch_sizes.append(batch_size)
    
    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        if not self.batch_times:
            return {}
        
        total_items = sum(self.batch_sizes)
        total_time = time.time() - self.start_time
        avg_batch_time = sum(self.batch_times) / len(self.batch_times)
        items_per_second = total_items / total_time if total_time > 0 else 0
        
        return {
            "total_items": total_items,
            "total_batches": len(self.batch_times),
            "total_time_seconds": round(total_time, 2),
            "avg_batch_time_seconds": round(avg_batch_time, 3),
            "items_per_second": round(items_per_second, 2),
            "avg_batch_size": round(total_items / len(self.batch_times), 1) if self.batch_times else 0
        }
    
    def log_summary(self):
        """Log a summary of the performance."""
        stats = self.get_stats()
        logger.info(
            f"Batch performance summary: {self.operation_name}",
            **stats
        )