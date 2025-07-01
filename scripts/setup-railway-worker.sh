#!/bin/bash

# Railway Worker Setup Script
# This script helps prepare the backend directory for Railway worker deployment

set -e

echo "🚀 Setting up Railway Worker deployment..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

# Copy worker configuration
echo "📋 Setting up worker configuration..."
cd backend

# Rename worker config to railway.json for deployment
if [ -f "railway.worker.json" ]; then
    cp railway.worker.json railway.json
    echo "✅ Copied railway.worker.json to railway.json"
else
    echo "❌ Error: railway.worker.json not found in backend directory"
    exit 1
fi

# Make worker health script executable
if [ -f "worker_health.py" ]; then
    chmod +x worker_health.py
    echo "✅ Made worker_health.py executable"
else
    echo "❌ Error: worker_health.py not found in backend directory"
    exit 1
fi

echo ""
echo "🎉 Railway Worker setup complete!"
echo ""
echo "Next steps:"
echo "1. Go to Railway.app and create a new project"
echo "2. Connect to your GitHub repository"
echo "3. Set Source Directory to: backend"
echo "4. Add the same environment variables as your backend service"
echo "5. Deploy the worker"
echo ""
echo "Environment variables needed:"
echo "- AWS_REGION, AWS_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
echo "- DYNAMODB_TABLE_NAME"
echo "- REDIS_URL (or REDIS_HOST, REDIS_PORT, REDIS_PASSWORD)"
echo "- GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION (optional)"
echo "- RAILWAY_ENVIRONMENT=production"
echo "- PORT=8001"
echo ""
echo "After deployment, test with:"
echo "curl https://your-worker-service.railway.app/health" 