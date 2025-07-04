"""Performance monitoring middleware and utilities."""

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware:
    """Middleware to monitor API request performance."""
    
    def __init__(self, slow_request_threshold: float = 1.0):
        """
        Initialize performance monitoring middleware.
        
        Args:
            slow_request_threshold: Time in seconds to consider a request slow
        """
        self.slow_request_threshold = slow_request_threshold
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure performance."""
        # Skip monitoring for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        # Log slow requests
        if process_time > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {process_time:.2f}s (threshold: {self.slow_request_threshold}s)"
            )
            
            # Log additional context for debugging
            logger.warning(
                f"Slow request details - "
                f"Client: {request.client.host if request.client else 'unknown'}, "
                f"User-Agent: {request.headers.get('user-agent', 'unknown')}, "
                f"Status: {response.status_code}"
            )
        else:
            # Log normal requests at debug level
            logger.debug(
                f"Request completed: {request.method} {request.url.path} "
                f"in {process_time:.3f}s - Status: {response.status_code}"
            )
        
        return response


def setup_database_monitoring(engine: Engine) -> None:
    """
    Set up database query monitoring.
    
    Args:
        engine: SQLAlchemy engine to monitor
    """
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time."""
        context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log slow queries."""
        total_time = time.time() - context._query_start_time
        
        # Log slow queries (> 500ms)
        if total_time > 0.5:
            logger.warning(
                f"Slow query detected ({total_time:.2f}s): "
                f"{statement[:200]}{'...' if len(statement) > 200 else ''}"
            )
            if parameters:
                logger.debug(f"Query parameters: {parameters}")
        elif total_time > 0.1:
            # Log moderately slow queries at debug level
            logger.debug(
                f"Query completed in {total_time:.3f}s: "
                f"{statement[:100]}{'...' if len(statement) > 100 else ''}"
            )


def setup_connection_pool_monitoring(pool: Pool) -> None:
    """
    Set up connection pool monitoring.
    
    Args:
        pool: SQLAlchemy connection pool to monitor
    """
    
    @event.listens_for(pool, "connect")
    def receive_connect(dbapi_connection, connection_record):
        """Log new database connections."""
        logger.info("New database connection established")
    
    @event.listens_for(pool, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkouts."""
        try:
            # Get pool statistics - AsyncAdaptedQueuePool has different attributes
            if hasattr(pool, '_pool'):
                # Access the underlying sync pool
                sync_pool = pool._pool
                num_connections = sync_pool.size()
                num_overflow = sync_pool.overflow()
                num_checked_out = sync_pool.checkedout()
                
                # Log if pool is getting full
                if num_checked_out > num_connections * 0.8:
                    logger.warning(
                        f"Connection pool usage high: "
                        f"{num_checked_out}/{num_connections} connections in use, "
                        f"{num_overflow} overflow connections"
                    )
        except AttributeError:
            # Silently ignore if pool doesn't have expected attributes
            pass
    
    @event.listens_for(pool, "reset")
    def receive_reset(dbapi_connection, connection_record):
        """Log connection resets."""
        logger.debug("Database connection reset")


class RequestMetrics:
    """Simple in-memory metrics collector."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.total_requests = 0
        self.total_errors = 0
        self.response_times = []
        self.slow_queries = 0
        self.endpoints = {}
    
    def record_request(self, path: str, method: str, status_code: int, duration: float):
        """Record request metrics."""
        self.total_requests += 1
        
        if status_code >= 400:
            self.total_errors += 1
        
        self.response_times.append(duration)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        # Track per-endpoint metrics
        endpoint_key = f"{method} {path}"
        if endpoint_key not in self.endpoints:
            self.endpoints[endpoint_key] = {
                "count": 0,
                "errors": 0,
                "total_time": 0,
            }
        
        self.endpoints[endpoint_key]["count"] += 1
        self.endpoints[endpoint_key]["total_time"] += duration
        if status_code >= 400:
            self.endpoints[endpoint_key]["errors"] += 1
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            p95_response_time = sorted(self.response_times)[int(len(self.response_times) * 0.95)]
        else:
            avg_response_time = 0
            p95_response_time = 0
        
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / max(self.total_requests, 1),
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "slow_queries": self.slow_queries,
            "endpoints": {
                endpoint: {
                    "count": stats["count"],
                    "errors": stats["errors"],
                    "avg_time": stats["total_time"] / max(stats["count"], 1),
                }
                for endpoint, stats in self.endpoints.items()
            },
        }


# Global metrics instance
metrics = RequestMetrics()