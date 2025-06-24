# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is DocuLearn - a document learning platform monorepo built with Nx, containing:

- **Frontend**: Angular 19 with Tailwind CSS
- **Backend**: FastAPI with LangChain integration
- **Infrastructure**: PostgreSQL with pgvector, optional Ollama for local LLM

## Essential Commands

### Development

```bash
# Start both frontend and backend
npx nx run-many -t serve

# Start individual services
npx nx serve frontend    # Angular at http://localhost:4200
npx nx serve backend     # FastAPI at http://localhost:8000

# Install dependencies
pnpm install             # JavaScript dependencies
npx nx install backend   # Python dependencies
```

### Code Quality

```bash
# Linting - ALWAYS run before committing
npx nx lint frontend     # ESLint for Angular
npx nx lint backend      # Ruff for Python

# Type checking (frontend)
npx nx typecheck frontend

# Format Python code
npx nx format backend
```

### Testing

```bash
npx nx test backend      # Run pytest with coverage
npx nx test frontend     # No tests configured yet
```

### Database Operations

```bash
# From apps/backend directory:
uv run alembic upgrade head              # Apply migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run python scripts/setup_db.py        # Initial database setup
```

### Python Dependency Management (via Nx)

```bash
npx nx add backend package-name          # Add dependency
npx nx remove backend package-name       # Remove dependency
npx nx update backend                    # Update dependencies
npx nx sync backend                      # Sync virtual environment
```

## Architecture Patterns

### Monorepo Structure

- Uses Nx with @nxlv/python plugin for unified tooling
- Frontend and backend are separate apps in `apps/` directory
- Shared ESLint config at root level

### Backend Architecture

- **Modular structure** by feature: auth/, pdf/, summarization/, database/
- **Dependency injection** using FastAPI's Depends
- **Async throughout** with asyncpg and async SQLAlchemy
- **Pydantic Settings** for environment configuration
- **JWT authentication** with OAuth2 providers (Google/GitHub)

### Frontend Architecture

- **Standalone components** (modern Angular 19 pattern)
- **Guards and interceptors** for authentication
- **API service** with environment-based configuration
- **Proxy configuration** to forward /api calls to backend

### Database Patterns

- **UUID primary keys** for all tables
- **File deduplication** using SHA-256 hashes
- **Vector embeddings** stored with pgvector for similarity search
- **Alembic migrations** with autogenerate support

### LLM Integration

- **Provider abstraction** supporting both OpenAI and Ollama
- **LangChain** for document processing and summarization
- **Configurable models** via environment variables

## Important Configuration

### Environment Variables (apps/backend/.env)

Required:

- `JWT_SECRET_KEY` - Generate secure random value
- OAuth credentials (at least one provider):
  - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
  - `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
- `DATABASE_URL` - PostgreSQL connection string

Optional:

- `LLM_PROVIDER` - "ollama" (default) or "openai"
- `OPENAI_API_KEY` - Required if using OpenAI
- `OLLAMA_MODEL` - Default: "llama2"

### Key Files

- `apps/frontend/proxy.conf.json` - API proxy configuration
- `apps/backend/alembic.ini` - Database migration config
- `docker-compose.yml` - PostgreSQL and Ollama services
- `nx.json` - Monorepo configuration

## Development Workflow

1. **Infrastructure**: Start PostgreSQL with `docker-compose up -d postgres`
2. **Database**: Run migrations with `cd apps/backend && uv run alembic upgrade head`
   - For new deployments, see `apps/backend/alembic/versions/README.md`
   - For migration management, see `apps/backend/docs/MIGRATION_STRATEGY.md`
3. **Environment**: Copy `.env.example` to `.env` and configure
4. **Dependencies**: Install with `pnpm install && npx nx install backend`
5. **Development**: Start with `npx nx run-many -t serve`
6. **Before committing**: Run `npx nx lint frontend && npx nx lint backend`

## API Endpoints

- Health check: `GET /api/v1/health`
- Auth endpoints: `/api/v1/auth/*`
- PDF operations: `/api/v1/pdf/*`
- Summarization: `/api/v1/summarization/*`
- API documentation: `http://localhost:8000/docs`

## Storage Patterns

PDFs are stored in PostgreSQL with:

- Original file content saved to disk temporarily
- Text extracted and stored in database
- File deduplicated by SHA-256 hash
- Embeddings generated for vector search

## OAuth Setup Requirements

The application requires OAuth configuration:

1. Google: Create credentials at Google Cloud Console
2. GitHub: Create OAuth App in GitHub Settings
3. Redirect URI for both: `http://localhost:8000/api/v1/auth/callback`

## Memories

- Always use TailwindCSS 4 when working with styles or design related files
- don't add co-author section to the git commit messages
- Always aim for production grade quality
- don't run the app, ask me to do it whenever necessary
- Always ask for structured outputs when using LLMs and provide appropriate pydantic schemas
- don't forget to await async expressions in python code

## Recent Backend Optimizations Completed

### Phase 1: Critical Performance ✅

- Added 10 comprehensive database indexes
- Fixed N+1 query problems
- Configured connection pooling (pool_size=20, max_overflow=40)
- Implemented async I/O with aiofiles
- Added timeouts for all external APIs
- Implemented batch operations for bulk inserts

### Phase 2: Stability & Resilience ✅

- Redis caching with graceful degradation
- Structured error handling hierarchy
- Retry logic with exponential backoff using tenacity
- pgvector HNSW indexes (created dynamically)
- Background tasks with Celery and Redis broker
- GZip compression middleware
- Performance monitoring with metrics collection

### Background Tasks Available

- Document embedding generation
- Tag embedding updates
- Summary generation
- Document exports
- Orphaned file cleanup (hourly)

### Monitoring Endpoints

- `/api/v1/monitoring/metrics` - Performance metrics
- `/api/v1/monitoring/health/detailed` - Detailed health status

### Phase 3: Memory Optimization ✅

- Streaming utilities for large file processing
- OptimizedStorageService with S3 multipart upload
- Chunked processing to avoid memory exhaustion
- Streaming PDF text extraction
- Batch processing with concurrency control

## Pending Optimizations

### Database Session Anti-pattern Fix

- Some services still store DB session as instance variable
- Need to refactor to use Unit of Work pattern or pass session to methods
- FolderService and TrashService already refactored as examples

### Migration Consolidation

- Multiple migration files could be consolidated for cleaner deployment
- See `apps/backend/MIGRATION_CONSOLIDATION_STRATEGY.md` for details
