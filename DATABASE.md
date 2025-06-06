# Database Documentation

This document explains the database structure and setup for the PDF Summarizer application.

## Database Schema

The application uses PostgreSQL with the pgvector extension for storing document embeddings.

### Tables

#### users
Stores user account information from OAuth providers.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | User's email address (unique) |
| name | VARCHAR(255) | User's display name |
| picture | TEXT | URL to user's profile picture |
| provider | VARCHAR(50) | OAuth provider (google/github) |
| provider_id | VARCHAR(255) | User ID from OAuth provider |
| created_at | TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### documents
Stores uploaded PDF documents and their summaries.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users table |
| filename | VARCHAR(255) | Original PDF filename |
| file_size | INTEGER | File size in bytes |
| file_hash | VARCHAR(64) | SHA-256 hash of file content |
| page_count | INTEGER | Number of pages in PDF |
| content | TEXT | Extracted text content |
| summary | TEXT | Generated summary |
| summary_metadata | JSONB | Additional summary metadata |
| embedding | VECTOR(1536) | Document embedding vector |
| created_at | TIMESTAMP | Upload timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### Indexes

- `idx_documents_user_id` - Index on user_id for fast user document queries
- `idx_documents_file_hash` - Index on file_hash for duplicate detection
- `idx_documents_embedding` - Vector index for similarity search

## Setup Instructions

1. **Start PostgreSQL with Docker:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Create database and enable extensions:**
   ```bash
   cd apps/backend
   uv run python scripts/setup_db.py
   ```

3. **Run migrations:**
   ```bash
   cd apps/backend
   uv run alembic upgrade head
   ```

## OAuth Configuration

The application uses OAuth2 for authentication. To set up OAuth:

1. **Configure environment variables in `.env`:**
   ```bash
   # Google OAuth
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   
   # GitHub OAuth  
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   
   # OAuth Redirect URI
   OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
   ```

2. **Configure OAuth providers:**
   - **Google**: Create OAuth2 credentials at [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
     - Add `http://localhost:8000/api/v1/auth/callback` as authorized redirect URI
   - **GitHub**: Create OAuth App at [GitHub Settings](https://github.com/settings/developers)
     - Set Authorization callback URL to `http://localhost:8000/api/v1/auth/callback`

## Migration Commands

- **Create a new migration:**
  ```bash
  cd apps/backend
  uv run alembic revision --autogenerate -m "Description of changes"
  ```

- **Apply migrations:**
  ```bash
  cd apps/backend
  uv run alembic upgrade head
  ```

- **Rollback one migration:**
  ```bash
  cd apps/backend
  uv run alembic downgrade -1
  ```

- **View migration history:**
  ```bash
  cd apps/backend
  uv run alembic history
  ```

## Vector Search

The application uses pgvector for storing and searching document embeddings:

```sql
-- Example: Find similar documents
SELECT id, filename, summary, 
       embedding <=> '[...]'::vector AS distance
FROM documents
WHERE user_id = 'user-uuid'
ORDER BY embedding <=> '[...]'::vector
LIMIT 5;
```