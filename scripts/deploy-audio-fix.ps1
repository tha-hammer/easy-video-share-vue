# Deploy Audio Upload Fix - PowerShell Version
# This script packages the updated Lambda function and deploys the infrastructure changes

Write-Host "🔧 Deploying Audio Upload Fix..." -ForegroundColor Green

# Change to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Change to terraform directory  
Set-Location "terraform"

Write-Host "📦 Cleaning up old packages..." -ForegroundColor Yellow
if (Test-Path "lambda_function.zip") { Remove-Item "lambda_function.zip" }
if (Test-Path "ai_video_lambda.zip") { Remove-Item "ai_video_lambda.zip" }

Write-Host "📦 Creating Lambda deployment package with audio support..." -ForegroundColor Yellow

# Create the lambda package using PowerShell's Compress-Archive
try {
    Compress-Archive -Path "lambda\*" -DestinationPath "lambda_function.zip" -Force
    Write-Host "📦 Lambda package created: lambda_function.zip" -ForegroundColor Green
} catch {
    Write-Error "Failed to create Lambda package: $_"
    exit 1
}

Write-Host "🚀 Planning Terraform changes..." -ForegroundColor Blue
& terraform plan

if ($LASTEXITCODE -ne 0) {
    Write-Error "Terraform plan failed!"
    exit 1
}

$confirmation = Read-Host "Do you want to apply these changes? (y/N)"
if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
    Write-Host "🚀 Deploying infrastructure changes..." -ForegroundColor Blue
    & terraform apply -auto-approve
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎯 Audio upload endpoints are now available:" -ForegroundColor Cyan
        Write-Host "   - GET  /audio        (list audio files)" -ForegroundColor White
        Write-Host "   - POST /audio        (save audio metadata)" -ForegroundColor White
        Write-Host "   - POST /audio/upload-url (get presigned upload URL)" -ForegroundColor White
        Write-Host ""
        Write-Host "🧪 Test the audio upload functionality:" -ForegroundColor Cyan
        Write-Host "   1. Navigate to /ai-video in your application" -ForegroundColor White
        Write-Host "   2. Try uploading an audio file" -ForegroundColor White
        Write-Host "   3. Check the browser console for any remaining errors" -ForegroundColor White
        Write-Host ""
        Write-Host "📊 Check CloudWatch Logs if you encounter issues:" -ForegroundColor Cyan
        Write-Host "   aws logs tail --follow /aws/lambda/easy-video-share-silmari-dev-video-metadata-api" -ForegroundColor White
    } else {
        Write-Error "Terraform apply failed!"
        exit 1
    }
} else {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Audio upload fix deployment complete!" -ForegroundColor Green 