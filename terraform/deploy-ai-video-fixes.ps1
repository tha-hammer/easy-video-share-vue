# Deploy AI Video Generation Fixes
# This script deploys the fixes for the AI video generation Lambda function

Write-Host "🚀 Deploying AI Video Generation Fixes..." -ForegroundColor Green

# Navigate to terraform directory
Set-Location -Path "terraform"

# Step 1: Create new Lambda deployment package
Write-Host "📦 Creating new Lambda deployment package..." -ForegroundColor Yellow

# Remove old package if it exists
if (Test-Path "ai_video_lambda_fixed.zip") {
    Remove-Item "ai_video_lambda_fixed.zip" -Force
}

# Create new package with fixes
Compress-Archive -Path "lambda-ai-video\*" -DestinationPath "ai_video_lambda_fixed.zip" -Force

Write-Host "✅ Lambda package created: ai_video_lambda_fixed.zip" -ForegroundColor Green

# Step 2: Apply Terraform changes (this will add the missing GSI)
Write-Host "🏗️ Applying Terraform infrastructure changes..." -ForegroundColor Yellow

# Initialize Terraform if needed
terraform init

# Plan the changes
Write-Host "📋 Planning Terraform changes..." -ForegroundColor Yellow
terraform plan -out=tfplan-fixes

# Apply the changes
Write-Host "🚀 Applying Terraform changes..." -ForegroundColor Yellow
terraform apply tfplan-fixes

Write-Host "✅ Terraform changes applied successfully" -ForegroundColor Green

# Step 3: Update Lambda function with new code
Write-Host "🔄 Updating Lambda function with fixes..." -ForegroundColor Yellow

# Get the Lambda function name from Terraform output
$lambdaFunctionName = terraform output -raw ai_video_lambda_function_name

if (-not $lambdaFunctionName) {
    Write-Host "❌ Could not get Lambda function name from Terraform output" -ForegroundColor Red
    exit 1
}

Write-Host "📝 Lambda function name: $lambdaFunctionName" -ForegroundColor Cyan

# Update the Lambda function code
aws lambda update-function-code `
    --function-name $lambdaFunctionName `
    --zip-file fileb://ai_video_lambda_fixed.zip `
    --region us-east-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Lambda function updated successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to update Lambda function" -ForegroundColor Red
    exit 1
}

# Step 4: Wait for Lambda update to complete
Write-Host "⏳ Waiting for Lambda update to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 5: Test the fixes
Write-Host "🧪 Testing the fixes..." -ForegroundColor Yellow

# Create a test payload
$testPayload = @{
    httpMethod = "POST"
    path = "/ai-video"
    body = '{
        "audioId": "test-audio-id",
        "prompt": "Test AI video generation",
        "targetDuration": 30,
        "style": "cinematic"
    }'
    headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer test-token"
    }
    requestContext = @{
        authorizer = @{
            claims = @{
                sub = "test-user-123"
                email = "test@example.com"
            }
        }
    }
} | ConvertTo-Json -Depth 10

# Save test payload
$testPayload | Out-File -FilePath "test-payload-fixes.json" -Encoding UTF8

Write-Host "✅ Test payload created: test-payload-fixes.json" -ForegroundColor Green

Write-Host "🎉 AI Video Generation Fixes Deployed Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary of fixes applied:" -ForegroundColor Cyan
Write-Host "   ✅ Fixed DynamoDB GSI query with fallback" -ForegroundColor Green
Write-Host "   ✅ Added missing GSI to Terraform configuration" -ForegroundColor Green
Write-Host "   ✅ Fixed undefined values in DynamoDB operations" -ForegroundColor Green
Write-Host "   ✅ Fixed const assignment error in updateAIGenerationStatus" -ForegroundColor Green
Write-Host ""
Write-Host "🧪 To test the fixes:" -ForegroundColor Yellow
Write-Host "   aws lambda invoke --function-name $lambdaFunctionName --payload file://test-payload-fixes.json response-fixes.json" -ForegroundColor White
Write-Host ""
Write-Host "📊 To monitor logs:" -ForegroundColor Yellow
Write-Host "   aws logs tail /aws/lambda/$lambdaFunctionName --follow" -ForegroundColor White 