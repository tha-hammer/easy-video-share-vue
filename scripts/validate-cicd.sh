#!/bin/bash

# CI/CD Validation Script
# This script helps validate that your CI/CD setup is ready

set -e

echo "🔍 Validating CI/CD Setup for Easy Video Share"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in a git repository
echo "🔍 Checking Git repository..."
if [ -d ".git" ]; then
    success "Git repository found"
    
    # Check if we have a remote origin
    if git remote get-url origin &> /dev/null; then
        REMOTE_URL=$(git remote get-url origin)
        success "Git remote origin: $REMOTE_URL"
        
        # Extract GitHub repository name
        if [[ $REMOTE_URL == *"github.com"* ]]; then
            GITHUB_REPO=$(echo $REMOTE_URL | sed -n 's/.*github\.com[:/]\([^/]*\/[^/]*\)\.git/\1/p' | sed 's/\.git$//')
            if [ -z "$GITHUB_REPO" ]; then
                GITHUB_REPO=$(echo $REMOTE_URL | sed -n 's/.*github\.com[:/]\([^/]*\/[^/]*\)/\1/p')
            fi
            
            if [ -n "$GITHUB_REPO" ]; then
                success "GitHub repository: $GITHUB_REPO"
                echo "💡 Use this in terraform.tfvars: github_repository = \"$GITHUB_REPO\""
            else
                warning "Could not extract GitHub repository name from: $REMOTE_URL"
            fi
        else
            warning "Remote is not a GitHub repository"
        fi
    else
        error "No git remote origin found. Push your code to GitHub first."
    fi
else
    error "Not a git repository. Initialize git first: git init"
fi

echo ""
echo "🔍 Checking CI/CD files..."

# Check for GitHub Actions workflows
if [ -d ".github/workflows" ]; then
    success ".github/workflows directory found"
    
    if [ -f ".github/workflows/backend-deploy.yml" ]; then
        success "Backend deployment workflow found"
    else
        error "Backend deployment workflow missing"
    fi
    
    if [ -f ".github/workflows/frontend-deploy.yml" ]; then
        success "Frontend deployment workflow found"
    else
        error "Frontend deployment workflow missing"
    fi
else
    error ".github/workflows directory not found"
fi

echo ""
echo "🔍 Checking Terraform configuration..."

if [ -d "terraform" ]; then
    success "Terraform directory found"
    
    if [ -f "terraform/github-oidc.tf" ]; then
        success "GitHub OIDC configuration found"
    else
        error "GitHub OIDC configuration missing (terraform/github-oidc.tf)"
    fi
    
    if [ -f "terraform/terraform.tfvars" ]; then
        success "Terraform variables file found"
        
        # Check if github_repository is configured
        if grep -q "github_repository" terraform/terraform.tfvars; then
            CONFIGURED_REPO=$(grep "github_repository" terraform/terraform.tfvars | cut -d'"' -f2)
            success "GitHub repository configured: $CONFIGURED_REPO"
        else
            warning "github_repository not configured in terraform.tfvars"
            echo "💡 Add this line: github_repository = \"your-username/your-repo\""
        fi
    else
        warning "terraform.tfvars not found. Copy from terraform.tfvars.example"
    fi
else
    error "Terraform directory not found"
fi

echo ""
echo "🔍 Checking Node.js setup..."

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js found: $NODE_VERSION"
    
    if [ -f "package.json" ]; then
        success "package.json found"
        
        if command -v npm &> /dev/null; then
            success "npm available"
            
            # Check if dependencies are installed
            if [ -d "node_modules" ]; then
                success "Dependencies installed"
            else
                warning "Dependencies not installed. Run: npm install"
            fi
        else
            error "npm not found"
        fi
    else
        error "package.json not found"
    fi
else
    error "Node.js not found. Install Node.js 18+"
fi

echo ""
echo "🔍 Checking AWS/Terraform tools..."

if command -v terraform &> /dev/null; then
    TERRAFORM_VERSION=$(terraform version | head -n1)
    success "Terraform found: $TERRAFORM_VERSION"
else
    error "Terraform not found. Install from: https://terraform.io"
fi

if command -v aws &> /dev/null; then
    success "AWS CLI found"
    
    # Check if AWS credentials are configured (for initial setup)
    if aws sts get-caller-identity &> /dev/null; then
        success "AWS credentials configured"
    else
        warning "AWS credentials not configured (OK if using CI/CD only)"
    fi
else
    warning "AWS CLI not found (optional for CI/CD setup)"
fi

echo ""
echo "📋 CI/CD Setup Summary"
echo "======================"

echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. **Update Terraform configuration**:"
echo "   cd terraform"
echo "   # Edit terraform.tfvars and add your GitHub repository"
echo "   terraform apply"
echo ""
echo "2. **Get GitHub Actions role ARN**:"
echo "   terraform output github_actions_role_arn"
echo ""
echo "3. **Add GitHub repository secret**:"
echo "   - Go to GitHub Settings → Secrets → Actions"
echo "   - Add secret: AWS_ROLE_TO_ASSUME"
echo "   - Value: [Role ARN from step 2]"
echo ""
echo "4. **Test the pipeline**:"
echo "   git add ."
echo "   git commit -m 'Setup CI/CD pipeline'"
echo "   git push origin main"
echo ""
echo "📖 For detailed instructions, see: CICD-SETUP.md"
echo ""
echo "🎉 Your CI/CD pipeline will then deploy automatically on every push to main!"
