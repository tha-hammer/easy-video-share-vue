# AI Video Cleanup Script
# This script deletes the AI video Lambda function and related resources

Write-Host "🧹 AI Video Cleanup Script" -ForegroundColor Cyan
Write-Host ""

# Configuration
$FUNCTION_NAME = "easy-video-share-ai-video-processor"
$LAYER_NAME = "easy-video-share-ai-video-layer"

Write-Host "🔍 Checking for existing resources..." -ForegroundColor Yellow

# Check and delete Lambda function
Write-Host "   Checking for Lambda function: $FUNCTION_NAME" -ForegroundColor Yellow
try {
    $FUNCTION = aws lambda get-function --function-name $FUNCTION_NAME 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Found Lambda function, deleting..." -ForegroundColor Yellow
        aws lambda delete-function --function-name $FUNCTION_NAME
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Lambda function deleted" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to delete Lambda function" -ForegroundColor Red
        }
    } else {
        Write-Host "   No Lambda function found" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Error checking Lambda function" -ForegroundColor Yellow
}

# Check and delete Lambda layer
Write-Host "   Checking for Lambda layer: $LAYER_NAME" -ForegroundColor Yellow
try {
    $LAYERS = aws lambda list-layers --query "Layers[?LayerName=='$LAYER_NAME'].LayerArn" --output text 2>$null
    if ($LASTEXITCODE -eq 0 -and $LAYERS) {
        Write-Host "   Found Lambda layer, deleting..." -ForegroundColor Yellow
        aws lambda delete-layer-version --layer-name $LAYER_NAME --version-number 1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Lambda layer deleted" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Failed to delete Lambda layer" -ForegroundColor Red
        }
    } else {
        Write-Host "   No Lambda layer found" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Error checking Lambda layer" -ForegroundColor Yellow
}

# Clean up local files
Write-Host "   Cleaning up local files..." -ForegroundColor Yellow
$FILES_TO_DELETE = @(
    "terraform/ai_video_layer.zip",
    "terraform/ai_video_lambda.zip",
    "terraform/tfplan"
)

foreach ($FILE in $FILES_TO_DELETE) {
    if (Test-Path $FILE) {
        Remove-Item $FILE -Force
        Write-Host "   ✅ Deleted: $FILE" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🎉 Cleanup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Run the deployment script again: ./scripts/deploy-ai-video.ps1"
Write-Host "   2. Or run the test script: ./scripts/test-ai-video-transcription.sh" 