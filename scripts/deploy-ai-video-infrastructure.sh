#!/bin/bash

# AI Video Infrastructure Deployment Script
# Deploys complete infrastructure for Bedrock Nova Reel video generation

set -e  # Exit on any error

echo "🎬 AI Video Infrastructure Deployment"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed or not in PATH"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed or not in PATH"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

print_status "Prerequisites check passed"

# Get current AWS account and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

print_info "AWS Account ID: $AWS_ACCOUNT_ID"
print_info "AWS Region: $AWS_REGION"

# Check if terraform.tfvars exists
if [ ! -f "terraform/terraform.tfvars" ]; then
    print_warning "terraform.tfvars not found. Creating from example..."
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars
    
    # Update with environment-specific values
    sed -i.bak "s/your-unique-bucket-name/easy-video-share-ai-$(date +%s)/" terraform/terraform.tfvars
    sed -i.bak "s/enable_ai_video_pipeline = false/enable_ai_video_pipeline = true/" terraform/terraform.tfvars
    
    echo ""
    print_warning "IMPORTANT: Edit terraform/terraform.tfvars to configure:"
    echo "  - bucket_name (must be globally unique)"
    echo "  - openai_api_key (for scene generation)"
    echo "  - Any other API keys you want to use"
    echo ""
    read -p "Press Enter when you've updated terraform.tfvars..."
fi

# Navigate to terraform directory
cd terraform

echo ""
echo "🏗️  Phase 1: Deploying Core Infrastructure..."

# Initialize terraform
echo "Initializing Terraform..."
terraform init

# Plan deployment
echo "Creating deployment plan..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Deploy the AI video infrastructure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Apply deployment
echo "Deploying infrastructure..."
terraform apply tfplan

# Get outputs
echo ""
echo "📋 Infrastructure Details:"
echo "========================="

# Core infrastructure
BUCKET_NAME=$(terraform output -raw bucket_name)
ECR_REPO_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")

echo "S3 Bucket: $BUCKET_NAME"
echo "ECR Repository: $ECR_REPO_URL"
echo "ECS Cluster: $ECS_CLUSTER_NAME"

# AI-specific infrastructure
if [ ! -z "$ECR_REPO_URL" ]; then
    AI_PROJECTS_TABLE=$(terraform output -raw ai_projects_table_name 2>/dev/null || echo "")
    VIDEO_ASSETS_TABLE=$(terraform output -raw video_assets_table_name 2>/dev/null || echo "")
    SECRETS_NAME=$(terraform output -raw secrets_manager_secret_name 2>/dev/null || echo "")
    
    echo "AI Projects Table: $AI_PROJECTS_TABLE"
    echo "Video Assets Table: $VIDEO_ASSETS_TABLE"
    echo "Secrets Manager: $SECRETS_NAME"
fi

# Go back to root directory
cd ..

echo ""
echo "🐳 Phase 2: Building and Deploying Video Processor..."

if [ ! -z "$ECR_REPO_URL" ]; then
    # Login to ECR
    print_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL
    
    # Navigate to video processor directory
    cd terraform/video-processor
    
    # Create production Dockerfile
    print_info "Creating production Dockerfile..."
    cat > Dockerfile.production << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app_production.py app.py
COPY services/ ./services/

# Create necessary directories
RUN mkdir -p /tmp/processing

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
EOF

    # Build Docker image
    print_info "Building Docker image..."
    docker build -f Dockerfile.production -t video-processor:latest .
    
    # Tag for ECR
    docker tag video-processor:latest $ECR_REPO_URL:latest
    docker tag video-processor:latest $ECR_REPO_URL:v$(date +%Y%m%d-%H%M%S)
    
    # Push to ECR
    print_info "Pushing to ECR..."
    docker push $ECR_REPO_URL:latest
    docker push $ECR_REPO_URL:v$(date +%Y%m%d-%H%M%S)
    
    print_status "Docker image pushed to ECR"
    
    # Go back to root
    cd ../..
    
    echo ""
    echo "🔄 Phase 3: Updating ECS Service..."
    
    # Update ECS service to use new image
    print_info "Updating ECS service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER_NAME \
        --service easy-video-share-video-processor-dev \
        --force-new-deployment \
        --region $AWS_REGION
    
    print_status "ECS service update initiated"
    
else
    print_warning "AI video pipeline not enabled or ECR repository not found"
fi

echo ""
echo "🧪 Phase 4: Running Infrastructure Tests..."

# Test S3 bucket
print_info "Testing S3 bucket..."
aws s3 ls "s3://$BUCKET_NAME" &> /dev/null && print_status "S3 bucket accessible" || print_error "S3 bucket not accessible"

# Test DynamoDB tables if they exist
if [ ! -z "$AI_PROJECTS_TABLE" ]; then
    print_info "Testing DynamoDB tables..."
    aws dynamodb describe-table --table-name $AI_PROJECTS_TABLE --region $AWS_REGION &> /dev/null && print_status "AI Projects table exists" || print_error "AI Projects table not found"
    aws dynamodb describe-table --table-name $VIDEO_ASSETS_TABLE --region $AWS_REGION &> /dev/null && print_status "Video Assets table exists" || print_error "Video Assets table not found"
fi

# Test ECS cluster
if [ ! -z "$ECS_CLUSTER_NAME" ]; then
    print_info "Testing ECS cluster..."
    aws ecs describe-clusters --clusters $ECS_CLUSTER_NAME --region $AWS_REGION &> /dev/null && print_status "ECS cluster exists" || print_error "ECS cluster not found"
fi

echo ""
echo "📝 Creating Environment Configuration..."

# Create environment file for local testing
cat > terraform/video-processor/env.aws << EOF
# Production AWS Environment Configuration
# Generated by deployment script on $(date)

# Environment
ENVIRONMENT=dev
PROJECT_NAME=easy-video-share
AWS_REGION=$AWS_REGION
USE_LOCALSTACK=false
LOG_LEVEL=INFO

# AWS Resources
S3_BUCKET=$BUCKET_NAME
AI_PROJECTS_TABLE=$AI_PROJECTS_TABLE
VIDEO_ASSETS_TABLE=$VIDEO_ASSETS_TABLE
SECRETS_NAME=$SECRETS_NAME

# API Configuration
HOST=0.0.0.0
PORT=8080

# Add your API keys here:
# OPENAI_API_KEY=your-openai-api-key-here
EOF

print_status "Environment configuration created (terraform/video-processor/env.aws)"

echo ""
echo "🎉 Deployment Complete!"
echo "======================"

# Display summary
echo ""
echo "📊 Infrastructure Summary:"
echo "  ✅ S3 Bucket: $BUCKET_NAME"
echo "  ✅ ECR Repository: ${ECR_REPO_URL:-'Not deployed'}"
echo "  ✅ ECS Cluster: ${ECS_CLUSTER_NAME:-'Not deployed'}"
echo "  ✅ DynamoDB Tables: ${AI_PROJECTS_TABLE:-'Not deployed'}"

echo ""
echo "🚀 Next Steps:"
echo "  1. Update API keys in Secrets Manager:"
echo "     aws secretsmanager update-secret --secret-id $SECRETS_NAME --secret-string '{\"openai_api_key\":\"your-key-here\"}'"
echo ""
echo "  2. Test the API locally:"
echo "     cd terraform/video-processor"
echo "     python test_real_aws.py"
echo ""
echo "  3. Monitor ECS service deployment:"
echo "     aws ecs describe-services --cluster $ECS_CLUSTER_NAME --services easy-video-share-video-processor-dev"
echo ""
echo "  4. Check logs:"
echo "     aws logs tail /ecs/easy-video-share-video-processor-dev --follow"

echo ""
echo "🔗 Useful URLs:"
echo "  - AWS Console: https://$AWS_REGION.console.aws.amazon.com/"
echo "  - ECS Console: https://$AWS_REGION.console.aws.amazon.com/ecs/home"
echo "  - S3 Console: https://s3.console.aws.amazon.com/s3/buckets/$BUCKET_NAME"

echo ""
print_status "AI Video Infrastructure deployment completed successfully!"

# Save deployment info
cat > deployment-info.json << EOF
{
  "deployment_date": "$(date -Iseconds)",
  "aws_account_id": "$AWS_ACCOUNT_ID",
  "aws_region": "$AWS_REGION",
  "s3_bucket": "$BUCKET_NAME",
  "ecr_repository": "$ECR_REPO_URL",
  "ecs_cluster": "$ECS_CLUSTER_NAME",
  "ai_projects_table": "$AI_PROJECTS_TABLE",
  "video_assets_table": "$VIDEO_ASSETS_TABLE",
  "secrets_name": "$SECRETS_NAME"
}
EOF

print_status "Deployment information saved to deployment-info.json" 