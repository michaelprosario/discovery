#!/usr/bin/env bash
# Setup script for the Discovery project using uv

set -e

echo "🚀 Setting up Discovery project with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Sync dependencies
echo "📦 Installing dependencies..."
uv sync

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  • Run tests: uv run pytest tests/ -v"
echo "  • Start server: uv run uvicorn src.api.main:app --reload"
echo "  • View docs: http://localhost:8000/docs"
