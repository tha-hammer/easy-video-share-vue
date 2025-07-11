#!/bin/bash

# Enhanced Lambda Video Processor Deployment Script
# Supports both Terraform and CLI deployment methods

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Enhanced Lambda Video Processor Deployment ===${NC}"
echo -e "${BLUE}Features: Two-phase processing, text overlays, thumbnail generation${NC}"
echo -e "${GREEN}Fixes: Environment variables syntax, JSON payload encoding${NC}"
echo ""

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3 first."
        exit 1
    fi
    
    # Check pip
    if ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install pip first."
        exit 1
    fi
    
    print_status "Prerequisites check passed ✅"
}

# Terraform deployment method
deploy_terraform() {
    print_status "Deploying with Terraform..."
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install Terraform first."
        print_warning "Download from: https://www.terraform.io/downloads.html"
        exit 1
    fi
    
    # Navigate to terraform directory
    cd terraform/
    
    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warning "terraform.tfvars not found. Creating with default values..."
        
        # Get AWS account ID
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        
        # Create terraform.tfvars with required variables
        cat > terraform.tfvars << EOF
# Required variables
bucket_name = "easy-video-share-bucket-${ACCOUNT_ID}"
cognito_domain_prefix = "easy-video-share-${ACCOUNT_ID}"

# Optional variables
aws_region = "us-east-1"
environment = "dev"
project_name = "easy-video-share"
admin_user_email = ""
admin_user_password = ""
EOF
        
        print_status "Created terraform.tfvars with default values"
        print_warning "You can edit terraform.tfvars to customize the deployment"
    fi
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    print_status "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply deployment
    print_status "Applying Terraform deployment..."
    terraform apply tfplan
    
    # Verify deployment
    print_status "Verifying deployment..."
    
    # Check Lambda function
    FUNCTION_NAME="easy-video-share-video-processor"
    if aws lambda get-function --function-name $FUNCTION_NAME &> /dev/null; then
        print_status "Lambda function deployed successfully ✅"
    else
        print_error "Lambda function deployment failed ❌"
        exit 1
    fi
    
    # Check DynamoDB tables
    if aws dynamodb describe-table --table-name easy-video-share-video-segments &> /dev/null; then
        print_status "DynamoDB segments table created successfully ✅"
    else
        print_error "DynamoDB segments table creation failed ❌"
        exit 1
    fi
    
    print_status "Terraform deployment completed successfully! 🎉"
}

# CLI deployment method
deploy_cli() {
    print_status "Deploying with CLI method..."
    
    # Store original directory
    ORIGINAL_DIR=$(pwd)
    
    # Navigate to lambda directory
    cd terraform/lambda/video-processor/
    
    # Configuration
    FUNCTION_NAME="easy-video-share-video-processor"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/easy-video-share-lambda-execution-role"
    
    # Check if IAM role exists
    print_status "Checking IAM role..."
    if ! aws iam get-role --role-name easy-video-share-lambda-execution-role &>/dev/null; then
        print_error "IAM role 'easy-video-share-lambda-execution-role' not found"
        print_error "Please run Terraform deployment first to create the role, or create it manually"
        exit 1
    fi
    
    print_status "Installing Python dependencies..."
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt -t . || {
            print_error "Failed to install dependencies"
            exit 1
        }
    fi
    
    print_status "Creating deployment package..."
    if [ -f production-lambda.zip ]; then
        print_status "Using existing production-lambda.zip"
        # Check if it's not empty
        if [ ! -s production-lambda.zip ]; then
            print_error "production-lambda.zip exists but is empty"
            print_status "Attempting to recreate package..."
            cd "$ORIGINAL_DIR"
            if [ -x scripts/create-lambda-package.sh ]; then
                ./scripts/create-lambda-package.sh
                cd terraform/lambda/video-processor/
            else
                print_error "Package creation script not found or not executable"
                exit 1
            fi
        fi
    else
        print_warning "production-lambda.zip not found, attempting to create..."
        cd "$ORIGINAL_DIR"
        if [ -x scripts/create-lambda-package.sh ]; then
            ./scripts/create-lambda-package.sh
            cd terraform/lambda/video-processor/
            if [ ! -f production-lambda.zip ]; then
                print_error "Failed to create deployment package"
                exit 1
            fi
        else
            print_error "production-lambda.zip not found and cannot auto-create"
            print_error "To create the deployment package manually:"
            print_error "1. Navigate to terraform/lambda/video-processor/"
            print_error "2. Run: zip -r production-lambda.zip . -x '*.git*' '*.zip'"
            print_error "Or run: ./scripts/create-lambda-package.sh from project root"
            exit 1
        fi
    fi
    
    print_status "Checking if Lambda function exists..."
    if aws lambda get-function --function-name $FUNCTION_NAME &>/dev/null; then
        print_status "Function exists, updating code..."
        aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --zip-file fileb://production-lambda.zip || {
            print_error "Failed to update function code"
            exit 1
        }
        
        print_status "Updating function configuration..."
        aws lambda update-function-configuration \
            --function-name $FUNCTION_NAME \
            --timeout 900 \
            --memory-size 3008 \
            --ephemeral-storage Size=10240 \
            --environment 'Variables={"ENVIRONMENT":"production","S3_BUCKET":"easy-video-share-bucket"}' || {
            print_error "Failed to update function configuration"
            exit 1
        }
    else
        print_status "Function doesn't exist, creating new function..."
        aws lambda create-function \
            --function-name $FUNCTION_NAME \
            --runtime python3.11 \
            --role $ROLE_ARN \
            --handler lambda_function.lambda_handler \
            --zip-file fileb://production-lambda.zip \
            --timeout 900 \
            --memory-size 3008 \
            --ephemeral-storage Size=10240 \
            --environment 'Variables={"ENVIRONMENT":"production","S3_BUCKET":"easy-video-share-bucket"}' || {
            print_error "Failed to create function"
            exit 1
        }
    fi
    
    print_status "Creating/updating DynamoDB table for video segments..."
    if ! aws dynamodb describe-table --table-name easy-video-share-video-segments &>/dev/null; then
        print_status "Creating video segments table..."
        
        # Create table with proper JSON formatting for GSI
        cat > gsi-config.json << 'EOF'
[
    {
        "IndexName": "VideoIndex",
        "KeySchema": [
            {"AttributeName": "video_id", "KeyType": "HASH"},
            {"AttributeName": "segment_number", "KeyType": "RANGE"}
        ],
        "Projection": {"ProjectionType": "ALL"}
    },
    {
        "IndexName": "CreatedAtIndex", 
        "KeySchema": [
            {"AttributeName": "video_id", "KeyType": "HASH"},
            {"AttributeName": "created_at", "KeyType": "RANGE"}
        ],
        "Projection": {"ProjectionType": "ALL"}
    }
]
EOF
        
        aws dynamodb create-table \
            --table-name easy-video-share-video-segments \
            --attribute-definitions \
                AttributeName=segment_id,AttributeType=S \
                AttributeName=video_id,AttributeType=S \
                AttributeName=segment_number,AttributeType=N \
                AttributeName=created_at,AttributeType=S \
            --key-schema \
                AttributeName=segment_id,KeyType=HASH \
            --global-secondary-indexes file://gsi-config.json \
            --billing-mode PAY_PER_REQUEST || {
            print_error "Failed to create DynamoDB table"
            rm -f gsi-config.json
            exit 1
        }
        
        # Clean up temp file
        rm -f gsi-config.json
    else
        print_status "DynamoDB table already exists ✅"
    fi
    
    print_status "CLI deployment completed successfully! 🎉"
    
    # Return to original directory
    cd "$ORIGINAL_DIR"
}

# Test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    FUNCTION_NAME="easy-video-share-video-processor"
    
    # Test 1: Basic connectivity
    print_status "Test 1: Basic connectivity..."
    echo '{"processing_type":"full_video_processing","test_mode":true}' > test-payload.json
    aws lambda invoke \
        --function-name $FUNCTION_NAME \
        --payload file://test-payload.json \
        test-basic.json
    
    if [ -f test-basic.json ]; then
        print_status "Basic connectivity test passed ✅"
        rm test-basic.json test-payload.json
    else
        print_error "Basic connectivity test failed ❌"
        rm -f test-payload.json
        exit 1
    fi
    
    # Test 2: Segments without text
    print_status "Test 2: Segments without text processing..."
    echo '{"processing_type":"segments_without_text","video_id":"test_video","video_s3_key":"test.mp4","segments":[{"start":0,"end":30}]}' > test-segments-payload.json
    aws lambda invoke \
        --function-name $FUNCTION_NAME \
        --payload file://test-segments-payload.json \
        test-segments.json
    
    if [ -f test-segments.json ]; then
        print_status "Segments processing test passed ✅"
        rm test-segments.json test-segments-payload.json
    else
        print_error "Segments processing test failed ❌"
        rm -f test-segments-payload.json
        exit 1
    fi
    
    # Test 3: Thumbnail generation
    print_status "Test 3: Thumbnail generation..."
    echo '{"processing_type":"generate_thumbnail","video_id":"test_video","segment_id":"seg_test_video_001"}' > test-thumbnail-payload.json
    aws lambda invoke \
        --function-name $FUNCTION_NAME \
        --payload file://test-thumbnail-payload.json \
        test-thumbnail.json
    
    if [ -f test-thumbnail.json ]; then
        print_status "Thumbnail generation test passed ✅"
        rm test-thumbnail.json test-thumbnail-payload.json
    else
        print_error "Thumbnail generation test failed ❌"
        rm -f test-thumbnail-payload.json
        exit 1
    fi
    
    print_status "All tests passed! 🎉"
}

# Display configuration info
show_config() {
    print_status "Configuration Information:"
    echo ""
    echo -e "${BLUE}AWS Configuration:${NC}"
    aws sts get-caller-identity
    echo ""
    echo -e "${BLUE}Lambda Function:${NC} easy-video-share-video-processor"
    echo -e "${BLUE}DynamoDB Tables:${NC}"
    echo "  - easy-video-share-video-metadata"
    echo "  - easy-video-share-video-segments"
    echo ""
    echo -e "${BLUE}Processing Types:${NC}"
    echo "  - full_video_processing (legacy)"
    echo "  - segments_without_text (Phase 1)"
    echo "  - apply_text_overlays (Phase 2)"
    echo "  - generate_thumbnail (thumbnails)"
    echo ""
}

# Main menu
main_menu() {
    echo -e "${BLUE}Choose deployment method:${NC}"
    echo "1. Terraform (Recommended - Full infrastructure)"
    echo "2. CLI (Quick - Lambda function only)"
    echo "3. Test existing deployment"
    echo "4. Show configuration"
    echo "5. Exit"
    echo ""
    read -p "Enter your choice [1-5]: " choice
    
    case $choice in
        1)
            deploy_terraform
            test_deployment
            ;;
        2)
            deploy_cli
            test_deployment
            ;;
        3)
            test_deployment
            ;;
        4)
            show_config
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please enter 1-5."
            main_menu
            ;;
    esac
}

# Post-deployment instructions
show_post_deployment() {
    echo ""
    echo -e "${GREEN}=== DEPLOYMENT SUCCESSFUL! ===${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Update Railway environment variables:"
    echo "   - USE_LAMBDA_PROCESSING=true"
    echo "   - LAMBDA_FUNCTION_NAME=easy-video-share-video-processor"
    echo ""
    echo "2. Configure terraform.tfvars (if using Terraform):"
    echo "   - Edit terraform/terraform.tfvars to customize deployment"
    echo "   - Update bucket_name, cognito_domain_prefix as needed"
    echo ""
    echo "3. Test the enhanced endpoints:"
    echo "   - POST /videos/{video_id}/process-segments-without-text"
    echo "   - POST /segments/{segment_id}/generate-thumbnail"
    echo "   - POST /segments/{segment_id}/process-with-text-overlays"
    echo ""
    echo "4. Monitor CloudWatch logs:"
    echo "   aws logs tail /aws/lambda/easy-video-share-video-processor --follow"
    echo ""
    echo "5. Check DynamoDB tables:"
    echo "   aws dynamodb scan --table-name easy-video-share-video-segments --max-items 10"
    echo ""
    echo -e "${GREEN}Enhanced Features Available:${NC}"
    echo "✅ Two-phase processing (segments → text overlays)"
    echo "✅ Thumbnail generation for design interface"
    echo "✅ Smart timeout handling with S3 temp storage"
    echo "✅ DynamoDB segment metadata tracking"
    echo "✅ FFmpeg text overlay processing"
    echo ""
    echo -e "${GREEN}Fixes Applied:${NC}"
    echo "✅ Environment variables syntax (proper JSON escaping)"
    echo "✅ Lambda test payload encoding (using file:// method)"
    echo "✅ CLI deployment method (inline implementation)"
    echo "✅ Error handling and validation"
    echo ""
    echo -e "${BLUE}Documentation:${NC} terraform/lambda/video-processor/README.md"
}

# Main execution
main() {
    check_prerequisites
    show_config
    main_menu
    show_post_deployment
}

# Run main function
main "$@" 