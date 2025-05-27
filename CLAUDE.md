# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a PDF summarizer application built as an Nx monorepo with Angular 19.2.0. The project uses pnpm as the package manager and TypeScript 5.7.2.

## Essential Commands

### Frontend Development
- `npx nx serve frontend` - Start the Angular development server (http://localhost:4200)
- `npx nx build frontend` - Build the Angular application for production
- `npx nx lint frontend` - Run ESLint on frontend code

### Backend Development
- `npx nx serve backend` - Start the FastAPI development server (http://localhost:8000)
- `npx nx install backend` - Install Python dependencies
- `npx nx lint backend` - Run Ruff linter on backend code
- `npx nx format backend` - Format backend code with Ruff

### Run Both Services
- `npx nx run-many -t serve` - Run both frontend and backend concurrently

### Backend API Development
When developing, the Angular app proxies API requests to the backend:
- `/api/*` routes are proxied to `http://localhost:8000`
- `/health`, `/docs`, `/redoc`, and `/openapi.json` are also proxied
- Proxy configuration is in `apps/frontend/proxy.conf.json`

### Code Quality
- `npx nx format:check` - Check code formatting
- `npx nx format:write` - Auto-fix code formatting
- `npx nx affected:lint` - Lint only affected projects

## Architecture

### Monorepo Structure
- **apps/frontend/** - Angular 19 standalone application
  - Uses Angular standalone components (no NgModules)
  - Router configured but no routes implemented yet
  - SCSS for styling
  - Zone.js for change detection

- **apps/backend/** - FastAPI Python application
  - REST API for PDF processing and summarization
  - Uses LangChain and OpenAI for text summarization
  - PyPDF for PDF text extraction
  - Requires OPENAI_API_KEY environment variable

### Key Technical Decisions
- **Build System**: Nx workspace with @nx/angular executor
- **Component Architecture**: Standalone components (modern Angular approach)
- **Testing**: Currently no test runners configured
- **Styling**: SCSS with component-scoped styles
- **TypeScript**: Strict mode enabled with strict template checking

### Configuration Files
- `nx.json` - Nx workspace configuration
- `tsconfig.base.json` - Base TypeScript configuration for the workspace
- `apps/frontend/project.json` - Frontend app-specific Nx configuration
- `eslint.config.mjs` - ESLint configuration with Nx and TypeScript plugins

## Development Guidelines

When implementing PDF summarization features:
1. Use Angular standalone components for new features
2. Follow the existing SCSS styling approach
3. Utilize Angular's built-in services for HTTP requests and state management
4. Keep components in the `apps/frontend/src/app/` directory
5. Use TypeScript strict mode - ensure all variables are properly typed