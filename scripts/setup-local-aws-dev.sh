#!/bin/bash

# Local AWS Development Setup Script
# Configures local environment to work with real AWS services

set -e

echo "🛠️  Local AWS Development Setup"
echo "==============================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

AWS_REGION=$(aws configure get region || echo "us-east-1")
print_info "Using AWS region: $AWS_REGION"

# Check if infrastructure is deployed
cd terraform

if [ ! -f "terraform.tfstate" ]; then
    print_warning "No Terraform state found. Infrastructure may not be deployed."
    echo "Run the deployment script first: ./scripts/deploy-ai-video-infrastructure.sh"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get infrastructure details from Terraform outputs
print_info "Getting infrastructure details..."

BUCKET_NAME=""
AI_PROJECTS_TABLE=""
VIDEO_ASSETS_TABLE=""
SECRETS_NAME=""

if [ -f "terraform.tfstate" ]; then
    BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null || echo "")
    AI_PROJECTS_TABLE=$(terraform output -raw ai_projects_table_name 2>/dev/null || echo "")
    VIDEO_ASSETS_TABLE=$(terraform output -raw video_assets_table_name 2>/dev/null || echo "")
    SECRETS_NAME=$(terraform output -raw secrets_manager_secret_name 2>/dev/null || echo "")
fi

# Fallback values if Terraform outputs are not available
if [ -z "$BUCKET_NAME" ]; then
    print_warning "Could not get bucket name from Terraform outputs"
    read -p "Enter S3 bucket name: " BUCKET_NAME
fi

if [ -z "$AI_PROJECTS_TABLE" ]; then
    AI_PROJECTS_TABLE="easy-video-share-ai-projects-dev"
    print_warning "Using default AI projects table: $AI_PROJECTS_TABLE"
fi

if [ -z "$VIDEO_ASSETS_TABLE" ]; then
    VIDEO_ASSETS_TABLE="easy-video-share-video-assets-dev"
    print_warning "Using default video assets table: $VIDEO_ASSETS_TABLE"
fi

cd ..

# Navigate to video processor directory
cd terraform/video-processor

print_info "Setting up local development environment..."

# Create local AWS environment file
cat > .env.local.aws << EOF
# Local AWS Development Environment
# Real AWS services configuration for local development

# Environment
ENVIRONMENT=dev
PROJECT_NAME=easy-video-share
AWS_REGION=$AWS_REGION
USE_LOCALSTACK=false
LOG_LEVEL=DEBUG

# AWS Resources
S3_BUCKET=$BUCKET_NAME
AI_PROJECTS_TABLE=$AI_PROJECTS_TABLE
VIDEO_ASSETS_TABLE=$VIDEO_ASSETS_TABLE
SECRETS_NAME=${SECRETS_NAME:-easy-video-share-ai-api-keys-dev}

# API Configuration
HOST=127.0.0.1
PORT=8080

# Local development URL for testing
API_BASE_URL=http://localhost:8080

# API Keys (uncomment and add your keys)
# OPENAI_API_KEY=your-openai-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Note: AWS credentials will be used from your AWS CLI configuration
# Make sure you have run 'aws configure' and have appropriate permissions
EOF

print_status "Environment file created: .env.local.aws"

# Create a local requirements file if it doesn't exist
if [ ! -f "requirements.local.txt" ]; then
    cat > requirements.local.txt << 'EOF'
# Local development requirements for AI video processor
fastapi==0.104.1
uvicorn[standard]==0.24.0
boto3==1.34.0
requests==2.31.0
python-dotenv==1.0.0
pydantic==2.5.0
python-multipart==0.0.6

# Development tools
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
EOF
    print_status "Local requirements file created: requirements.local.txt"
fi

# Install dependencies
print_info "Installing Python dependencies..."
if command -v python3 &> /dev/null; then
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.local.txt
    print_status "Dependencies installed in virtual environment"
else
    print_warning "Python3 not found. Please install dependencies manually."
fi

# Test AWS connectivity
print_info "Testing AWS connectivity..."

# Test S3 access
if aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
    print_status "S3 bucket accessible: $BUCKET_NAME"
else
    print_error "Cannot access S3 bucket: $BUCKET_NAME"
    print_info "Make sure your AWS credentials have S3 access"
fi

# Test DynamoDB access
if aws dynamodb describe-table --table-name "$AI_PROJECTS_TABLE" --region "$AWS_REGION" &> /dev/null; then
    print_status "DynamoDB table accessible: $AI_PROJECTS_TABLE"
else
    print_warning "Cannot access DynamoDB table: $AI_PROJECTS_TABLE"
    print_info "Table may not exist yet or you may lack permissions"
fi

# Test Bedrock access (optional)
if aws bedrock list-foundation-models --region "$AWS_REGION" &> /dev/null 2>&1; then
    print_status "Bedrock service accessible"
else
    print_warning "Bedrock access limited - this is normal if you don't have Bedrock permissions"
fi

# Create run script
cat > run_local_aws.sh << 'EOF'
#!/bin/bash
# Run the AI video processor with real AWS services

# Load environment
if [ -f ".env.local.aws" ]; then
    export $(cat .env.local.aws | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting AI Video Processor (Local + AWS)"
echo "============================================="
echo "Environment: $ENVIRONMENT"
echo "AWS Region: $AWS_REGION"
echo "S3 Bucket: $S3_BUCKET"
echo "API URL: http://localhost:$PORT"
echo ""

# Start the application
if [ -f "app_production.py" ]; then
    python app_production.py
else
    python app.py
fi
EOF

chmod +x run_local_aws.sh
print_status "Run script created: run_local_aws.sh"

# Create test script
cat > test_local_aws.sh << 'EOF'
#!/bin/bash
# Test the local AWS integration

# Load environment
if [ -f ".env.local.aws" ]; then
    export $(cat .env.local.aws | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🧪 Testing Local AWS Integration"
echo "================================"

# Run the test script
python test_real_aws.py
EOF

chmod +x test_local_aws.sh
print_status "Test script created: test_local_aws.sh"

# Go back to project root
cd ../..

echo ""
print_status "Local AWS development setup complete!"
echo ""
echo "🚀 Next Steps:"
echo "  1. Add your API keys to terraform/video-processor/.env.local.aws"
echo "  2. Start the local server:"
echo "     cd terraform/video-processor"
echo "     ./run_local_aws.sh"
echo ""
echo "  3. In another terminal, test the integration:"
echo "     cd terraform/video-processor"
echo "     ./test_local_aws.sh"
echo ""
echo "📝 Configuration Files Created:"
echo "  - terraform/video-processor/.env.local.aws (environment variables)"
echo "  - terraform/video-processor/requirements.local.txt (Python dependencies)"
echo "  - terraform/video-processor/run_local_aws.sh (start script)"
echo "  - terraform/video-processor/test_local_aws.sh (test script)"
echo ""
echo "🔑 Don't forget to:"
echo "  - Add your OpenAI API key to .env.local.aws"
echo "  - Ensure your AWS credentials have appropriate permissions"
echo "  - Test the Bedrock Nova Reel integration when ready"
echo ""
print_status "Happy coding! 🎬" 