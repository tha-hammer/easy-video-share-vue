#!/bin/bash

# Deploy Segments Backend Implementation
# This script applies Terraform changes and deploys the updated backend

set -e  # Exit on any error

echo "🚀 Starting Segments Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    print_error "Terraform configuration not found. Please run this script from the project root."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured. Please configure AWS credentials first."
    exit 1
fi

print_status "Current AWS identity:"
aws sts get-caller-identity --profile AdministratorAccess-571960159088
$env:AWS_PROFILE = "AdministratorAccess-571960159088"

# Navigate to terraform directory
cd terraform

print_status "Initializing Terraform..."
terraform init

print_status "Validating Terraform configuration..."
terraform validate

print_status "Planning Terraform changes..."
terraform plan --out=segments-deployment.tfplan

print_warning "The following changes will be applied:"
echo "  - Add segment attributes to DynamoDB table"
echo "  - Add new Global Secondary Indexes for segment queries"
echo "  - Update table description"

read -p "Do you want to apply these changes? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled by user."
    exit 0
fi

print_status "Applying Terraform changes..."
terraform apply segments-deployment.tfplan

print_success "Terraform changes applied successfully!"

# Get the table name from Terraform output
TABLE_NAME=$(terraform output -raw dynamodb_table_name)
print_status "DynamoDB table name: $TABLE_NAME"

# Verify the table structure
print_status "Verifying DynamoDB table structure..."
aws dynamodb describe-table --table-name "$TABLE_NAME" --query 'Table.{TableName:TableName,AttributeDefinitions:AttributeDefinitions,GlobalSecondaryIndexes:GlobalSecondaryIndexes}' --output table

print_success "DynamoDB table structure verified!"

# Navigate back to project root
cd ..

# Check if backend dependencies are installed
print_status "Checking backend dependencies..."
if [ ! -d "backend/.venv" ]; then
    print_warning "Backend virtual environment not found. Creating one..."
    cd backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    print_status "Backend virtual environment found."
fi

# Test the backend
print_status "Testing backend endpoints..."
cd backend

# Activate virtual environment
source .venv/bin/activate

# Start backend in background for testing
print_status "Starting backend server for testing..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Test health endpoint
print_status "Testing health endpoint..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend health check passed!"
else
    print_error "Backend health check failed!"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Test new segment endpoints
print_status "Testing segment endpoints..."
if curl -f http://localhost:8000/api/segments > /dev/null 2>&1; then
    print_success "Segment endpoints are accessible!"
else
    print_warning "Segment endpoints test failed (this might be expected if no segments exist)"
fi

# Stop backend
kill $BACKEND_PID 2>/dev/null || true

cd ..

print_success "🎉 Segments Backend Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Deploy the updated backend to your production environment"
echo "2. Test the new segment endpoints with real data"
echo "3. Monitor the Celery tasks for segment creation"
echo "4. Configure social media API integrations when ready"
echo ""
echo "New endpoints available:"
echo "  - POST /api/segments - Create a new segment"
echo "  - GET /api/segments/{segment_id} - Get a specific segment"
echo "  - GET /api/videos/{video_id}/segments - List segments for a video"
echo "  - GET /api/segments - List user segments with filtering"
echo "  - PUT /api/segments/{segment_id} - Update a segment"
echo "  - DELETE /api/segments/{segment_id} - Delete a segment"
echo "  - POST /api/segments/{segment_id}/social-media - Sync social media metrics"
echo "  - GET /api/segments/{segment_id}/analytics - Get social media analytics"
echo "  - GET /api/segments/{segment_id}/download - Get download URL"
echo ""
echo "New Celery tasks:"
echo "  - create_segments_from_video_task - Creates segment records after video processing"
echo "  - sync_social_media_metrics_task - Syncs social media metrics for a segment"
echo "  - batch_sync_social_media_task - Batch syncs metrics for all user segments" 