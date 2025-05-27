# PDF Summarizer Backend

FastAPI backend for the PDF Summarizer application following best practices with feature-based module organization.

## Project Structure

```
src/
├── common/          # Shared utilities and schemas
├── config.py        # Application configuration
├── health/          # Health check endpoints
├── main.py         # Application entry point
├── pdf/            # PDF processing module
└── summarization/  # Text summarization module
```

## Setup

1. Install dependencies:
```bash
npx nx install backend
```

2. Create a `.env` file in the `apps/backend` directory:
```bash
cp .env.example .env
```

3. Add your OpenAI API key to the `.env` file:
```
OPENAI_API_KEY=your_actual_api_key_here
```

## Running the Backend

Start the development server:
```bash
npx nx serve backend
```

The backend will be available at http://localhost:8000

## API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check with service status

### PDF Operations
- `POST /api/v1/pdf/extract-text` - Extract text from PDF
- `POST /api/v1/pdf/summarize` - Upload and summarize a PDF file

### Text Summarization
- `POST /api/v1/summarize/text` - Summarize text content
- `GET /api/v1/summarize/info` - Get summarization service info

## API Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

Key configurations:
- `OPENAI_API_KEY` - Required for summarization features
- `MAX_PDF_SIZE_MB` - Maximum PDF file size (default: 10MB)
- `MAX_PDF_PAGES` - Maximum number of pages (default: 100)
- `DEFAULT_SUMMARY_LENGTH` - Default summary word count (default: 500)