# Frontend Deployment Instructions
# 
# IMPORTANT: This Terraform configuration does NOT automatically deploy frontend files
# because the application uses IAM roles instead of AWS access keys for security.
#
# Instead, this file provides deployment guidance and creates a deployment package.

# Local variables for frontend paths
locals {
  frontend_dist_path = "${path.root}/../dist"
  frontend_build_path = "${path.root}/.."
  deployment_script_path = "${path.root}/deploy-frontend-manual.ps1"
}

# Create a PowerShell deployment script that can be run manually
resource "local_file" "frontend_deployment_script" {
  filename = local.deployment_script_path
  content = <<-EOT
# Easy Video Share - Frontend Deployment Script
# This script deploys the Vue.js frontend to S3 using proper AWS authentication

$BucketName = "${aws_s3_bucket.video_bucket.bucket}"
$WebsiteEndpoint = "${aws_s3_bucket_website_configuration.video_bucket_website.website_endpoint}"

Write-Host "🚀 Easy Video Share - Frontend Deployment" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Target Bucket: $BucketName" -ForegroundColor Yellow
Write-Host "Website URL: http://$WebsiteEndpoint" -ForegroundColor Yellow
Write-Host ""

# Check if AWS CLI is available
if (!(Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    Write-Host "Visit: https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check if build directory exists
if (!(Test-Path "../dist")) {
    Write-Host "❌ Build directory not found. Building frontend..." -ForegroundColor Red
    Set-Location ".."
    npm install
    npm run build-only
    Set-Location "terraform"
    
    if (!(Test-Path "../dist")) {
        Write-Host "❌ Build failed. Please check the build process." -ForegroundColor Red
        exit 1
    }
}

Write-Host "📤 Deploying frontend files to S3..." -ForegroundColor Green

# Upload all files
Write-Host "Uploading all files..." -ForegroundColor Cyan
aws s3 cp ../dist/ s3://$BucketName/ --recursive --exclude "*.map"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Upload failed. Please check your AWS credentials and permissions." -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Make sure you have:" -ForegroundColor Yellow
    Write-Host "  - AWS CLI configured with valid credentials" -ForegroundColor Yellow
    Write-Host "  - S3 write permissions for bucket: $BucketName" -ForegroundColor Yellow
    Write-Host "  - Or use AWS CloudShell for deployment" -ForegroundColor Yellow
    exit 1
}

# Set content types for better performance
Write-Host "Setting content types..." -ForegroundColor Cyan

aws s3 cp ../dist/index.html s3://$BucketName/index.html --content-type "text/html" --cache-control "public, max-age=300"
aws s3 cp ../dist/assets/ s3://$BucketName/assets/ --recursive --exclude "*" --include "*.css" --content-type "text/css" --cache-control "public, max-age=31536000"
aws s3 cp ../dist/assets/ s3://$BucketName/assets/ --recursive --exclude "*" --include "*.js" --content-type "application/javascript" --cache-control "public, max-age=31536000"

# Handle optional files
if (Get-ChildItem -Path "../dist" -Filter "*.svg" -Recurse) {
    aws s3 cp ../dist/ s3://$BucketName/ --recursive --exclude "*" --include "*.svg" --content-type "image/svg+xml" --cache-control "public, max-age=31536000"
}

if (Get-ChildItem -Path "../dist" -Filter "*.png" -Recurse) {
    aws s3 cp ../dist/ s3://$BucketName/ --recursive --exclude "*" --include "*.png" --include "*.ico" --cache-control "public, max-age=31536000"
}

Write-Host ""
Write-Host "✅ Frontend deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your application is available at:" -ForegroundColor Green
Write-Host "   http://$WebsiteEndpoint" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔒 Security Features Active:" -ForegroundColor Green
Write-Host "✅ Cognito Authentication" -ForegroundColor Yellow
Write-Host "✅ IAM Role-based Backend" -ForegroundColor Yellow
Write-Host "✅ Presigned URL Uploads" -ForegroundColor Yellow
Write-Host "✅ No Access Keys in Frontend" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 Ready for secure video sharing!" -ForegroundColor Green
EOT

  depends_on = [
    aws_s3_bucket.video_bucket,
    aws_s3_bucket_website_configuration.video_bucket_website
  ]
}

# Output deployment instructions
output "frontend_deployment_instructions" {
  description = "Instructions for deploying the frontend"
  value = <<-EOT
Frontend deployment script created at: ${local.deployment_script_path}

To deploy your frontend:
1. Run: cd terraform
2. Run: powershell -ExecutionPolicy Bypass -File deploy-frontend-manual.ps1

Alternative deployment methods:
- Use AWS CloudShell (recommended for one-time deployment)
- Set up CI/CD with IAM role assumption
- Use AWS Console S3 upload (manual)

Your website will be available at: http://${aws_s3_bucket_website_configuration.video_bucket_website.website_endpoint}
EOT
}
