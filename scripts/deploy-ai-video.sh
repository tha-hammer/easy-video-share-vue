#!/bin/bash

# AI Video Deployment Script for Easy Video Share
# This script builds the Lambda layer and deploys the AI video infrastructure

echo "🚀 Deploying AI Video Infrastructure for Easy Video Share"
echo ""

# Configuration
PROJECT_ROOT=$(pwd)
LAMBDA_LAYER_DIR="lambda-layer"
LAMBDA_LAYER_ZIP="terraform/ai_video_layer.zip"
LAMBDA_ZIP="terraform/ai_video_lambda.zip"

# Step 1: Create Lambda layer directory
echo "🔧 Step 1: Creating Lambda layer..."
if [ -d "$LAMBDA_LAYER_DIR" ]; then
    rm -rf "$LAMBDA_LAYER_DIR"
fi
mkdir -p "$LAMBDA_LAYER_DIR/nodejs"

# Step 2: Create package.json for Lambda layer
echo "🔧 Step 2: Creating package.json for Lambda layer..."
cat > "$LAMBDA_LAYER_DIR/nodejs/package.json" << 'EOF'
{
  "name": "ai-video-layer",
  "version": "1.0.0",
  "description": "AI Video Generation Dependencies",
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.450.0",
    "@aws-sdk/client-s3": "^3.450.0",
    "@aws-sdk/client-secrets-manager": "^3.450.0",
    "@aws-sdk/client-transcribe": "^3.450.0",
    "@aws-sdk/lib-dynamodb": "^3.450.0",
    "google-auth-library": "^9.0.0",
    "@google-cloud/vertexai": "^0.1.0",
    "openai": "^4.20.0"
  }
}
EOF

# Step 3: Install dependencies
echo "🔧 Step 3: Installing Lambda layer dependencies..."
cd "$LAMBDA_LAYER_DIR/nodejs"
npm install --production
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    cd "$PROJECT_ROOT"
    exit 1
fi
cd "$PROJECT_ROOT"

# Step 4: Create Lambda layer ZIP using PowerShell
echo "🔧 Step 4: Creating Lambda layer ZIP..."
if [ -f "$LAMBDA_LAYER_ZIP" ]; then
    rm "$LAMBDA_LAYER_ZIP"
fi

# Create the correct Lambda layer structure: nodejs/node_modules/
# We need to zip the nodejs directory itself, not its contents
cd "$LAMBDA_LAYER_DIR"
powershell -Command "Compress-Archive -Path 'nodejs' -DestinationPath '../$LAMBDA_LAYER_ZIP' -Force"
if [ $? -ne 0 ]; then
    echo "❌ Failed to create Lambda layer ZIP"
    cd "$PROJECT_ROOT"
    exit 1
fi
cd "$PROJECT_ROOT"

echo "✅ Lambda layer ZIP created: $LAMBDA_LAYER_ZIP"

# Verify Lambda layer structure
echo "🔍 Verifying Lambda layer structure..."
# Simple verification - check if file exists and has reasonable size
if [ -f "$LAMBDA_LAYER_ZIP" ]; then
    FILE_SIZE=$(stat -c%s "$LAMBDA_LAYER_ZIP" 2>/dev/null || stat -f%z "$LAMBDA_LAYER_ZIP" 2>/dev/null || echo "unknown")
    if [ "$FILE_SIZE" -gt 1000000 ] 2>/dev/null; then
        echo "✅ Lambda layer ZIP created successfully"
        echo "   File size: $FILE_SIZE bytes"
        echo "   Note: Structure verified in test script"
    else
        echo "❌ Lambda layer ZIP is too small \($FILE_SIZE bytes\)"
        echo "   Expected: > 1MB for dependencies"
        exit 1
    fi
else
    echo "❌ Lambda layer ZIP not found!"
    exit 1
fi

# Step 5: Create Lambda function ZIP
echo "🔧 Step 5: Creating Lambda function ZIP..."
if [ -f "$LAMBDA_ZIP" ]; then
    rm "$LAMBDA_ZIP"
fi

# Copy Lambda function to a temporary directory
TEMP_LAMBDA_DIR="temp-lambda"
if [ -d "$TEMP_LAMBDA_DIR" ]; then
    rm -rf "$TEMP_LAMBDA_DIR"
fi
mkdir -p "$TEMP_LAMBDA_DIR"

cp "terraform/lambda-ai-video/ai-video.js" "$TEMP_LAMBDA_DIR/ai-video.js"

# Create ZIP using PowerShell in terraform directory
powershell -Command "Compress-Archive -Path '$TEMP_LAMBDA_DIR/*' -DestinationPath '$LAMBDA_ZIP' -Force"
if [ $? -ne 0 ]; then
    echo "❌ Failed to create Lambda function ZIP"
    cd "$PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "✅ Lambda function ZIP created: $LAMBDA_ZIP"

# Clean up temporary files
rm -rf "$TEMP_LAMBDA_DIR"
rm -rf "$LAMBDA_LAYER_DIR"

# Step 6: Check Terraform configuration
echo "🔧 Step 6: Checking Terraform configuration..."
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo "❌ terraform.tfvars not found. Please run the Google Cloud setup script first:"
    echo "   ./scripts/setup-google-cloud.sh"
    exit 1
fi

# Check if required variables are set
if ! grep -q "google_cloud_project_id" "terraform/terraform.tfvars"; then
    echo "❌ google_cloud_project_id not found in terraform.tfvars"
    echo "   Please run the Google Cloud setup script first"
    exit 1
fi

if ! grep -q "openai_api_key" "terraform/terraform.tfvars"; then
    echo "⚠️  openai_api_key not found in terraform.tfvars"
    echo "   Please add your OpenAI API key to terraform.tfvars"
fi

# Step 7: Deploy with Terraform
echo "🔧 Step 7: Deploying with Terraform..."
cd terraform

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo "   Initializing Terraform..."
    terraform init
    if [ $? -ne 0 ]; then
        echo "❌ Terraform initialization failed"
        cd "$PROJECT_ROOT"
        exit 1
    fi
fi

# Delete existing Lambda function if it exists (to avoid conflicts)
echo "   Checking for existing Lambda function..."
EXISTING_FUNCTION=$(aws lambda get-function --function-name "easy-video-share-ai-video-processor" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   Found existing Lambda function, deleting it..."
    aws lambda delete-function --function-name "easy-video-share-ai-video-processor"
    if [ $? -eq 0 ]; then
        echo "   ✅ Existing Lambda function deleted"
        # Wait a moment for deletion to complete
        sleep 5
    else
        echo "   ⚠️  Failed to delete existing function, continuing anyway..."
    fi
else
    echo "   No existing Lambda function found"
fi

# Delete existing Lambda layer if it exists (to force recreation)
echo "   Checking for existing Lambda layer..."
EXISTING_LAYER=$(aws lambda list-layers --query 'Layers[?contains(LayerName, `ai-video-layer`)].LayerName' --output text 2>/dev/null)
if [ ! -z "$EXISTING_LAYER" ]; then
    echo "   Found existing Lambda layer: $EXISTING_LAYER"
    echo "   Deleting layer to force recreation..."
    aws lambda delete-layer-version --layer-name "$EXISTING_LAYER" --version-number 1 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ Existing Lambda layer deleted"
        sleep 3
    else
        echo "   ⚠️  Failed to delete existing layer, continuing anyway..."
    fi
else
    echo "   No existing Lambda layer found"
fi

# Force Terraform to recreate resources
echo "   Forcing Terraform to recreate resources..."
terraform taint aws_lambda_layer_version.ai_video_layer 2>/dev/null
terraform taint aws_lambda_function.ai_video_processor 2>/dev/null

# Plan the deployment
echo "   Planning deployment..."
terraform plan -out=tfplan
if [ $? -ne 0 ]; then
    echo "❌ Terraform plan failed"
    cd "$PROJECT_ROOT"
    exit 1
fi

# Apply the deployment
echo "   Applying deployment..."
terraform apply tfplan
if [ $? -ne 0 ]; then
    echo "❌ Terraform apply failed"
    cd "$PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT"

# Step 8: Get API Gateway URL
echo "🔧 Step 8: Getting API Gateway URL..."
API_URL=$(cd terraform && terraform output -raw api_gateway_endpoint 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ API Gateway URL: $API_URL"
    echo "   AI Video endpoint: $API_URL/ai-video"
else
    echo "⚠️  Could not get API Gateway URL"
fi

# Step 9: Update frontend configuration
echo "🔧 Step 9: Updating frontend configuration..."
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    if ! grep -q "VITE_API_BASE_URL" "$ENV_FILE"; then
        echo "" >> "$ENV_FILE"
        echo "# API Configuration" >> "$ENV_FILE"
        echo "VITE_API_BASE_URL=$API_URL" >> "$ENV_FILE"
        echo "✅ Added API base URL to .env file"
    fi
else
    echo "# API Configuration" > "$ENV_FILE"
    echo "VITE_API_BASE_URL=$API_URL" >> "$ENV_FILE"
    echo "✅ Created .env file with API base URL"
fi

echo ""
echo "🎉 AI Video infrastructure deployment completed!"
echo ""
echo "📋 What was deployed:"
echo "   ✅ Lambda function for AI video processing"
echo "   ✅ Lambda layer with dependencies"
echo "   ✅ API Gateway endpoints"
echo "   ✅ Secrets Manager for credentials"
echo "   ✅ CloudWatch logging"
echo ""
echo "🔗 Test your AI video features:"
echo "   1. Start your Vue development server: npm run dev"
echo "   2. Upload an audio file"
echo "   3. Navigate to AI Video generation"
echo "   4. Test the AI video generation workflow"
echo ""
echo "📊 Monitor your deployment:"
echo "   - CloudWatch Logs: /aws/lambda/easy-video-share-ai-video-processor"
echo "   - API Gateway Console: https://console.aws.amazon.com/apigateway"
echo "   - Lambda Console: https://console.aws.amazon.com/lambda" 