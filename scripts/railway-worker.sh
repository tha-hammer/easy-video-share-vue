#!/bin/bash

# Railway Worker Configuration Script
# Switches the backend directory to use the Celery worker configuration

set -e

echo "🤖 Switching to Railway Worker configuration..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

cd backend

# Backup current railway.json if it exists
if [ -f "railway.json" ]; then
    cp railway.json railway.json.backup
    echo "📋 Backed up current railway.json"
fi

# Copy worker configuration
if [ -f "railway.worker.json" ]; then
    cp railway.worker.json railway.json
    echo "✅ Switched to worker configuration"
else
    echo "❌ Error: railway.worker.json not found"
    exit 1
fi

echo ""
echo "🎉 Railway Worker configuration is ready!"
echo ""
echo "Next steps:"
echo "1. Deploy to Railway with Source Directory: backend"
echo "2. Add the same environment variables as backend service"
echo "3. Add PORT=8001 to environment variables"
echo "4. Test with: curl https://your-worker-service.up.railway.app/health"
echo ""
echo "Current configuration: Celery Worker" 