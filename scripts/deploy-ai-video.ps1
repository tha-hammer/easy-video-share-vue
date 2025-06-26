# AI Video Deployment Script for Easy Video Share
# This script builds the Lambda layer and deploys the AI video infrastructure

Write-Host "🚀 Deploying AI Video Infrastructure for Easy Video Share" -ForegroundColor Green
Write-Host ""

# Configuration
$PROJECT_ROOT = Get-Location
$LAMBDA_LAYER_DIR = "lambda-layer"
$LAMBDA_LAYER_ZIP = "ai_video_layer.zip"
$LAMBDA_ZIP = "ai_video_lambda.zip"

# Step 1: Create Lambda layer directory
Write-Host "🔧 Step 1: Creating Lambda layer..." -ForegroundColor Yellow
if (Test-Path $LAMBDA_LAYER_DIR) {
    Remove-Item $LAMBDA_LAYER_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $LAMBDA_LAYER_DIR -Force | Out-Null
New-Item -ItemType Directory -Path "$LAMBDA_LAYER_DIR/nodejs" -Force | Out-Null

# Step 2: Create package.json for Lambda layer
Write-Host "🔧 Step 2: Creating package.json for Lambda layer..." -ForegroundColor Yellow
$PACKAGE_JSON = @"
{
  "name": "ai-video-layer",
  "version": "1.0.0",
  "description": "AI Video Generation Dependencies",
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.450.0",
    "@aws-sdk/client-s3": "^3.450.0",
    "@aws-sdk/client-secrets-manager": "^3.450.0",
    "@aws-sdk/client-transcribe": "^3.450.0",
    "@aws-sdk/lib-dynamodb": "^3.450.0",
    "google-auth-library": "^9.0.0",
    "@google-cloud/vertexai": "^0.1.0",
    "openai": "^4.20.0"
  }
}
"@

$PACKAGE_JSON | Out-File -FilePath "$LAMBDA_LAYER_DIR/nodejs/package.json" -Encoding UTF8

# Step 3: Install dependencies
Write-Host "🔧 Step 3: Installing Lambda layer dependencies..." -ForegroundColor Yellow
Set-Location "$LAMBDA_LAYER_DIR/nodejs"
npm install --production
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}
Set-Location $PROJECT_ROOT

# Step 4: Create Lambda layer ZIP
Write-Host "🔧 Step 4: Creating Lambda layer ZIP..." -ForegroundColor Yellow
if (Test-Path $LAMBDA_LAYER_ZIP) {
    Remove-Item $LAMBDA_LAYER_ZIP -Force
}

Compress-Archive -Path "$LAMBDA_LAYER_DIR/nodejs/node_modules" -DestinationPath $LAMBDA_LAYER_ZIP
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create Lambda layer ZIP" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda layer ZIP created: $LAMBDA_LAYER_ZIP" -ForegroundColor Green

# Step 5: Create Lambda function ZIP
Write-Host "🔧 Step 5: Creating Lambda function ZIP..." -ForegroundColor Yellow
if (Test-Path $LAMBDA_ZIP) {
    Remove-Item $LAMBDA_ZIP -Force
}

# Copy Lambda function to a temporary directory
$TEMP_LAMBDA_DIR = "temp-lambda"
if (Test-Path $TEMP_LAMBDA_DIR) {
    Remove-Item $TEMP_LAMBDA_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $TEMP_LAMBDA_DIR -Force | Out-Null

Copy-Item "terraform/lambda-ai-video/ai-video.js" -Destination "$TEMP_LAMBDA_DIR/ai-video.js"

# Create ZIP
Compress-Archive -Path "$TEMP_LAMBDA_DIR/*" -DestinationPath $LAMBDA_ZIP
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create Lambda function ZIP" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda function ZIP created: $LAMBDA_ZIP" -ForegroundColor Green

# Clean up temporary files
Remove-Item $TEMP_LAMBDA_DIR -Recurse -Force
Remove-Item $LAMBDA_LAYER_DIR -Recurse -Force

# Step 6: Check Terraform configuration
Write-Host "🔧 Step 6: Checking Terraform configuration..." -ForegroundColor Yellow
if (-not (Test-Path "terraform/terraform.tfvars")) {
    Write-Host "❌ terraform.tfvars not found. Please run the Google Cloud setup script first:" -ForegroundColor Red
    Write-Host "   .\scripts\setup-google-cloud.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if required variables are set
$TFVARS_CONTENT = Get-Content "terraform/terraform.tfvars" -Raw
if ($TFVARS_CONTENT -notmatch "google_cloud_project_id") {
    Write-Host "❌ google_cloud_project_id not found in terraform.tfvars" -ForegroundColor Red
    Write-Host "   Please run the Google Cloud setup script first" -ForegroundColor Yellow
    exit 1
}

if ($TFVARS_CONTENT -notmatch "openai_api_key") {
    Write-Host "⚠️  openai_api_key not found in terraform.tfvars" -ForegroundColor Yellow
    Write-Host "   Please add your OpenAI API key to terraform.tfvars" -ForegroundColor Yellow
}

# Step 7: Deploy with Terraform
Write-Host "🔧 Step 7: Deploying with Terraform..." -ForegroundColor Yellow
Set-Location terraform

# Initialize Terraform if needed
if (-not (Test-Path ".terraform")) {
    Write-Host "   Initializing Terraform..." -ForegroundColor White
    terraform init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Terraform initialization failed" -ForegroundColor Red
        Set-Location $PROJECT_ROOT
        exit 1
    }
}

# Plan the deployment
Write-Host "   Planning deployment..." -ForegroundColor White
terraform plan -out=tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform plan failed" -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}

# Apply the deployment
Write-Host "   Applying deployment..." -ForegroundColor White
terraform apply tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform apply failed" -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}

Set-Location $PROJECT_ROOT

# Step 8: Get API Gateway URL
Write-Host "🔧 Step 8: Getting API Gateway URL..." -ForegroundColor Yellow
$API_URL = terraform -chdir=terraform output -raw api_gateway_url
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ API Gateway URL: $API_URL" -ForegroundColor Green
    Write-Host "   AI Video endpoint: $API_URL/ai-video" -ForegroundColor White
} else {
    Write-Host "⚠️  Could not get API Gateway URL" -ForegroundColor Yellow
}

# Step 9: Update frontend configuration
Write-Host "🔧 Step 9: Updating frontend configuration..." -ForegroundColor Yellow
$ENV_FILE = ".env"
if (Test-Path $ENV_FILE) {
    $ENV_CONTENT = Get-Content $ENV_FILE -Raw
    if ($ENV_CONTENT -notmatch "VITE_API_BASE_URL") {
        Add-Content $ENV_FILE "`n# API Configuration`nVITE_API_BASE_URL=$API_URL"
        Write-Host "✅ Added API base URL to .env file" -ForegroundColor Green
    }
} else {
    "# API Configuration`nVITE_API_BASE_URL=$API_URL" | Out-File -FilePath $ENV_FILE -Encoding UTF8
    Write-Host "✅ Created .env file with API base URL" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 AI Video infrastructure deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 What was deployed:" -ForegroundColor Cyan
Write-Host "   ✅ Lambda function for AI video processing" -ForegroundColor White
Write-Host "   ✅ Lambda layer with dependencies" -ForegroundColor White
Write-Host "   ✅ API Gateway endpoints" -ForegroundColor White
Write-Host "   ✅ Secrets Manager for credentials" -ForegroundColor White
Write-Host "   ✅ CloudWatch logging" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Test your AI video features:" -ForegroundColor Cyan
Write-Host "   1. Start your Vue development server: npm run dev" -ForegroundColor White
Write-Host "   2. Upload an audio file" -ForegroundColor White
Write-Host "   3. Navigate to AI Video generation" -ForegroundColor White
Write-Host "   4. Test the AI video generation workflow" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitor your deployment:" -ForegroundColor Cyan
Write-Host "   - CloudWatch Logs: /aws/lambda/easy-video-share-ai-video-processor" -ForegroundColor White
Write-Host "   - API Gateway Console: https://console.aws.amazon.com/apigateway" -ForegroundColor White
Write-Host "   - Lambda Console: https://console.aws.amazon.com/lambda" -ForegroundColor White 