#!/bin/bash
# Startup script for Hermes that avoids .env conflicts

# Export environment variables if they exist
export PYTHONUNBUFFERED=1

# Use PORT from environment or default to 8590
PORT=${PORT:-8590}

echo "🚀 Starting Hermes on port $PORT"
echo "   GEMINI_API_KEY is $(if [ -z "$GEMINI_API_KEY" ]; then echo "NOT SET ⚠️"; else echo "SET ✓"; fi)"

# Start the Python server
exec python hermes_server.py