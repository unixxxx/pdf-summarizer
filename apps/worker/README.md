# DocuLearn Worker

Background task worker for DocuLearn using arq (async Redis queue).

## Overview

This worker handles all asynchronous document processing tasks including:

- **Document Processing**: Text extraction from PDFs
- **Embedding Generation**: Vector embeddings for documents and tags
- **Summarization**: Document analysis (summary, title, tags)
- **Quiz Generation**: Creating quiz questions from documents
- **Flashcard Generation**: Creating flashcards from documents
- **Maintenance**: Orphaned file cleanup (scheduled)

## Architecture

The worker uses:
- **arq**: Modern Python async job queue
- **Redis**: Job queue broker
- **PostgreSQL**: Data storage
- **pgvector**: Vector storage for embeddings
- **LangChain**: LLM operations
- **OpenAI/Ollama**: LLM providers

## Setup

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Worker Configuration
WORKER_NAME=doculearn-worker

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/doculearn

# LLM Configuration
LLM_PROVIDER=ollama  # or "openai"
OPENAI_API_KEY=your-openai-api-key-here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### Local Development

1. Install dependencies:
   ```bash
   npx nx install worker
   ```

2. Run the worker:
   ```bash
   npx nx serve worker
   ```

### Docker

The worker is included in the docker-compose setup:

```bash
docker-compose up worker
```

## Task Flow

1. **Document Upload** (Backend)
   - User uploads document
   - Backend stores file and creates DB record
   - Backend enqueues `process_document` job

2. **Document Processing** (Worker)
   - Extract text from PDF
   - Store extracted text in DB
   - Enqueue `generate_document_embeddings`

3. **Embedding Generation** (Worker)
   - Chunk document text
   - Generate embeddings for each chunk
   - Store vectors in pgvector
   - Enqueue `generate_document_summary`

4. **Summarization** (Worker)
   - Generate summary, title, and tags
   - Store results in DB
   - Update document status to completed
   - Enqueue tag embedding generation

## Available Tasks

### Document Processing
- `process_document(document_id, user_id)`: Main document processing pipeline
- `generate_document_embeddings(document_id, user_id)`: Generate vector embeddings
- `generate_document_summary(document_id, user_id)`: Create summary and tags

### Content Generation
- `generate_quiz(document_id, user_id, options)`: Generate quiz questions
- `generate_flashcards(document_id, user_id, options)`: Generate flashcards

### Tag Processing
- `generate_tag_embeddings(tag_names)`: Generate embeddings for tags
- `update_all_tag_embeddings()`: Batch update all tag embeddings

### Maintenance
- `cleanup_orphaned_files()`: Remove orphaned files (runs daily at 2 AM)

## Progress Reporting

The worker reports progress back to the backend via HTTP API calls. Progress updates include:

- Task stage (downloading, extracting, embedding, etc.)
- Progress percentage (0.0 to 1.0)
- Status messages
- Error information

The backend then broadcasts these updates to the frontend via WebSockets.

## Error Handling

- Automatic retries with exponential backoff for LLM operations
- Failed jobs update document status in DB
- Detailed error logging with structlog
- Progress reporter captures errors

## Monitoring

The worker logs include:
- Job start/completion times
- Processing metrics
- Error details
- LLM usage information

## Testing

Run tests:
```bash
npx nx test worker
```

## Configuration

Worker settings are in `worker_settings.py`:
- Max jobs: 10 (concurrent)
- Job timeout: 600 seconds (10 minutes)
- Result retention: 24 hours
- Health check interval: 30 seconds