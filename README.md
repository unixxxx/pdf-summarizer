# DocuLearn

Transform Documents into Knowledge - An intelligent document learning platform that helps you extract insights, generate study materials, and interact with your documents using AI.

## 🚀 Features

- 📄 **Universal Document Support** - Upload PDFs, create text documents, with more formats coming soon
- 🧠 **AI-Powered Processing** - Automatic text extraction, embeddings, and intelligent analysis
- 💬 **Interactive Chat** - Ask questions about your documents with context-aware AI responses
- 📝 **Smart Summarization** - Generate customizable summaries in multiple styles
- ❓ **Quiz Generation** - Create quizzes from your documents for better retention
- 🎴 **Flashcard Creation** - Generate flashcards for spaced repetition learning
- 📊 **Real-time Progress** - Watch as your documents are processed with live status updates
- 🏷️ **Smart Organization** - AI-generated tags and folder management
- 🔐 **Secure Authentication** - OAuth with Google, Facebook or GitHub
- 🌓 **Modern UI** - Beautiful interface with dark mode support
- ☁️ **Cloud Ready** - Direct S3 uploads for scalability

## 🎯 What Makes DocuLearn Different

Unlike simple PDF summarizers, DocuLearn transforms any document into a comprehensive learning experience:

1. **Library-First Approach** - Your document library is the home screen
2. **Multiple Learning Modes** - Chat, summarize, quiz, flashcards, and more
3. **Real-time Processing** - See exactly what's happening with your documents
4. **No Forced Features** - Upload documents without mandatory summarization
5. **Future-Ready** - Built for expansion with upcoming features like text-to-speech and collaborative study

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.9+
- Docker (for PostgreSQL)
- Ollama (for local AI) or OpenAI API key
- OAuth credentials (Google, Facebook or GitHub)

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
   uv run alembic upgrade head  # Apply migrations
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
   # - S3 configuration (optional)
   ```

5. **Run the application:**

   ```sh
   npx nx run-many -t serve
   ```

   DocuLearn will be available at:

   - Frontend: http://localhost:4200
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🧠 AI Configuration

### Using Ollama (Local AI)

Default configuration uses Ollama with the `llama2` model. Other available models:

- `mistral` - Fast and efficient
- `neural-chat` - Optimized for conversational tasks
- `phi` - Lightweight model

### Using OpenAI

Update `apps/backend/.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

## 📚 How It Works

1. **Upload** - Drop your PDF or create a text document
2. **Process** - Watch real-time progress as DocuLearn:
   - Extracts text
   - Generates embeddings
   - Creates tags
   - Prepares for interaction
3. **Learn** - Choose how to interact:
   - Chat with your document
   - Generate summaries
   - Create quizzes
   - Make flashcards
   - Export study materials

## 🛠️ Development

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

# Run tests
npx nx test backend

# Build for production
npx nx build frontend
npx nx build backend
```

### Project Structure

```
doculearn/
├── apps/
│   ├── frontend/               # Angular 19 application
│   │   └── src/app/
│   │       ├── auth/          # Authentication
│   │       ├── library/       # Document library (main screen)
│   │       ├── chat/          # Document chat interface
│   │       ├── quiz/          # Quiz generation
│   │       ├── flashcards/    # Flashcard creation
│   │       └── shared/        # Shared components
│   └── backend/               # FastAPI application
│       └── src/
│           ├── auth/          # OAuth and JWT
│           ├── upload/        # S3 direct upload
│           ├── processing/    # Document pipeline
│           ├── quiz/          # Quiz generation
│           └── flashcard/     # Flashcard service
├── docker-compose.yml         # PostgreSQL and services
└── nx.json                   # Nx monorepo configuration
```

## 🔐 OAuth Setup (Required)

Configure at least one OAuth provider:

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 credentials (Web application)
3. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/callback`
4. Add to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### GitHub OAuth

1. Go to [GitHub Settings > Developer settings > OAuth Apps](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/api/v1/auth/callback`
4. Add to `.env`:
   ```env
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   ```

## 🏗️ Architecture

### Frontend (Angular 19)

- **State Management:** NgRx SignalStore
- **UI Framework:** Tailwind CSS 4
- **Real-time Updates:** WebSocket/SSE
- **Type Safety:** Strict TypeScript

### Backend (FastAPI)

- **Async Architecture:** Full async/await
- **Database:** PostgreSQL with pgvector
- **Storage:** S3-compatible with direct upload
- **Processing:** Background tasks with Celery
- **AI Integration:** LangChain with multiple providers

### Key Features

- **Direct S3 Upload:** Faster, more reliable uploads
- **Real-time Progress:** WebSocket status updates
- **Modular Services:** Clean separation of concerns
- **Vector Search:** Semantic document search
- **Extensible:** Built for future features

## 🚀 Roadmap

### Current Release

- ✅ Document upload and processing
- ✅ Interactive chat
- ✅ Smart summarization
- ✅ Quiz generation
- ✅ Flashcard creation

### Coming Soon

- 🎧 Text-to-speech
- 📖 Distraction-free reading mode
- 👥 Collaborative study groups
- 📊 Learning analytics
- 🔄 Spaced repetition system
- 📱 Mobile app

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for more information.

## 📄 License

MIT License - see LICENSE file for details

---

**DocuLearn** - Transform Documents into Knowledge 🚀

Visit us at [doculearn.ai](https://doculearn.ai)
