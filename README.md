# PDF Summarizer

A modern, production-ready web application for summarizing PDF documents using AI, built with Angular 19, NgRx SignalStore, and FastAPI.

## Features

- 📄 **PDF Upload & Processing** - Extract and process text from PDF files with automatic deduplication
- 🤖 **AI-Powered Summarization** - Generate intelligent summaries using OpenAI or Ollama with customizable styles
- 💬 **Interactive Chat** - Ask questions about your documents with context-aware AI responses
- 🔐 **OAuth Authentication** - Secure sign-in with Google or GitHub
- 📚 **Document Library** - Advanced search, filtering by tags, and document management
- 🏷️ **Smart Tagging** - Automatic AI-generated tags for easy organization
- 📥 **Export Options** - Download summaries in Markdown, PDF, or plain text formats
- 🌓 **Dark Mode** - Full theme support with system preference detection
- 🚀 **Modern Architecture** - Clean architecture with NgRx SignalStore state management
- ☁️ **Cloud Ready** - S3-compatible storage support for scalability

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

### Common Commands

```sh
# Start both frontend and backend
npx nx run-many -t serve

# Frontend only (http://localhost:4200)
npx nx serve frontend

# Backend only (http://localhost:8000)
npx nx serve backend

# Run linters
npx nx lint frontend
npx nx lint backend

# Format code
npx nx format

# Run tests
npx nx test backend    # Frontend tests not configured yet

# Build for production
npx nx build frontend
npx nx build backend
```

### Backend Commands

```sh
# Install/update Python dependencies
npx nx install backend
npx nx add backend <package-name>

# Database migrations
cd apps/backend
uv run alembic upgrade head                              # Apply migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
```

### Project Structure

```
pdf-summarizer/
├── apps/
│   ├── frontend/               # Angular 19 application
│   │   └── src/app/
│   │       ├── auth/          # Authentication (store, guard, components)
│   │       ├── chat/          # Chat feature with AI
│   │       ├── documents/     # Document library and management
│   │       ├── summary/       # Summarization features
│   │       └── shared/        # Shared components and utilities
│   └── backend/               # FastAPI application
│       └── src/
│           ├── auth/          # OAuth and JWT authentication
│           ├── chat/          # Chat endpoints and AI integration
│           ├── document/      # Document management and processing
│           ├── library/       # Library browsing and search
│           ├── storage/       # File storage abstraction
│           └── summarization/ # AI summarization logic
├── docker-compose.yml         # PostgreSQL and Ollama services
└── nx.json                   # Nx monorepo configuration
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

### Frontend (Angular 19)
- **State Management:** NgRx SignalStore with reactive state management
- **Component Architecture:** Standalone components with signal-based reactivity
- **Styling:** Tailwind CSS 4 with custom design system
- **Type Safety:** Strict TypeScript with comprehensive interfaces
- **Clean Architecture:** Components → Stores → Services pattern

### Backend (FastAPI)
- **Async Architecture:** Full async/await support with asyncpg
- **Domain-Driven Design:** Modular structure by business domain
- **Validation:** Pydantic v2 for request/response validation
- **Database:** PostgreSQL with pgvector for semantic search
- **Storage:** Flexible storage with local filesystem and S3 support

### AI/LLM Integration
- **Framework:** LangChain for document processing and chat
- **Providers:** OpenAI and Ollama with easy provider switching
- **Features:** Streaming responses, context-aware chat, smart tagging
- **Vector Search:** pgvector for semantic document search

### Key Design Patterns
- **Frontend State:** All state managed through NgRx SignalStore
- **Backend Services:** Repository pattern with dependency injection
- **Authentication:** JWT with OAuth2 flow (Google/GitHub)
- **API Design:** RESTful with OpenAPI documentation
- **Error Handling:** Centralized error handling on both frontend and backend

## License

MIT
