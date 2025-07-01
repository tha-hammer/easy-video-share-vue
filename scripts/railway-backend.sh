#!/bin/bash

# Railway Backend Configuration Script
# Switches the backend directory to use the FastAPI backend configuration

set -e

echo "🚀 Switching to Railway Backend configuration..."

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

# Copy backend configuration
if [ -f "railway.json" ]; then
    echo "✅ Backend configuration is already active"
else
    echo "❌ Error: backend/railway.json not found"
    exit 1
fi

echo ""
echo "🎉 Railway Backend configuration is ready!"
echo ""
echo "Next steps:"
echo "1. Deploy to Railway with Source Directory: backend"
echo "2. Add environment variables for backend service"
echo "3. Test with: curl https://your-backend-service.up.railway.app/health"
echo ""
echo "Current configuration: FastAPI Backend" 