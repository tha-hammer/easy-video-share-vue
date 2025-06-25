#!/bin/bash

# Setup Frontend Environment Variables for Vue3 App
# This script gets AWS credentials from Terraform and creates the .env file

set -e

echo "🔧 Setting up Vue3 Frontend Environment Variables"
echo "================================================="

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

BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null)
ACCESS_KEY_ID=$(terraform output -raw app_user_access_key_id 2>/dev/null)
SECRET_ACCESS_KEY=$(terraform output -raw app_user_secret_access_key 2>/dev/null)
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null)
API_ENDPOINT=$(terraform output -raw api_gateway_endpoint 2>/dev/null)
API_VIDEOS_ENDPOINT=$(terraform output -raw api_videos_endpoint 2>/dev/null)
API_ADMIN_USERS_ENDPOINT=$(terraform output -raw api_admin_users_endpoint 2>/dev/null)
API_ADMIN_VIDEOS_ENDPOINT=$(terraform output -raw api_admin_videos_endpoint 2>/dev/null)
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id 2>/dev/null)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id 2>/dev/null)

cd ..

# Validate outputs
if [ -z "$BUCKET_NAME" ] || [ -z "$ACCESS_KEY_ID" ] || [ -z "$SECRET_ACCESS_KEY" ] || [ -z "$API_ENDPOINT" ] || [ -z "$COGNITO_USER_POOL_ID" ]; then
    echo "❌ Error: Could not retrieve all required values from Terraform"
    echo "Make sure your infrastructure is deployed and terraform outputs are available"
    echo "Required outputs: bucket_name, app_user_access_key_id, app_user_secret_access_key, api_gateway_endpoint, cognito_user_pool_id"
    exit 1
fi

# Create .env file in Vue3 app root directory
echo "📝 Creating .env file in Vue3 project root..."

cat > .env << EOF
# AWS Configuration for Easy Video Share Vue3 App
# Generated automatically from Terraform outputs
# DO NOT commit this file to git

VITE_AWS_REGION=${AWS_REGION}
VITE_AWS_BUCKET_NAME=${BUCKET_NAME}
VITE_AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}
VITE_AWS_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}

# API Configuration
VITE_API_ENDPOINT=${API_ENDPOINT}
VITE_API_VIDEOS_ENDPOINT=${API_VIDEOS_ENDPOINT}

# Admin API Configuration
VITE_API_ADMIN_USERS_ENDPOINT=${API_ADMIN_USERS_ENDPOINT}
VITE_API_ADMIN_VIDEOS_ENDPOINT=${API_ADMIN_VIDEOS_ENDPOINT}

# Cognito Configuration
VITE_COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID}
VITE_COGNITO_CLIENT_ID=${COGNITO_CLIENT_ID}
VITE_COGNITO_REGION=${AWS_REGION}
EOF

echo "✅ Vue3 Frontend environment variables configured!"
echo ""
echo "📋 Configuration Summary:"
echo "========================"
echo "Region:      ${AWS_REGION}"
echo "Bucket:      ${BUCKET_NAME}"
echo "Access Key:  ${ACCESS_KEY_ID}"
echo "API Endpoint: ${API_ENDPOINT}"
echo ""
echo "🚀 Next steps:"
echo "1. npm install"
echo "2. npm run dev"
echo ""
echo "🔒 Security Note: Keep your .env file secure and never commit it to git!"

echo ""
echo "✨ Vue3 app ready to start developing!" 