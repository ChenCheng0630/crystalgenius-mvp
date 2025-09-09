#!/bin/bash

# CrystalGenius MVP Setup Script

set -e

echo "🚀 CrystalGenius MVP Setup"
echo "========================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo ""
    echo "Please install Docker Desktop:"
    echo "  macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
    echo "  Linux: https://docs.docker.com/desktop/install/linux-install/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is installed but not running."
    echo ""
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is ready"

# Create backend .env if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env file..."
    cat > backend/.env << EOF
# OpenAI Configuration (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Feature Flags
ENABLE_LLM_CHAT=true
ENABLE_LLM_FILTERS=true

# Optional: Curations config
# CURATIONS_CONFIG=config/curations.yaml
EOF
    echo "✅ Created backend/.env"
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your OpenAI API key!"
    echo "   You can get one from: https://platform.openai.com/api-keys"
    echo ""
else
    echo "✅ backend/.env already exists"
fi

# Check if data files exist
if [ ! -f "data/products_full.csv" ]; then
    echo "❌ Data files not found in data/ directory"
    echo "   Please ensure you have the CSV files:"
    echo "   - data/products_full.csv"
    echo "   - data/category.csv"
    echo "   - data/parent_category.csv"
    exit 1
fi

echo "✅ Data files found"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your OpenAI API key"
echo "2. Run: make up"
echo "3. Open: http://localhost:3000"
echo ""
echo "Available commands:"
echo "  make up      - Start all services"
echo "  make down    - Stop all services"
echo "  make logs    - View logs"
echo "  make health  - Check service health"
echo ""
