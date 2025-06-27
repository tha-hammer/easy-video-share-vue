#!/bin/bash

# Easy Video Share - Deploy and Test Script
# This script deploys the infrastructure and runs basic echo ""
echo "🔧 Next Steps for Frontend Setup:"
echo "================================="
echo "1. Update your .env file with the following values:"
echo ""
echo "VITE_AWS_REGION=$AWS_REGION"
echo "VITE_AWS_BUCKET_NAME=$BUCKET_NAME"
if [ "$COGNITO_USER_POOL_ID" != "Not available" ]; then
    echo "VITE_COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID"
fi
if [ "$COGNITO_CLIENT_ID" != "Not available" ]; then
    echo "VITE_COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID"
fi
if [ "$API_GATEWAY_URL" != "Not available" ]; then
    echo "VITE_API_ENDPOINT=$API_GATEWAY_URL"
fi
if [ "$API_UPLOAD_URL_ENDPOINT" != "Not available" ]; then
    echo "VITE_VIDEO_UPLOAD_URL_ENDPOINT=$API_UPLOAD_URL_ENDPOINT"
fi
echo ""
echo "2. Run 'npm install' to install dependencies"
echo "3. Run 'npm run dev' to start the development server"
echo "4. Register a new account using Cognito authentication"
echo "5. Test video upload functionality with presigned URLs"t on any error

echo "🚀 Easy Video Share - Infrastructure Deployment & Testing"
echo "========================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed or not in PATH"
    exit 1
fi

print_status "Prerequisites check passed"

# Check if terraform.tfvars exists
if [ ! -f "terraform/terraform.tfvars" ]; then
    print_warning "terraform.tfvars not found. Creating from example..."
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars
    echo ""
    print_warning "IMPORTANT: Edit terraform/terraform.tfvars with your unique bucket name before continuing!"
    echo "Example: bucket_name = \"easy-video-share-yourname-dev\""
    echo ""
    read -p "Press Enter when you've updated terraform.tfvars..."
fi

# Navigate to terraform directory
cd terraform

echo ""
echo "🏗️  Deploying infrastructure..."

# Initialize terraform
echo "Initializing Terraform..."
terraform init

# Plan deployment
echo "Creating deployment plan..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Deploy the infrastructure? (y/N): " -n 1 -r
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
BUCKET_NAME=$(terraform output -raw bucket_name)
WEBSITE_ENDPOINT=$(terraform output -raw bucket_website_endpoint)
API_GATEWAY_URL=$(terraform output -raw api_gateway_endpoint 2>/dev/null || echo "Not available")
API_VIDEOS_ENDPOINT=$(terraform output -raw api_videos_endpoint 2>/dev/null || echo "Not available")
API_UPLOAD_URL_ENDPOINT=$(terraform output -raw api_videos_upload_url_endpoint 2>/dev/null || echo "Not available")
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id 2>/dev/null || echo "Not available")
COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id 2>/dev/null || echo "Not available")
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-1")

echo "Bucket Name: $BUCKET_NAME"
echo "Website Endpoint: http://$WEBSITE_ENDPOINT"
echo "API Gateway URL: $API_GATEWAY_URL"
echo "Videos API Endpoint: $API_VIDEOS_ENDPOINT"
echo "Upload URL Endpoint: $API_UPLOAD_URL_ENDPOINT"
echo "Cognito User Pool ID: $COGNITO_USER_POOL_ID"
echo "Cognito Client ID: $COGNITO_CLIENT_ID"
echo "AWS Region: $AWS_REGION"

echo ""
print_status "✅ Infrastructure deployed successfully!"

echo ""
echo "� Next Steps for Frontend Setup:"
echo "================================="
echo "1. Update your .env file with the following values:"
echo ""
echo "VITE_AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || echo "us-east-1")"
echo "VITE_AWS_BUCKET_NAME=$BUCKET_NAME"
if [ "$COGNITO_USER_POOL_ID" != "Not available" ]; then
    echo "VITE_COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID"
fi
if [ "$COGNITO_CLIENT_ID" != "Not available" ]; then
    echo "VITE_COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID"
fi
if [ "$API_GATEWAY_URL" != "Not available" ]; then
    echo "VITE_API_ENDPOINT=$API_GATEWAY_URL"
fi
echo ""
echo "2. Run 'npm run dev' to start the development server"
echo "3. Register a new account or log in with existing credentials"
echo "4. Test video upload functionality"

# Run basic tests
echo ""
echo "🧪 Running basic infrastructure tests..."

# Test 1: Website endpoint accessibility
echo "Testing website endpoint..."
if curl -f -s -I "http://$WEBSITE_ENDPOINT" > /dev/null 2>&1; then
    print_status "Website endpoint is accessible"
else
    print_warning "Website endpoint may not be ready yet (normal for first deployment)"
fi

# Test 2: API Gateway connectivity (if available)
if [ "$API_GATEWAY_URL" != "Not available" ]; then
    echo "Testing API Gateway connectivity..."
    if curl -f -s "$API_GATEWAY_URL/health" > /dev/null 2>&1; then
        print_status "API Gateway connectivity test passed"
    else
        print_warning "API Gateway may not be ready yet (normal for first deployment)"
    fi
fi

# Test 5: Create deployment confirmation page
cat > deployment-success.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Easy Video Share - Deployment Success</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            max-width: 600px;
            margin: 0 auto;
        }
        .success { color: #4ade80; font-size: 1.2em; }
        .info { background: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 5px; margin: 20px 0; }
        .next-steps { text-align: left; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Easy Video Share</h1>
        <p class="success">✅ Infrastructure deployed successfully!</p>
        <div class="info">
            <h3>Authentication: AWS Cognito</h3>
            <p>Secure user registration and login</p>
        </div>
        <div class="info">
            <h3>File Uploads: Presigned URLs</h3>
            <p>Direct-to-S3 uploads without exposing credentials</p>
        </div>
        <div class="info next-steps">
            <h3>Next Steps:</h3>
            <ol>
                <li>Configure your frontend .env file</li>
                <li>Run 'npm install && npm run dev'</li>
                <li>Register a new account</li>
                <li>Upload and share videos securely!</li>
            </ol>
        </div>
    </div>
</body>
</html>
EOF

print_status "Deployment confirmation page prepared"

# Clean up
rm deployment-success.html

# Final output
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "Website URL: http://$WEBSITE_ENDPOINT"
echo "Bucket: $BUCKET_NAME"
if [ "$API_GATEWAY_URL" != "Not available" ]; then
    echo "API Gateway: $API_GATEWAY_URL"
fi
if [ "$COGNITO_USER_POOL_ID" != "Not available" ]; then
    echo "Cognito User Pool: $COGNITO_USER_POOL_ID"
fi
echo ""
echo "🚀 Ready for Vue.js Development!"
echo ""
echo "Authentication Model: AWS Cognito (no access keys needed)"
echo "Upload Method: Presigned URLs (secure, direct-to-S3)"
echo ""
echo "Next steps:"
echo "1. Visit your website URL: http://$WEBSITE_ENDPOINT"
echo "2. Update your frontend .env file with the configuration shown above"
echo "3. Run 'npm install && npm run dev' to start your Vue.js development server"
echo "4. Test user registration with Cognito authentication"
echo "5. Test secure video upload with presigned URLs"
echo "6. Check terraform/TESTING.md for comprehensive validation"

# Go back to root directory
cd ..

echo ""
echo "✨ Ready to build something awesome!"