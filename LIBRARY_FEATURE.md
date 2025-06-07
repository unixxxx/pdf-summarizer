# Library Feature Implementation

This document outlines the implementation of the library feature that transforms the simple history page into a full-featured document library with tags, search, filtering, and export capabilities.

## Overview

The library feature enhances the PDF summarizer application by:
- Automatically generating tags for documents using LLM
- Providing search and filtering capabilities
- Enabling document downloads and summary exports
- Organizing documents with a tag-based categorization system

## Backend Implementation

### 1. Database Schema Changes

#### New Models Added:
- **Tag Model** (`src/database/models.py`)
  - `id`: UUID primary key
  - `name`: Display name of the tag
  - `slug`: URL-friendly version for filtering
  - `description`: Optional tag description
  - `color`: Optional hex color code for UI
  - `created_at`: Timestamp

- **Document-Tags Relationship**
  - Many-to-many relationship via `document_tags` association table
  - Allows documents to have multiple tags
  - Cascading deletes to maintain referential integrity

#### Migration:
```bash
# Created migration
uv run alembic revision --autogenerate -m "Add tags table and document-tags relationship"
# Applied migration
uv run alembic upgrade head
```

### 2. Automatic Tag Generation

Modified `SummarizerService` (`src/summarization/service.py`):
- Added `generate_tags()` method that uses LLM to generate 3-8 relevant tags
- Tags are generated based on document summary and content sample
- Integrated into `summarize_pdf()` to automatically tag documents
- Tags are normalized (lowercase, hyphenated) for consistency

### 3. Storage and Download Features

#### Download Endpoint (`src/storage/router.py`):
- `GET /api/v1/storage/download/{document_id}`
- Supports both S3 and local storage
- S3: Returns presigned URLs with 1-hour expiration
- Local: Serves files directly with appropriate headers
- Security: Users can only download their own documents

#### S3 Configuration:
- Fixed environment variable loading issues in pydantic settings
- Updated field names to match AWS environment variables
- Added backward compatibility with property aliases
- Configuration in `.env`:
  ```
  STORAGE_BACKEND=s3
  S3_BUCKET_NAME=your-bucket
  AWS_ACCESS_KEY_ID=your-key
  AWS_SECRET_ACCESS_KEY=your-secret
  AWS_DEFAULT_REGION=your-region
  ```

### 4. Export Functionality

Created `ExportService` (`src/pdf/export.py`):
- Supports three export formats:
  - **Markdown**: Clean, formatted markdown with metadata and tags
  - **PDF**: Professional PDF document using ReportLab
  - **Plain Text**: Simple text format for compatibility

Export Endpoint:
- `GET /api/v1/pdf/export/{summary_id}?format=markdown|pdf|text`
- Includes document metadata, tags, and processing information
- Generates appropriate filenames based on original document

### 5. Library API with Search and Filtering

#### Main Library Endpoint (`src/pdf/router.py`):
- `GET /api/v1/pdf/library`
- Query Parameters:
  - `search`: Search in filenames and summaries (case-insensitive)
  - `tag`: Filter by single tag slug
  - `tags`: Filter by multiple tag slugs (array)
  - `limit`: Maximum results (1-100, default: 50)
  - `offset`: Pagination offset
- Returns documents with all associated tags
- Maintains backward compatibility with deprecated `/history` endpoint

#### Tags Endpoint:
- `GET /api/v1/pdf/tags`
- Returns all tags with document counts
- Ordered by usage frequency
- Only shows tags from user's own documents

### 6. Updated Response Schemas

Modified `PDFSummaryHistoryItem` (`src/pdf/schemas.py`):
- Added `tags` field with list of `TagSchema` objects
- Each tag includes: id, name, slug, color
- Maintains backward compatibility with existing fields

## Dependencies Added

```bash
# For export functionality
uv add reportlab markdown2
```

## API Endpoints Summary

### Document Operations
- `POST /api/v1/pdf/summarize` - Upload and summarize PDF (now generates tags)
- `GET /api/v1/pdf/library` - Get documents with search/filter/pagination
- `GET /api/v1/pdf/history` - Deprecated, redirects to library
- `DELETE /api/v1/pdf/history/{summary_id}` - Delete document and all data

### Tag Operations
- `GET /api/v1/pdf/tags` - Get all tags with document counts

### Storage Operations
- `GET /api/v1/storage/download/{document_id}` - Download original PDF
- `GET /api/v1/pdf/export/{summary_id}` - Export summary in various formats

## Frontend Requirements (To Be Implemented)

The frontend needs to be updated to:

1. **Transform History Page to Library**:
   - Replace simple list with card/grid view
   - Display tags on each document
   - Add search bar and tag filters
   - Show document counts per tag

2. **Add Action Buttons**:
   - Download original PDF
   - Export summary (dropdown for format selection)
   - View/Edit tags (future enhancement)
   - Delete document

3. **Implement Search and Filtering**:
   - Real-time search as user types
   - Tag filter chips/buttons
   - Clear all filters option
   - Results count display

4. **Add Tag Management**:
   - Tag cloud or list sidebar
   - Click tags to filter
   - Show document count per tag
   - Color-coded tags (using tag.color field)

## Testing the Implementation

### Test Tag Generation:
```bash
# Upload a new PDF to see automatic tag generation
curl -X POST http://localhost:8000/api/v1/pdf/summarize \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

### Test Library Endpoint:
```bash
# Search and filter
curl "http://localhost:8000/api/v1/pdf/library?search=angular&tag=technology&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get all tags
curl "http://localhost:8000/api/v1/pdf/tags" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Download and Export:
```bash
# Download original PDF
curl "http://localhost:8000/api/v1/storage/download/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded.pdf

# Export summary as PDF
curl "http://localhost:8000/api/v1/pdf/export/{summary_id}?format=pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o summary.pdf
```

## Next Session: Advanced Search and Filtering

### Requirements to Implement:

1. **Full-Text Search Enhancement**:
   - Current: Basic ILIKE search in filenames and summaries
   - TODO: Implement PostgreSQL full-text search with:
     - GIN indexes for better performance
     - ts_vector and ts_query for advanced text search
     - Search ranking and relevance scoring
     - Search highlighting in results
     - Support for phrase search and boolean operators

2. **Date Range Filtering**:
   - Add query parameters to library endpoint:
     - `created_after`: Filter documents created after this date
     - `created_before`: Filter documents created before this date
     - `processed_after`: Filter by processing date
     - `processed_before`: Filter by processing date
   - Add database indexes for date columns

3. **File Size Filtering**:
   - Add query parameters:
     - `min_size_mb`: Minimum file size in MB
     - `max_size_mb`: Maximum file size in MB
   - Consider adding size categories (small, medium, large)

4. **Processing Time Filtering**:
   - Add query parameters:
     - `min_processing_time`: Minimum processing time in seconds
     - `max_processing_time`: Maximum processing time in seconds
   - Useful for identifying documents that took long to process

5. **Vector Similarity Search**:
   - Leverage existing document embeddings in `document_chunks` table
   - Add endpoint: `POST /api/v1/pdf/search/similar`
   - Input: Query text or document ID
   - Process:
     - Generate embedding for query text
     - Use pgvector's `<->` operator for cosine similarity
     - Return documents ranked by similarity score
   - Consider adding:
     - Similarity threshold parameter
     - Hybrid search (combine with text search)
     - Filtering similar search results by tags/date

### Implementation Plan:

1. **Update Library Endpoint** (`/api/v1/pdf/library`):
   ```python
   # Additional query parameters
   created_after: Optional[datetime] = Query(None)
   created_before: Optional[datetime] = Query(None)
   min_size_mb: Optional[float] = Query(None, ge=0)
   max_size_mb: Optional[float] = Query(None, ge=0)
   min_processing_time: Optional[float] = Query(None, ge=0)
   max_processing_time: Optional[float] = Query(None, ge=0)
   sort_by: Optional[str] = Query("created_at", regex="^(created_at|file_size|processing_time|relevance)$")
   sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$")
   ```

2. **Create Similar Documents Endpoint**:
   ```python
   @router.post("/search/similar")
   async def search_similar_documents(
       query: str | UUID,  # Text query or document ID
       limit: int = 10,
       threshold: float = 0.7,  # Similarity threshold
       include_tags: Optional[List[str]] = None,  # Filter by tags
   )
   ```

3. **Database Optimizations**:
   - Add GIN index for full-text search
   - Add B-tree indexes for date and numeric filters
   - Consider materialized views for complex queries

4. **Frontend Requirements**:
   - Advanced search modal/drawer
   - Date range pickers
   - Size and time sliders
   - Sort options dropdown
   - Similar documents section

## Future Enhancements

1. **Tag Management**:
   - Manual tag editing
   - Tag merging and renaming
   - Custom tag colors
   - Tag descriptions

2. **Advanced Search Features**:
   - Saved searches
   - Search history
   - Search suggestions/autocomplete
   - Export search results

3. **Collections/Folders**:
   - Group documents into collections
   - Hierarchical organization
   - Shared collections for teams

4. **Batch Operations**:
   - Bulk tag assignment
   - Bulk export
   - Bulk delete

5. **Analytics Dashboard**:
   - Document statistics
   - Tag usage analytics
   - Processing time trends
   - Storage usage breakdown

## Notes

- Tags are automatically generated during summarization
- Existing documents won't have tags until re-summarized
- S3 storage is fully supported with presigned URLs
- Export formats can be extended (e.g., DOCX, HTML)
- The system maintains backward compatibility with existing APIs