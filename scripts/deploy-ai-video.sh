#!/bin/bash

# AI Video Generation Feature Deployment Script
# This script deploys the AI video generation Lambda function and infrastructure

set -e

echo "🎬 Starting AI Video Generation Feature Deployment..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running in terraform directory
if [ ! -f "main.tf" ]; then
    echo -e "${RED}Error: This script must be run from the terraform directory${NC}"
    exit 1
fi

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AI video variables are configured
print_status "Checking AI video configuration..."
if [ -f "terraform.tfvars" ]; then
    if grep -q "google_cloud_credentials_json" terraform.tfvars && \
       grep -q "openai_api_key" terraform.tfvars; then
        print_success "AI video configuration found in terraform.tfvars"
    else
        print_warning "AI video variables not found in terraform.tfvars"
        print_warning "The infrastructure will be deployed but AI features will be disabled"
        print_warning "Add the following variables to enable AI video generation:"
        echo ""
        echo "google_cloud_credentials_json = \"...\""
        echo "openai_api_key = \"...\""
        echo "vertex_ai_project_id = \"...\""
        echo "vertex_ai_location = \"us-central1\""
        echo ""
    fi
else
    print_error "terraform.tfvars file not found!"
    print_error "Copy terraform.tfvars.example to terraform.tfvars and configure your values"
    exit 1
fi

# Create Lambda deployment package for AI video processor
print_status "Building AI video Lambda function..."

# Create temporary build directory
BUILD_DIR="./build-ai-video"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy Lambda function code
if [ -d "lambda-ai-video" ]; then
    cp -r lambda-ai-video/* $BUILD_DIR/
    print_success "Lambda function code copied"
else
    print_error "lambda-ai-video directory not found!"
    exit 1
fi

# Install dependencies
cd $BUILD_DIR
if [ -f "package.json" ]; then
    print_status "Installing Lambda dependencies..."
    npm install --production
    print_success "Dependencies installed"
else
    print_error "package.json not found in Lambda function directory"
    exit 1
fi

# Create deployment zip
print_status "Creating Lambda deployment package..."
zip -r ../ai_video_lambda.zip . -x "*.git*" "*.DS_Store*" "node_modules/.cache/*"
cd ..

print_success "Lambda deployment package created: ai_video_lambda.zip"

# Clean up build directory
rm -rf $BUILD_DIR

# Create Lambda Layer (placeholder - in production this would contain Google Cloud SDK)
print_status "Creating Lambda layer package..."
mkdir -p layer-build/nodejs
echo '{"name": "ai-video-layer", "version": "1.0.0"}' > layer-build/nodejs/package.json
cd layer-build
zip -r ../ai_video_layer.zip . 
cd ..
rm -rf layer-build
print_success "Lambda layer package created: ai_video_layer.zip"

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    print_status "Initializing Terraform..."
    terraform init
    print_success "Terraform initialized"
fi

# Plan the deployment
print_status "Planning Terraform deployment..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Do you want to apply these changes? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled by user"
    rm -f tfplan ai_video_lambda.zip ai_video_layer.zip
    exit 0
fi

# Apply the changes
print_status "Applying Terraform configuration..."
terraform apply tfplan

print_success "AI Video Generation infrastructure deployed successfully!"

# Clean up
rm -f tfplan

# Display deployment information
echo ""
echo "================================"
echo "🎬 AI VIDEO GENERATION DEPLOYED"
echo "================================"
echo ""

# Get API Gateway URL
API_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "Not available")
echo "API Gateway URL: $API_URL"

# Check if AI features are enabled
if terraform show | grep -q "ai_video_secrets"; then
    print_success "✅ AI Video Generation: ENABLED"
    echo "- Audio transcription: AWS Transcribe"
    echo "- Scene planning: OpenAI GPT-4"
    echo "- Video generation: Vertex AI Veo 2 (placeholder)"
else
    print_warning "⚠️  AI Video Generation: DISABLED"
    echo "Configure AI credentials in terraform.tfvars to enable"
fi

echo ""
echo "Next Steps:"
echo "1. Update your frontend environment variables:"
echo "   VITE_APP_API_URL=$API_URL"
echo "   VITE_AI_VIDEO_ENABLED=true"
echo ""
echo "2. Deploy your Vue.js frontend with the AI video components"
echo ""
echo "3. Test the AI video generation workflow"
echo ""

# Display resource cleanup command
echo "To clean up resources later, run:"
echo "  terraform destroy"
echo ""

print_success "Deployment complete! 🚀" 