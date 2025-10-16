#!/usr/bin/env bash
# Development server script using uv

set -e

echo "🚀 Starting Discovery API server..."

uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
