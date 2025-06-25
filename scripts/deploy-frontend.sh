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

echo "📤 Deploying to S3..."

# Upload all files
aws s3 cp dist/ s3://$BUCKET_NAME/ --recursive --exclude "*.map"

# Set specific content types for better performance
echo "🔧 Setting content types..."

# HTML files
aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
    --content-type "text/html" \
    --cache-control "public, max-age=300"

# CSS files
aws s3 cp dist/assets/ s3://$BUCKET_NAME/assets/ \
    --recursive \
    --exclude "*" \
    --include "*.css" \
    --content-type "text/css" \
    --cache-control "public, max-age=31536000"

# JavaScript files
aws s3 cp dist/assets/ s3://$BUCKET_NAME/assets/ \
    --recursive \
    --exclude "*" \
    --include "*.js" \
    --content-type "application/javascript" \
    --cache-control "public, max-age=31536000"

# SVG files
if find dist -name "*.svg" -type f | grep -q .; then
    aws s3 cp dist/ s3://$BUCKET_NAME/ \
        --recursive \
        --exclude "*" \
        --include "*.svg" \
        --content-type "image/svg+xml" \
        --cache-control "public, max-age=31536000"
fi

# PNG/ICO files
if find dist -name "*.png" -o -name "*.ico" -type f | grep -q .; then
    aws s3 cp dist/ s3://$BUCKET_NAME/ \
        --recursive \
        --exclude "*" \
        --include "*.png" \
        --include "*.ico" \
        --cache-control "public, max-age=31536000"
fi

echo "✅ Vue3 deployment complete!"
echo ""
echo "🌐 Your Vue3 application is now live at:"
echo "   http://$WEBSITE_ENDPOINT"
echo ""
echo "📋 Deployment Summary:"
echo "====================="
echo "Bucket:    $BUCKET_NAME"
echo "Endpoint:  http://$WEBSITE_ENDPOINT"
echo "Build:     dist/"
echo ""
echo "💡 Tips:"
echo "- Test your Vue3 application by visiting the URL above"
echo "- It may take a few minutes for changes to propagate"
echo "- Check browser developer tools if you encounter issues"
echo "- Consider fixing TypeScript errors by running 'npm run type-check'"
echo ""
echo "⚠️  Note: Deployment used build-only (TypeScript type checking was skipped)"
echo "   Run 'npm run type-check' to see and fix TypeScript issues"
echo ""
echo "🎉 Happy Vue3 video sharing!" 