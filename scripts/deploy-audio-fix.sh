#!/bin/bash

# Deploy Audio Upload Fix
# This script packages the updated Lambda function and deploys the infrastructure changes

set -e

echo "🔧 Deploying Audio Upload Fix..."

# Change to project root
cd "$(dirname "$0")/.."

# Change to terraform directory
cd terraform

echo "📦 Cleaning up old packages..."
rm -f lambda_function.zip
rm -f ai_video_lambda.zip

echo "📦 Creating Lambda deployment package with audio support..."
# Create the lambda package
cd lambda
zip -r ../lambda_function.zip . -x "*.DS_Store" "*.git*"
cd ..

echo "📦 Lambda package created: lambda_function.zip"

echo "🚀 Applying Terraform changes..."
# Apply terraform changes
terraform plan

read -p "Do you want to apply these changes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying infrastructure changes..."
    terraform apply -auto-approve
    
    echo "✅ Deployment complete!"
    echo ""
    echo "🎯 Audio upload endpoints are now available:"
    echo "   - GET  /audio        (list audio files)"
    echo "   - POST /audio        (save audio metadata)"  
    echo "   - POST /audio/upload-url (get presigned upload URL)"
    echo ""
    echo "🧪 Test the audio upload functionality:"
    echo "   1. Navigate to /ai-video in your application"
    echo "   2. Try uploading an audio file"
    echo "   3. Check the browser console for any remaining errors"
    echo ""
    echo "📊 Check CloudWatch Logs if you encounter issues:"
    echo "   aws logs tail --follow /aws/lambda/easy-video-share-silmari-dev-video-metadata-api"
else
    echo "❌ Deployment cancelled"
    exit 1
fi

echo "🎉 Audio upload fix deployment complete!" 