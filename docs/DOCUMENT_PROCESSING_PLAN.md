# Document Processing Architecture Plan

## Overview

This document outlines the architecture and implementation plan for asynchronous document processing features in DocuLearn, using arq for background job processing with real-time progress updates via WebSockets.

## Core Technologies

- **arq**: Modern Python async job queue (replacement for Celery)
- **Redis**: Job queue broker and caching
- **pgvector**: Vector storage for embeddings
- **LangChain**: Document processing and LLM integration
- **OpenAI/Ollama**: Embedding and LLM providers
- **WebSockets**: Real-time progress updates to frontend

## Architecture Flow

```
1. Frontend uploads document
   ↓
2. Backend stores document in DB
   ↓
3. Backend enqueues job to Redis (via arq)
   ↓
4. Worker picks up job from Redis
   ↓
5. Worker processes document:
   - Reports progress via Redis/API
   - Backend sends WebSocket updates
   - Downloads file
   - Extracts text
   - Generates embeddings
   - Stores vectors in pgvector
   ↓
6. Document ready for search/chat/analysis
```

## Phase 1: Core Infrastructure (Immediate)

### 1.1 WebSocket Setup

```python
# apps/backend/app/api/v1/websockets.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_progress(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, user_id)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

### 1.2 Progress Tracking Schema

```python
# apps/backend/app/schemas/progress.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, Any

class ProgressStage(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProgressUpdate(BaseModel):
    job_id: str
    document_id: str
    stage: ProgressStage
    progress: float  # 0.0 to 1.0
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### 1.3 Arq Integration with Progress

```python
# arq configuration
class WorkerSettings:
    functions = [
        process_document,
        generate_embeddings,
        update_document_status
    ]
    redis_settings = RedisSettings(
        host='localhost',
        port=6379,
        database=0
    )
    queue_name = 'doculearn:queue'
    
    # Progress reporting
    on_job_start = report_job_start
    on_job_complete = report_job_complete
    on_job_error = report_job_error
```

### 1.4 Job Enqueuing with Progress Tracking

```python
async def complete_pdf_upload(
    pdf_id: str, 
    user_id: str,
    redis: ArqRedis,
    db: AsyncSession
):
    # Create job record in database
    job_record = JobProgress(
        document_id=pdf_id,
        user_id=user_id,
        status="queued",
        progress=0.0
    )
    db.add(job_record)
    await db.commit()
    
    # Enqueue document processing job
    job = await redis.enqueue_job(
        'process_document',
        pdf_id,
        user_id,
        job_id=f"doc:{pdf_id}",
        expires=3600  # 1 hour expiry
    )
    
    # Send initial WebSocket update
    await manager.send_progress(user_id, {
        "type": "job_queued",
        "job_id": job.job_id,
        "document_id": pdf_id,
        "stage": "queued",
        "progress": 0.0,
        "message": "Document processing queued"
    })
    
    return {"job_id": job.job_id, "status": "queued"}
```

### 1.5 Worker Implementation with Progress Reporting

```python
# apps/worker/tasks/document_processor.py
from redis.asyncio import Redis
from typing import Dict
import json

class RedisProgressReporter:
    def __init__(self, redis: Redis, job_id: str, document_id: str, user_id: str):
        self.redis = redis
        self.job_id = job_id
        self.document_id = document_id
        self.user_id = user_id
        self.channel = "document_progress"
    
    async def report_progress(
        self, 
        stage: str, 
        progress: float, 
        message: str,
        details: Dict = None
    ):
        """Report progress via Redis pub/sub"""
        try:
            progress_data = {
                "job_id": self.job_id,
                "document_id": self.document_id,
                "user_id": self.user_id,
                "stage": stage,
                "progress": progress,
                "message": message,
                "details": details or {}
            }
            
            await self.redis.publish(
                self.channel,
                json.dumps(progress_data)
            )
        except Exception as e:
            logger.error(f"Failed to report progress: {e}")

async def process_document(ctx: dict, pdf_id: str, user_id: str):
    """Main document processing task with progress reporting"""
    
    redis = ctx['redis']
    reporter = RedisProgressReporter(
        redis=redis,
        job_id=ctx['job_id'],
        document_id=pdf_id,
        user_id=user_id
    )
        
        try:
            # 1. Fetch document (5%)
            await reporter.report_progress(
                "downloading", 0.05, "Fetching document from database"
            )
            async with get_db_session() as db:
                document = await get_document(db, pdf_id)
            
            # 2. Download file content (15%)
            await reporter.report_progress(
                "downloading", 0.15, "Downloading file content"
            )
            file_content = await download_file(document.file_path)
            
            # 3. Extract text (25%)
            await reporter.report_progress(
                "extracting", 0.25, "Extracting text from PDF"
            )
            if not document.extracted_text:
                text = await extract_pdf_text(file_content)
                await update_document_text(db, pdf_id, text)
            else:
                text = document.extracted_text
            
            # 4. Chunk document (35%)
            await reporter.report_progress(
                "chunking", 0.35, "Splitting document into chunks"
            )
            chunks = chunk_document(text)
            await reporter.report_progress(
                "chunking", 0.40, f"Created {len(chunks)} chunks",
                {"chunk_count": len(chunks)}
            )
            
            # 5. Generate embeddings (40-85%)
            await reporter.report_progress(
                "embedding", 0.40, "Starting embedding generation"
            )
            embeddings = []
            for i, chunk in enumerate(chunks):
                # Report progress for each chunk
                chunk_progress = 0.40 + (0.45 * (i / len(chunks)))
                await reporter.report_progress(
                    "embedding", 
                    chunk_progress, 
                    f"Processing chunk {i+1}/{len(chunks)}"
                )
                
                embedding = await generate_embedding(chunk['text'])
                embeddings.append({
                    'chunk': chunk,
                    'embedding': embedding
                })
            
            # 6. Store vectors (85-95%)
            await reporter.report_progress(
                "storing", 0.85, "Storing embeddings in database"
            )
            await store_vectors(db, pdf_id, embeddings)
            
            # 7. Update status (95-100%)
            await reporter.report_progress(
                "storing", 0.95, "Finalizing document processing"
            )
            await update_document_status(db, pdf_id, "completed")
            
            # 8. Complete
            await reporter.report_progress(
                "completed", 1.0, "Document processing completed successfully"
            )
            
        except Exception as e:
            await reporter.report_progress(
                "failed", 
                0.0, 
                f"Processing failed: {str(e)}",
                {"error": str(e)}
            )
            raise
```

### 1.6 Backend Progress Endpoint

```python
# apps/backend/app/api/v1/jobs.py
from app.api.v1.websockets import manager

@router.post("/progress")
async def update_job_progress(
    progress: ProgressUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Receive progress updates from worker and broadcast via WebSocket"""
    
    # Update job progress in database
    await db.execute(
        update(JobProgress)
        .where(JobProgress.job_id == progress.job_id)
        .values(
            stage=progress.stage,
            progress=progress.progress,
            last_update=datetime.utcnow(),
            error=progress.error
        )
    )
    await db.commit()
    
    # Send WebSocket update to user
    await manager.send_progress(progress.user_id, {
        "type": "job_progress",
        "job_id": progress.job_id,
        "document_id": progress.document_id,
        "stage": progress.stage,
        "progress": progress.progress,
        "message": progress.message,
        "details": progress.details,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return {"status": "ok"}
```

### 1.7 Frontend WebSocket Integration

```typescript
// apps/frontend/src/app/services/websocket.service.ts
import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

export interface ProgressUpdate {
  type: string;
  job_id: string;
  document_id: string;
  stage: string;
  progress: number;
  message: string;
  details?: any;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket?: WebSocket;
  private progressSubject = new Subject<ProgressUpdate>();
  
  connect(userId: string): Observable<ProgressUpdate> {
    const wsUrl = `ws://localhost:8000/api/v1/ws/${userId}`;
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'job_progress') {
        this.progressSubject.next(data);
      }
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    // Keep alive
    setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send('ping');
      }
    }, 30000);
    
    return this.progressSubject.asObservable();
  }
  
  disconnect() {
    this.socket?.close();
  }
}
```

```typescript
// apps/frontend/src/app/components/upload-progress.component.ts
export class UploadProgressComponent implements OnInit {
  progressUpdates$ = new Subject<ProgressUpdate>();
  
  ngOnInit() {
    this.websocketService.connect(this.userId)
      .pipe(
        filter(update => update.document_id === this.documentId)
      )
      .subscribe(update => {
        this.updateProgress(update);
      });
  }
  
  updateProgress(update: ProgressUpdate) {
    this.currentStage = update.stage;
    this.progressPercentage = Math.round(update.progress * 100);
    this.statusMessage = update.message;
    
    if (update.stage === 'completed') {
      this.onProcessingComplete();
    } else if (update.stage === 'failed') {
      this.onProcessingError(update.details?.error);
    }
  }
}
```

## Phase 2: Database Schema for Progress Tracking

```sql
-- Job progress tracking
CREATE TABLE job_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    document_id UUID REFERENCES pdfs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    stage VARCHAR(50) NOT NULL,
    progress FLOAT NOT NULL DEFAULT 0.0,
    message TEXT,
    details JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    INDEX idx_job_progress_user (user_id),
    INDEX idx_job_progress_document (document_id)
);

-- Progress history for analytics
CREATE TABLE job_progress_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    progress FLOAT NOT NULL,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_progress_history_job (job_id)
);
```

## Phase 3: Progress UI Components

### 3.1 Progress Bar Component

```html
<!-- apps/frontend/src/app/components/document-progress.component.html -->
<div class="document-progress" *ngIf="isProcessing">
  <div class="progress-header">
    <h3>{{ documentName }}</h3>
    <span class="progress-stage">{{ getStageLabel(currentStage) }}</span>
  </div>
  
  <div class="progress-bar-container">
    <div class="progress-bar" [style.width.%]="progressPercentage">
      <span class="progress-text">{{ progressPercentage }}%</span>
    </div>
  </div>
  
  <div class="progress-details">
    <p class="progress-message">{{ statusMessage }}</p>
    
    <div class="stage-indicators">
      <div class="stage" 
           *ngFor="let stage of stages" 
           [class.active]="isStageActive(stage)"
           [class.completed]="isStageCompleted(stage)">
        <mat-icon>{{ getStageIcon(stage) }}</mat-icon>
        <span>{{ stage }}</span>
      </div>
    </div>
  </div>
  
  <div class="progress-actions" *ngIf="currentStage === 'failed'">
    <button mat-button color="warn" (click)="retry()">
      <mat-icon>refresh</mat-icon> Retry
    </button>
  </div>
</div>
```

### 3.2 Toast Notifications

```typescript
// Show toast notifications for progress updates
this.websocketService.connect(this.userId)
  .subscribe(update => {
    switch (update.stage) {
      case 'completed':
        this.toastr.success(
          `Document "${update.document_name}" is ready for search and chat!`,
          'Processing Complete'
        );
        break;
      case 'failed':
        this.toastr.error(
          `Failed to process "${update.document_name}": ${update.error}`,
          'Processing Failed'
        );
        break;
    }
  });
```

## Phase 4: Advanced Progress Features

### 4.1 Batch Progress Tracking

```python
async def process_batch_documents(ctx: dict, document_ids: List[str], user_id: str):
    """Process multiple documents with aggregated progress"""
    batch_id = f"batch:{uuid4()}"
    total_docs = len(document_ids)
    
    redis = ctx['redis']
    reporter = RedisProgressReporter(
        redis=redis,
        job_id=batch_id,
        document_id=None,
        user_id=user_id
    )
        
        for i, doc_id in enumerate(document_ids):
            # Report batch progress
            batch_progress = i / total_docs
            await reporter.report_progress(
                "batch_processing",
                batch_progress,
                f"Processing document {i+1} of {total_docs}",
                {
                    "current_document": doc_id,
                    "completed": i,
                    "total": total_docs
                }
            )
            
            # Process individual document
            await process_document(ctx, doc_id, user_id)
```

### 4.2 Progress Analytics

```python
async def get_processing_analytics(user_id: str) -> dict:
    """Get analytics on document processing times"""
    result = await db.execute(
        """
        SELECT 
            stage,
            AVG(EXTRACT(EPOCH FROM (last_update - started_at))) as avg_duration,
            COUNT(*) as count,
            AVG(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as error_rate
        FROM job_progress
        WHERE user_id = :user_id
        GROUP BY stage
        """,
        {"user_id": user_id}
    )
    
    return {
        "stages": [
            {
                "stage": row.stage,
                "avg_duration": row.avg_duration,
                "count": row.count,
                "error_rate": row.error_rate
            }
            for row in result
        ]
    }
```

## Implementation Timeline

### Week 1: Core Infrastructure
- [x] Add arq to dependencies
- [ ] Configure Redis for job queue
- [ ] Implement WebSocket manager
- [ ] Create progress tracking schema
- [ ] Implement job enqueuing with progress

### Week 2: Worker Progress Reporting
- [ ] Implement ProgressReporter class
- [ ] Add progress reporting to document processor
- [ ] Create progress API endpoint
- [ ] Test end-to-end progress flow

### Week 3: Frontend Integration
- [ ] Create WebSocket service
- [ ] Build progress UI components
- [ ] Add toast notifications
- [ ] Implement retry functionality

### Week 4: Advanced Features
- [ ] Batch processing with progress
- [ ] Progress analytics
- [ ] Error recovery mechanisms
- [ ] Performance optimization

## Monitoring and Observability

### Progress Metrics

```python
# Prometheus metrics
processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Time spent processing documents',
    ['stage']
)

processing_errors = Counter(
    'document_processing_errors_total',
    'Total number of processing errors',
    ['stage', 'error_type']
)

active_jobs = Gauge(
    'active_processing_jobs',
    'Number of currently active processing jobs'
)
```

### WebSocket Monitoring

- Active connections per user
- Message throughput
- Connection duration
- Reconnection frequency

## Error Handling and Recovery

### Connection Recovery

```typescript
// Automatic reconnection with exponential backoff
class WebSocketService {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      setTimeout(() => {
        this.connect(this.userId);
        this.reconnectAttempts++;
      }, delay);
    }
  }
}
```

### Progress Recovery

```python
async def recover_stalled_jobs():
    """Detect and recover stalled jobs"""
    stalled_threshold = datetime.utcnow() - timedelta(minutes=10)
    
    stalled_jobs = await db.execute(
        select(JobProgress)
        .where(
            JobProgress.stage != 'completed',
            JobProgress.stage != 'failed',
            JobProgress.last_update < stalled_threshold
        )
    )
    
    for job in stalled_jobs:
        # Re-queue or mark as failed
        await handle_stalled_job(job)
```

## Security Considerations

1. **WebSocket Authentication**: Verify JWT token on connection
2. **User Isolation**: Users only receive their own progress updates
3. **Rate Limiting**: Limit progress update frequency
4. **Message Validation**: Validate all WebSocket messages
5. **Connection Limits**: Limit concurrent connections per user