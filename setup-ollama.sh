#!/bin/bash

echo "🦙 Setting up Ollama for PDF Summarizer..."
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo ""
    echo "Please install Ollama first:"
    echo "  - macOS: brew install ollama"
    echo "  - Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  - Or visit: https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama is installed"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 3
fi

echo "✅ Ollama is running"

# Pull the default model
MODEL="llama2"
echo ""
echo "📥 Pulling $MODEL model (this may take a while)..."
ollama pull $MODEL

echo ""
echo "✅ Model $MODEL is ready"

# Create .env file if it doesn't exist
if [ ! -f "apps/backend/.env" ]; then
    echo ""
    echo "📝 Creating .env file from example..."
    cp apps/backend/.env.example apps/backend/.env
    echo "✅ Created apps/backend/.env"
    echo ""
    echo "⚠️  Please update the JWT_SECRET_KEY in apps/backend/.env with a secure value"
fi

echo ""
echo "🎉 Ollama setup complete!"
echo ""
echo "Available models for summarization:"
ollama list | grep -E "^(llama2|mistral|neural-chat|phi)" || echo "  - llama2 (default)"
echo ""
echo "To use a different model, update OLLAMA_MODEL in apps/backend/.env"
echo ""
echo "To start the application:"
echo "  npx nx run-many -t serve"