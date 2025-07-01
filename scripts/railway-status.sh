#!/bin/bash

# Railway Configuration Status Script
# Shows which Railway configuration is currently active

set -e

echo "🔍 Checking Railway configuration status..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

cd backend

if [ ! -f "railway.json" ]; then
    echo "❌ No railway.json found in backend directory"
    exit 1
fi

# Check which configuration is active by looking at the startCommand
if grep -q "uvicorn main:app" railway.json; then
    echo "✅ Current configuration: FastAPI Backend"
    echo "   - Handles API requests and dispatches Celery tasks"
    echo "   - Uses Dockerfile (not Dockerfile.worker)"
    echo "   - Start command: uvicorn main:app"
elif grep -q "python worker_health.py" railway.json; then
    echo "✅ Current configuration: Celery Worker"
    echo "   - Processes videos in the background"
    echo "   - Uses Dockerfile.worker"
    echo "   - Start command: python worker_health.py"
else
    echo "❓ Unknown configuration detected"
    echo "   Start command in railway.json:"
    grep "startCommand" railway.json || echo "   No startCommand found"
fi

echo ""
echo "Available configurations:"
echo "  backend/railway.json      - FastAPI Backend"
echo "  backend/railway.worker.json - Celery Worker"
echo ""
echo "To switch configurations:"
echo "  ./scripts/railway-backend.sh  - Switch to backend"
echo "  ./scripts/railway-worker.sh   - Switch to worker" 