# Build Vue3 Frontend (No Deployment) - PowerShell Version
# This script only builds the frontend without deploying to avoid AWS credential issues

param(
    [switch]$SkipInstall = $false
)

Write-Host "🔨 Building Vue3 Frontend" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Check if we're in the right directory
if (!(Test-Path "package.json") -or !(Test-Path "src")) {
    Write-Host "❌ Error: Run this script from the Vue3 project root directory" -ForegroundColor Red
    Write-Host "Expected: package.json and src/ directories" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
if (!(Test-Path "node_modules") -and !$SkipInstall) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install failed" -ForegroundColor Red
        exit 1
    }
}

# Build the frontend
Write-Host "🔨 Building Vue3 application..." -ForegroundColor Yellow

npm run build-only

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Build files ready in: ./dist/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Next Steps for Deployment:" -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Green
    Write-Host ""
    Write-Host "1. Using Terraform (Recommended):" -ForegroundColor Yellow
    Write-Host "   cd terraform" -ForegroundColor Cyan
    Write-Host "   terraform apply  # This will create a deployment script" -ForegroundColor Cyan
    Write-Host "   powershell -ExecutionPolicy Bypass -File deploy-frontend-manual.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Using AWS CloudShell:" -ForegroundColor Yellow
    Write-Host "   - Upload your ./dist/ folder to AWS CloudShell" -ForegroundColor Cyan
    Write-Host "   - Run the AWS CLI commands from there" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Using AWS S3 Console:" -ForegroundColor Yellow
    Write-Host "   - Go to AWS S3 Console" -ForegroundColor Cyan
    Write-Host "   - Upload all files from ./dist/ to your bucket" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4. Using CI/CD Pipeline:" -ForegroundColor Yellow
    Write-Host "   - Set up GitHub Actions or similar with IAM role assumption" -ForegroundColor Cyan
    Write-Host "   - Configure automated deployment from git pushes" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔒 Security Note:" -ForegroundColor Green
    Write-Host "This application uses modern AWS authentication (no access keys needed):" -ForegroundColor White
    Write-Host "✅ Cognito for user authentication" -ForegroundColor Yellow
    Write-Host "✅ IAM roles for backend services" -ForegroundColor Yellow
    Write-Host "✅ Presigned URLs for secure uploads" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Build failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "- Run 'npm run lint' to fix linting issues" -ForegroundColor Cyan
    Write-Host "- Run 'npm run type-check' to see TypeScript issues" -ForegroundColor Cyan
    Write-Host "- Check for syntax errors in Vue components" -ForegroundColor Cyan
    exit 1
}
