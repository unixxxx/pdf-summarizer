# PDF Summarizer

A modern web application for summarizing PDF documents using AI, built with Angular 19 and FastAPI.

## Features

- 📄 **PDF Upload & Processing** - Extract text from PDF files
- 🤖 **AI-Powered Summarization** - Generate concise summaries using OpenAI or Ollama
- 🔐 **OAuth Authentication** - Sign in with Google or GitHub
- 📊 **Summary History** - View and manage past summaries
- 🚀 **Modern Stack** - Angular 19, FastAPI, Tailwind CSS

## Quick Start

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.9+
- Docker (for PostgreSQL)
- Ollama (for local AI) or OpenAI API key
- OAuth credentials (Google or GitHub)

### Setup Instructions

1. **Install dependencies:**
   ```sh
   pnpm install
   npx nx install backend
   ```

2. **Set up the database:**
   ```sh
   # Start PostgreSQL
   docker-compose up -d postgres
   
   # Create database and run migrations
   cd apps/backend
   uv run python scripts/setup_db.py
   uv run alembic upgrade head
   cd ../..
   ```

3. **Set up Ollama (for local AI):**
   ```sh
   ./setup-ollama.sh
   ```

4. **Configure environment:**
   ```sh
   cp apps/backend/.env.example apps/backend/.env
   # Edit .env file to add:
   # - JWT_SECRET_KEY (generate a secure value)
   # - OAuth credentials (see OAuth Setup section)
   ```

5. **Run the application:**
   ```sh
   npx nx run-many -t serve
   ```

   The app will be available at:
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Using OpenAI

1. Update `apps/backend/.env`:
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your-api-key-here
   ```

2. Follow steps 1, 3, and 4 from above.

## Available LLM Models

### Ollama Models
- `llama2` - Default, good for general summarization
- `mistral` - Fast and efficient
- `neural-chat` - Optimized for conversational tasks
- `phi` - Lightweight model

To change models, update `OLLAMA_MODEL` in `.env`.

## Development

### Running Individual Services

```sh
# Frontend only
npx nx serve frontend

# Backend only
npx nx serve backend

# Both services
npx nx run-many -t serve
```

### Building for Production

```sh
npx nx build frontend
npx nx build backend
```

### Running Tests

```sh
npx nx test frontend
npx nx test backend
```

## OAuth Setup (Required)

The application requires OAuth authentication. Configure at least one provider:

### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing one
3. Create OAuth 2.0 credentials (Web application)
4. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/callback`
5. Copy credentials to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### GitHub OAuth
1. Go to [GitHub Settings > Developer settings > OAuth Apps](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/api/v1/auth/callback`
4. Copy credentials to `.env`:
   ```env
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   ```

## Architecture

- **Frontend:** Angular 19 with standalone components, Tailwind CSS for styling
- **Backend:** FastAPI with async support, Pydantic for validation
- **AI/LLM:** LangChain with support for OpenAI and Ollama
- **Authentication:** JWT tokens with OAuth2 providers
- **Database:** PostgreSQL with pgvector extension for document storage
- **Storage:** Database-backed persistent storage with duplicate detection

## License

MIT
