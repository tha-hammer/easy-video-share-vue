#!/bin/bash

# Deploy Terraform updates for database and Lambda changes
# This script applies the updates we made to support the new segment architecture

set -e

echo "🚀 Starting Terraform deployment for database and Lambda updates..."

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo "❌ Error: main.tf not found. Please run this script from the terraform directory."
    exit 1
fi

# Initialize Terraform if needed
echo "📋 Initializing Terraform..."
terraform init

# Plan the changes
echo "📋 Planning Terraform changes..."
terraform plan -out=tfplan

# Show what will be changed
echo "📋 Changes to be applied:"
terraform show tfplan

# Ask for confirmation
read -p "🤔 Do you want to apply these changes? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

# Apply the changes
echo "🚀 Applying Terraform changes..."
terraform apply tfplan

# Clean up the plan file
rm tfplan

echo "✅ Terraform deployment completed successfully!"
echo ""
echo "📊 Summary of changes applied:"
echo "  • Updated video_metadata table with new GSI: user_id-created_at-index"
echo "  • Updated video_segments table with additional attributes and GSIs"
echo "  • Updated Lambda environment variables to include both table names"
echo "  • Enhanced Lambda IAM permissions for batch operations"
echo ""
echo "🔧 Next steps:"
echo "  1. Test the thumbnail generation functionality"
echo "  2. Verify segment retrieval works with both storage systems"
echo "  3. Test text overlay processing"
echo ""
echo "🎯 The system now supports:"
echo "  • Video upload pipeline using output_s3_urls in video-metadata table"
echo "  • Text overlay pipeline using video-segments table for additional data"
echo "  • Seamless segment retrieval from both storage systems" 