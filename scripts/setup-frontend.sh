#!/bin/bash

# Setup Frontend Environment Variables for Vue3 App with AI Video Support
# This script gets AWS credentials from Terraform and creates the .env file

set -e

echo "🔧 Setting up Vue3 Frontend Environment Variables for AI Video"
echo "============================================================="

# Check if we're in the right directory (Vue3 app structure)
if [ ! -d "terraform" ] || [ ! -f "package.json" ] || [ ! -d "src" ]; then
    echo "❌ Error: Run this script from the Vue3 project root directory"
    echo "Expected: terraform/, package.json, and src/ directories"
    exit 1
fi

# Check if Terraform state exists
if [ ! -f "terraform/terraform.tfstate" ]; then
    echo "❌ Error: Terraform state not found. Deploy infrastructure first:"
    echo "cd terraform && terraform apply"
    exit 1
fi

# Get credentials from Terraform
echo "📋 Getting AWS credentials and API endpoints from Terraform..."

cd terraform

# Core AWS Infrastructure
BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null)
AUDIO_BUCKET_NAME=$(terraform output -raw audio_bucket_name 2>/dev/null)
ACCESS_KEY_ID=$(terraform output -raw app_user_access_key_id 2>/dev/null)
SECRET_ACCESS_KEY=$(terraform output -raw app_user_secret_access_key 2>/dev/null)
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null)

# API Gateway Endpoints
API_ENDPOINT=$(terraform output -raw api_gateway_endpoint 2>/dev/null)
API_VIDEOS_ENDPOINT=$(terraform output -raw api_videos_endpoint 2>/dev/null)

# Admin API Endpoints
API_ADMIN_USERS_ENDPOINT=$(terraform output -raw api_admin_users_endpoint 2>/dev/null)
API_ADMIN_VIDEOS_ENDPOINT=$(terraform output -raw api_admin_videos_endpoint 2>/dev/null)

# Audio API Endpoints
API_AUDIO_ENDPOINT=$(terraform output -raw api_audio_endpoint 2>/dev/null)
API_AUDIO_UPLOAD_ENDPOINT=$(terraform output -raw api_audio_upload_endpoint 2>/dev/null)

# Cognito Configuration
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id 2>/dev/null)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id 2>/dev/null)

# AI Video Configuration (Modern Authentication)
API_AI_VIDEO_ENDPOINT="${API_ENDPOINT}/ai-video"

# Google Cloud Configuration (Modern Authentication)
# These will be set from environment or user input
GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID:-"easy-video-share"}
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION:-"us-central1"}
GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL=${GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL:-"easy-vide-share-sa@easy-video-share.iam.gserviceaccount.com"}

# OpenAI Configuration
OPENAI_API_KEY=${OPENAI_API_KEY:-"sk-your-openai-api-key"}

cd ..

# Validate required outputs
if [ -z "$BUCKET_NAME" ] || [ -z "$AUDIO_BUCKET_NAME" ] || [ -z "$ACCESS_KEY_ID" ] || [ -z "$SECRET_ACCESS_KEY" ] || [ -z "$API_ENDPOINT" ] || [ -z "$COGNITO_USER_POOL_ID" ]; then
    echo "❌ Error: Could not retrieve all required values from Terraform"
    echo "Make sure your infrastructure is deployed and terraform outputs are available"
    echo "Required outputs: bucket_name, audio_bucket_name, app_user_access_key_id, app_user_secret_access_key, api_gateway_endpoint, cognito_user_pool_id"
    exit 1
fi

# Create .env file in Vue3 app root directory
echo "📝 Creating .env file with AI Video support in Vue3 project root..."

cat > .env << EOF
# Easy Video Share Vue3 App - AI Video Configuration
# Generated automatically from Terraform outputs
# DO NOT commit this file to git

# AWS Configuration
VITE_AWS_REGION=${AWS_REGION}
VITE_AWS_BUCKET_NAME=${BUCKET_NAME}
VITE_AWS_AUDIO_BUCKET_NAME=${AUDIO_BUCKET_NAME}
VITE_AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}
VITE_AWS_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}

# API Configuration - Core
VITE_APP_API_URL=${API_ENDPOINT}
VITE_API_ENDPOINT=${API_ENDPOINT}
VITE_API_VIDEOS_ENDPOINT=${API_VIDEOS_ENDPOINT}

# Audio API Configuration
VITE_API_AUDIO_ENDPOINT=${API_AUDIO_ENDPOINT}
VITE_API_AUDIO_UPLOAD_ENDPOINT=${API_AUDIO_UPLOAD_ENDPOINT}

# AI Video API Configuration
VITE_API_AI_VIDEO_ENDPOINT=${API_AI_VIDEO_ENDPOINT}

# Admin API Configuration
VITE_API_ADMIN_USERS_ENDPOINT=${API_ADMIN_USERS_ENDPOINT}
VITE_API_ADMIN_VIDEOS_ENDPOINT=${API_ADMIN_VIDEOS_ENDPOINT}

# Cognito Authentication Configuration
VITE_COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID}
VITE_COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID}
VITE_COGNITO_REGION=${AWS_REGION}

# Google Cloud Configuration (Modern Authentication)
VITE_GOOGLE_CLOUD_PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID}
VITE_GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}
VITE_GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL=${GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL}

# OpenAI Configuration
VITE_OPENAI_API_KEY=${OPENAI_API_KEY}

# Feature Flags
VITE_ENABLE_AI_VIDEO=true
VITE_ENABLE_AUDIO_UPLOAD=true
VITE_ENABLE_ADMIN_PANEL=true

# Upload Configuration
VITE_MAX_AUDIO_FILE_SIZE=104857600
VITE_MAX_VIDEO_FILE_SIZE=524288000
VITE_SUPPORTED_AUDIO_FORMATS=mp3,wav,m4a,aac,ogg,webm
VITE_SUPPORTED_VIDEO_FORMATS=mp4,webm,avi,mov

# UI Configuration
VITE_APP_NAME=Easy Video Share
VITE_APP_VERSION=2.0.0
VITE_ENABLE_DEBUG=false
EOF

echo "✅ Vue3 Frontend environment variables configured with AI Video support!"
echo ""
echo "📋 Configuration Summary:"
echo "========================"
echo "Region:           ${AWS_REGION}"
echo "Video Bucket:     ${BUCKET_NAME}"
echo "Audio Bucket:     ${AUDIO_BUCKET_NAME}"
echo "Access Key:       ${ACCESS_KEY_ID}"
echo "API Endpoint:     ${API_ENDPOINT}"
echo "Audio API:        ${API_AUDIO_ENDPOINT}"
echo "AI Video API:     ${API_AI_VIDEO_ENDPOINT}"
echo "Cognito Pool:     ${COGNITO_USER_POOL_ID}"
echo ""
echo "🎯 AI Video Features Configured:"
echo "================================"
echo "✅ Audio Upload Infrastructure"
echo "✅ AI Video Generation API Endpoints"
echo "✅ Audio Processing Pipeline"
echo "✅ Enhanced Authentication"
echo "✅ Admin Panel Integration"
echo ""
echo "🚀 Next steps:"
echo "1. npm install"
echo "2. npm run dev"
echo "3. Test AI Video page at /ai-video"
echo ""
echo "🔒 Security Note: Keep your .env file secure and never commit it to git!"

echo ""
echo "✨ Vue3 app ready for AI Video development!" 