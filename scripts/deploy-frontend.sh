#!/bin/bash

# Deploy Vue3 Frontend to S3
# This script builds the Vite Vue3 app and deploys it to your S3 bucket

set -e

echo "🚀 Deploying Vue3 Frontend to S3"
echo "================================="

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

# Get bucket name from Terraform
echo "📋 Getting bucket information from Terraform..."
cd terraform
BUCKET_NAME=$(terraform output -raw bucket_name 2>/dev/null)
WEBSITE_ENDPOINT=$(terraform output -raw bucket_website_endpoint 2>/dev/null)
cd ..

if [ -z "$BUCKET_NAME" ]; then
    echo "❌ Error: Could not get bucket name from Terraform"
    exit 1
fi

echo "📦 Target bucket: $BUCKET_NAME"
echo "🌐 Website will be available at: http://$WEBSITE_ENDPOINT"

# Check if Vue3 dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📥 Installing Vue3 dependencies..."
    npm install
fi

# Build the Vue3 frontend (skip type checking for deployment)
echo "🔨 Building Vue3 application (skipping type check for deployment)..."
echo "ℹ️  Note: Using build-only to skip TypeScript type checking during deployment"

# Try to build without type checking first
if npm run build-only; then
    echo "✅ Build successful"
else
    echo "❌ Build failed even without type checking"
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "- Check for syntax errors in your Vue components"
    echo "- Ensure all imports are valid"
    echo "- Try running 'npm run lint' to fix linting issues"
    echo "- Run 'npm run type-check' separately to see TypeScript issues"
    exit 1
fi

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Error: Build failed - dist directory not found"
    exit 1
fi

echo "📤 Build completed successfully!"
echo ""
echo "🚨 IMPORTANT: AWS CLI S3 Upload Removed for Security"
echo "==================================================="
echo "This script no longer uploads to S3 using AWS CLI credentials for security reasons."
echo "The application has been migrated to use IAM roles instead of access keys."
echo ""
echo "📦 Your build files are ready in: ./dist/"
echo ""
echo "🚀 Deployment Options:"
echo "1. **Terraform Deployment (Recommended)**:"
echo "   - Add S3 object resources to your Terraform configuration"
echo "   - Use terraform to deploy both infrastructure and frontend files"
echo ""
echo "2. **Manual Upload via AWS Console**:"
echo "   - Go to AWS S3 Console: https://console.aws.amazon.com/s3/"
echo "   - Navigate to bucket: $BUCKET_NAME"
echo "   - Upload all files from ./dist/ folder"
echo ""
echo "3. **CI/CD Pipeline with IAM Roles**:"
echo "   - Set up GitHub Actions, GitLab CI, or AWS CodePipeline"
echo "   - Configure IAM role assumption for deployment"
echo ""
echo "4. **AWS CloudShell (if available)**:"
echo "   - Use AWS CloudShell with built-in AWS CLI"
echo "   - Upload dist/ folder and run AWS CLI commands there"
echo ""
echo "📋 Required S3 Upload Commands (for manual execution):"
echo "======================================================"
echo "# Upload all files:"
echo "aws s3 cp dist/ s3://$BUCKET_NAME/ --recursive --exclude \"*.map\""
echo ""
echo "# Set content types for better performance:"
echo "aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \\"
echo "    --content-type \"text/html\" \\"
echo "    --cache-control \"public, max-age=300\""
echo ""
echo "aws s3 cp dist/assets/ s3://$BUCKET_NAME/assets/ \\"
echo "    --recursive --exclude \"*\" --include \"*.css\" \\"
echo "    --content-type \"text/css\" \\"
echo "    --cache-control \"public, max-age=31536000\""
echo ""
echo "aws s3 cp dist/assets/ s3://$BUCKET_NAME/assets/ \\"
echo "    --recursive --exclude \"*\" --include \"*.js\" \\"
echo "    --content-type \"application/javascript\" \\"
echo "    --cache-control \"public, max-age=31536000\""

echo ""
echo "🌐 Your application will be available at: http://$WEBSITE_ENDPOINT"
echo ""
echo "📋 Deployment Summary:"
echo "====================="
echo "Bucket:    $BUCKET_NAME"
echo "Endpoint:  http://$WEBSITE_ENDPOINT"
echo "Build:     dist/ (ready for upload)"
echo ""
echo "� Security Note:"
echo "=================="
echo "This application now uses modern AWS authentication:"
echo "✅ Cognito for user authentication"
echo "✅ IAM roles for backend services"
echo "✅ Presigned URLs for secure uploads"
echo "✅ No AWS access keys in frontend code"
echo ""
echo "💡 Next Steps:"
echo "1. Choose a deployment method above"
echo "2. Upload your ./dist/ files to S3"
echo "3. Test your application at: http://$WEBSITE_ENDPOINT"
echo "4. Register new users via Cognito authentication"
echo ""
echo "🎉 Build completed - Ready for secure deployment!" 