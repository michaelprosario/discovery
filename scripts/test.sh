#!/usr/bin/env bash
# Test script using uv

set -e

echo "🧪 Running tests with uv..."

# Default to all tests
TEST_PATH="${1:-tests/}"

uv run pytest "$TEST_PATH" -v

echo ""
echo "✅ Tests completed"
