#!/bin/bash

# Create Lambda Deployment Package Script
# This script creates the production-lambda.zip file for the video processor Lambda

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Creating Lambda Deployment Package ===${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "terraform/lambda/video-processor/lambda_function.py" ]; then
    print_error "This script must be run from the project root directory"
    print_error "Current directory: $(pwd)"
    print_error "Expected file: terraform/lambda/video-processor/lambda_function.py"
    exit 1
fi

# Navigate to lambda directory
cd terraform/lambda/video-processor/

print_status "Creating Lambda deployment package..."

# Remove old package if it exists
if [ -f production-lambda.zip ]; then
    print_warning "Removing existing production-lambda.zip"
    rm production-lambda.zip
fi

# Create the package
print_status "Zipping Lambda function and dependencies..."

# Include all Python files and dependencies
zip -r production-lambda.zip \
    lambda_function.py \
    utils/ \
    boto3/ \
    boto3-*.dist-info/ \
    botocore/ \
    botocore-*.dist-info/ \
    dateutil/ \
    python_dateutil-*.dist-info/ \
    jmespath/ \
    jmespath-*.dist-info/ \
    redis/ \
    redis-*.dist-info/ \
    s3transfer/ \
    s3transfer-*.dist-info/ \
    six-*.dist-info/ \
    urllib3/ \
    urllib3-*.dist-info/ \
    -x '*.pyc' '__pycache__/*' '*.git*' '*.DS_Store' 2>/dev/null || {
    
    print_warning "Some dependencies not found, creating basic package..."
    
    # Create minimal package with just the Lambda function
    zip production-lambda.zip lambda_function.py || {
        print_error "Failed to create basic package"
        exit 1
    }
}

# Check if package was created successfully
if [ -f production-lambda.zip ]; then
    PACKAGE_SIZE=$(ls -lh production-lambda.zip | awk '{print $5}')
    print_status "Package created successfully: production-lambda.zip (${PACKAGE_SIZE})"
    
    # Verify package contents
    print_status "Package contents:"
    unzip -l production-lambda.zip | head -20
    
    echo ""
    print_status "✅ Lambda deployment package ready!"
    print_status "Run './scripts/deploy-enhanced-lambda.sh' to deploy"
else
    print_error "❌ Failed to create deployment package"
    exit 1
fi 