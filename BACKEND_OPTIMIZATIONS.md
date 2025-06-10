# Backend Performance Optimizations Roadmap

## Completed Optimizations ✅

### 1. Database Query Optimizations
- Added indexes on frequently queried columns:
  - `documents.file_hash` - For deduplication lookups
  - `documents.created_at` - For sorting and filtering
  - `summaries.created_at` - For sorting
- Migration created: `84c678a2ecc2_add_performance_indexes.py`

### 2. Pagination Implementation
- `DocumentService.list_user_documents()` - Added limit/offset parameters (default: 50)
- `/api/v1/library` endpoint - Added pagination query parameters
- Chat history retrieval - Limited to last 20 messages

### 3. Memory Optimization
- Embeddings generation - Batch processing (10 chunks at a time)
- Chat context - Limited to prevent loading entire conversation history

## Future Optimizations 🚀

### 1. Caching Layer with Redis

#### Implementation Plan:
```python
# config.py
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# cache_service.py
import redis.asyncio as redis
from functools import wraps
import json

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str):
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        await self.redis.setex(key, ttl, json.dumps(value))
```

#### Cache Targets:
- **User lookups**: Cache user data by provider ID
  - Key: `user:provider:{provider}:{provider_id}`
  - TTL: 1 hour
- **Tag counts**: Cache tag statistics
  - Key: `tags:counts:{user_id}`
  - TTL: 5 minutes
- **Document metadata**: Cache frequently accessed documents
  - Key: `document:meta:{document_id}`
  - TTL: 30 minutes

### 2. Async File I/O with aiofiles

#### Current Issues:
- Synchronous file operations in `storage_service.py`
- Blocking I/O during file uploads/downloads

#### Implementation:
```python
# storage_service.py updates
import aiofiles

async def store_file(self, content: bytes, ...):
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

async def retrieve_file(self, storage_key: str) -> bytes:
    async with aiofiles.open(file_path, 'rb') as f:
        return await f.read()
```

### 3. Connection Pool Optimization

#### SQLAlchemy Configuration:
```python
# database/session.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # Increase from default 5
    max_overflow=40,           # Allow up to 60 total connections
    pool_timeout=30,           # Timeout waiting for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Test connections before use
)
```

#### Benefits:
- Better handling of concurrent requests
- Reduced connection overhead
- Automatic stale connection handling

### 4. Advanced Query Optimizations

#### Cursor-based Pagination:
```python
# For large datasets, replace offset/limit with cursor
async def get_documents_cursor(
    last_id: Optional[UUID] = None,
    limit: int = 50
):
    query = select(Document).order_by(Document.created_at.desc())
    if last_id:
        query = query.where(Document.id < last_id)
    return await db.execute(query.limit(limit))
```

#### Query Result Streaming:
```python
# For very large results
async def stream_documents():
    async with db.stream(query) as result:
        async for row in result:
            yield row
```

### 5. Background Task Processing

#### Celery Integration:
```python
# tasks.py
from celery import Celery

celery_app = Celery('pdf_summarizer', broker=REDIS_URL)

@celery_app.task
async def generate_embeddings_task(document_id: str):
    # Move heavy embedding generation to background
    pass

@celery_app.task
async def generate_summary_task(document_id: str):
    # Process summaries asynchronously
    pass
```

#### Task Queue Benefits:
- Non-blocking document processing
- Retry failed operations
- Better resource utilization
- Progress tracking

### 6. Vector Search Optimization

#### pgvector Indexing:
```sql
-- Create HNSW index for fast similarity search
CREATE INDEX ON document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Or IVFFlat for memory efficiency
CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);
```

#### Query Optimization:
```python
# Use approximate search for better performance
async def search_similar_approximate(
    query_embedding: list[float],
    limit: int = 10
):
    # Set probes for IVFFlat
    await db.execute(text("SET ivfflat.probes = 10"))
    
    # Or set ef_search for HNSW
    await db.execute(text("SET hnsw.ef_search = 100"))
    
    # Then run similarity query
```

### 7. API Response Optimization

#### Response Compression:
```python
# Add gzip middleware
from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### Field Selection:
```python
# Allow clients to specify fields
@router.get("/documents")
async def get_documents(
    fields: Optional[str] = Query(None, description="Comma-separated fields")
):
    if fields:
        selected_fields = fields.split(",")
        # Build dynamic query with only selected fields
```

### 8. Monitoring and Profiling

#### Performance Monitoring:
```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### Database Query Logging:
```python
# Log slow queries
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Add query timing
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.5:  # Log queries taking > 500ms
        logger.warning(f"Slow query ({total:.2f}s): {statement[:100]}")
```

## Implementation Priority

1. **High Priority** 🔴
   - Redis caching (immediate performance boost)
   - Connection pool optimization (stability improvement)
   - pgvector indexing (critical for search performance)

2. **Medium Priority** 🟡
   - Background task processing (better UX)
   - Async file I/O (faster uploads/downloads)
   - Response compression (bandwidth optimization)

3. **Low Priority** 🟢
   - Advanced pagination strategies
   - Field selection optimization
   - Comprehensive monitoring

## Performance Targets

- **API Response Time**: < 200ms for 95th percentile
- **Document Processing**: < 10s for average PDF
- **Search Latency**: < 100ms for vector similarity search
- **Concurrent Users**: Support 1000+ concurrent connections
- **Database Connections**: Maintain pool utilization < 80%

## Testing Strategy

1. **Load Testing**: Use Locust or K6 for API testing
2. **Database Benchmarks**: pgbench for PostgreSQL performance
3. **Memory Profiling**: memory_profiler for Python code
4. **Query Analysis**: EXPLAIN ANALYZE for all major queries

## References

- [pgvector Performance](https://github.com/pgvector/pgvector#performance)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#best-practices)