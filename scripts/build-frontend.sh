#!/bin/bash

# Build Vue3 Frontend (No Deployment)
# This script only builds the frontend without deploying to avoid AWS credential issues

set -e

echo "🔨 Building Vue3 Frontend"
echo "========================="

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "src" ]; then
    echo "❌ Error: Run this script from the Vue3 project root directory"
    echo "Expected: package.json and src/ directories"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies..."
    npm install
fi

# Build the frontend
echo "🔨 Building Vue3 application..."

if npm run build-only; then
    echo "✅ Build successful!"
    echo ""
    echo "📦 Build files ready in: ./dist/"
    echo ""
    echo "🚀 Next Steps for Deployment:"
    echo "=============================="
    echo ""
    echo "🎯 **RECOMMENDED: CI/CD Pipeline**"
    echo "   Set up GitHub Actions for automated deployment:"
    echo "   ./scripts/validate-cicd.sh  # Check CI/CD setup"
    echo "   See CICD-SETUP.md for detailed instructions"
    echo ""
    echo "📦 **Alternative: Manual Deployment Options**"
    echo ""
    echo "1. **Using Terraform Script**:"
    echo "   cd terraform"
    echo "   terraform apply  # Creates deployment script"
    echo "   powershell -ExecutionPolicy Bypass -File deploy-frontend-manual.ps1"
    echo ""
    echo "2. **Using AWS CloudShell**:"
    echo "   - Upload your ./dist/ folder to AWS CloudShell"
    echo "   - Run the AWS CLI commands from there"
    echo ""
    echo "3. **Using AWS S3 Console**:"
    echo "   - Go to AWS S3 Console"
    echo "   - Upload all files from ./dist/ to your bucket"
    echo ""
    echo "🔒 Security Note:"
    echo "This application uses modern AWS authentication (no access keys needed):"
    echo "✅ Cognito for user authentication"
    echo "✅ IAM roles for backend services"  
    echo "✅ Presigned URLs for secure uploads"
    echo ""
else
    echo "❌ Build failed"
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "- Run 'npm run lint' to fix linting issues"
    echo "- Run 'npm run type-check' to see TypeScript issues"
    echo "- Check for syntax errors in Vue components"
    exit 1
fi
