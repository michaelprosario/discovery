#!/usr/bin/env bash
# Script to build discoveryPortalReact and copy the dist contents to src/api/static

# Exit immediately if a command exits with a non-zero status
set -e

# Get the directory of the script to make paths relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

FRONTEND_DIR="$WORKSPACE_DIR/discoveryPortalReact"
STATIC_DIR="$WORKSPACE_DIR/src/api/static"

echo "🚀 Starting frontend build process..."
echo "📂 Workspace: $WORKSPACE_DIR"
echo "📂 Frontend:  $FRONTEND_DIR"
echo "📂 Static:    $STATIC_DIR"

# 1. Step into the React app directory
cd "$FRONTEND_DIR"

# 2. Check and install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 node_modules not found. Installing dependencies..."
    npm install
else
    echo "📦 node_modules found. Checking/updating dependencies..."
    npm install
fi

# 3. Build the frontend
echo "🏗️ Building the React application..."
npm run build

# 4. Ensure the static directory exists
mkdir -p "$STATIC_DIR"

# 5. Clean up old build files in static directory (excluding the archive/ folder if we want to keep it)
echo "🧹 Cleaning up previous build assets in $STATIC_DIR..."
# Remove assets directory if it exists
if [ -d "$STATIC_DIR/assets" ]; then
    rm -rf "$STATIC_DIR/assets"
fi
# Remove index.html
if [ -f "$STATIC_DIR/index.html" ]; then
    rm -f "$STATIC_DIR/index.html"
fi
# Remove any vite.svg or other files from dist root if they exist
if [ -f "$STATIC_DIR/vite.svg" ]; then
    rm -f "$STATIC_DIR/vite.svg"
fi

# 6. Move the build contents to the static directory
echo "🚚 Moving build files from dist/ to $STATIC_DIR..."
cp -r dist/* "$STATIC_DIR/"

echo "✨ Frontend build and deployment complete!"
echo "📂 Static files contents:"
ls -la "$STATIC_DIR"
