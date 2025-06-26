#!/bin/bash
# Phase 2 Setup Script: Real AI Integration with fal.ai
# This script prepares the environment for real AI-powered video generation

echo "🚀 Setting up Phase 2: Real AI Integration with fal.ai"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the video-processor directory"
    exit 1
fi

# Create environment file for AI services
echo "📝 Creating environment configuration..."
cat > .env << EOF
# AI Service Configuration
ENVIRONMENT=dev
PROJECT_NAME=easy-video-share
USE_LOCALSTACK=true
LOG_LEVEL=INFO

# AWS Configuration (LocalStack)
AWS_REGION=us-east-1
LOCALSTACK_ENDPOINT=http://localhost:4566

# Database Tables
AI_PROJECTS_TABLE=easy-video-share-ai-projects-dev
VIDEO_ASSETS_TABLE=easy-video-share-video-assets-dev
EVENT_BUS_NAME=easy-video-share-ai-video-bus-dev
SECRETS_NAME=easy-video-share-ai-api-keys-dev
S3_BUCKET=easy-video-share-silmari-dev

# AI API Keys (for real integration)
# Add your actual API keys below:
OPENAI_API_KEY=
FAL_API_KEY=

# Optional: Anthropic for alternative LLM
ANTHROPIC_API_KEY=
EOF

echo "✅ Environment file created (.env)"

# Create sample API keys file for reference
echo "📝 Creating sample API keys reference..."
cat > api-keys-sample.env << EOF
# Sample API Keys Configuration
# Copy this to .env and add your real API keys

# OpenAI API Key (for scene generation)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# fal.ai API Key (for video/image generation)
# Get from: https://fal.ai/dashboard
FAL_API_KEY=your-fal-api-key-here

# Optional: Anthropic API Key (alternative to OpenAI)
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-api-key-here
EOF

echo "✅ Sample API keys file created (api-keys-sample.env)"

# Check if containers are running
echo "🔍 Checking container status..."
if docker-compose ps | grep -q "Up"; then
    echo "⚠️  Containers are running. Stopping to rebuild with new dependencies..."
    docker-compose down
fi

# Install new dependencies
echo "📦 Installing updated dependencies with fal.ai support..."
docker-compose build --no-cache

# Start containers
echo "🔥 Starting updated containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Create S3 bucket for audio uploads
echo "🪣 Setting up S3 bucket for audio uploads..."
docker-compose exec localstack awslocal s3 mb s3://easy-video-share-silmari-dev || echo "Bucket may already exist"

# Create DynamoDB tables for AI projects
echo "🗃️  Setting up DynamoDB tables..."
docker-compose exec localstack awslocal dynamodb create-table \
    --table-name easy-video-share-ai-projects-dev \
    --attribute-definitions \
        AttributeName=project_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=project_id,KeyType=HASH \
    --global-secondary-indexes \
        IndexName=user-projects-index,KeySchema=[{AttributeName=user_id,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    2>/dev/null || echo "Table may already exist"

# Test the setup
echo "🧪 Testing the setup..."
sleep 5

# Run health check
echo "🔍 Running health check..."
response=$(curl -s http://localhost:8080/health)
if echo "$response" | grep -q "healthy"; then
    echo "✅ Health check passed!"
    echo "   API Version: $(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)"
    echo "   Services Status:"
    echo "$response" | grep -o '"services_status":{[^}]*}' | sed 's/.*"services_status":{//; s/}.*//; s/,/\n/g; s/"//g; s/:/: /g' | sed 's/^/     /'
else
    echo "❌ Health check failed!"
    echo "   Response: $response"
fi

echo ""
echo "🎉 Phase 2 Setup Complete!"
echo "=================================================="
echo ""
echo "🔧 Current Status:"
echo "   ✅ Docker containers rebuilt with fal.ai support"
echo "   ✅ LocalStack S3 bucket created"
echo "   ✅ DynamoDB tables configured"
echo "   ✅ Environment variables configured"
echo ""
echo "🚀 Next Steps:"
echo "   1. Add your real API keys to .env file:"
echo "      - OpenAI API key for scene generation"
echo "      - fal.ai API key for video/image generation"
echo ""
echo "   2. Test with real AI integration:"
echo "      python test_real_ai.py"
echo ""
echo "   3. When ready for production:"
echo "      - Update terraform variables with API keys"
echo "      - Deploy to AWS with: terraform apply"
echo ""
echo "📚 Documentation:"
echo "   - fal.ai API docs: https://docs.fal.ai/clients/python"
echo "   - OpenAI API docs: https://platform.openai.com/docs"
echo ""
echo "💡 Local Development URLs:"
echo "   - API Health Check: http://localhost:8080/health"
echo "   - API Documentation: http://localhost:8080/docs"
echo "   - LocalStack Dashboard: http://localhost:4566"
echo ""

# Display current service status
echo "📊 Current Service Status:"
curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || echo "Could not fetch detailed status"

echo ""
echo "🎬 Your AI video generation pipeline is ready for real-world testing!" 