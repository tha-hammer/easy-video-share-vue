# Step 4: Create Lambda layer ZIP
Write-Host "🔧 Step 4: Creating Lambda layer ZIP..." -ForegroundColor Yellow
if (Test-Path $LAMBDA_LAYER_ZIP) {
    Remove-Item $LAMBDA_LAYER_ZIP -Force
}

# Create the correct Lambda layer structure: nodejs/node_modules/
Compress-Archive -Path "$LAMBDA_LAYER_DIR/nodejs" -DestinationPath $LAMBDA_LAYER_ZIP
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create Lambda layer ZIP" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda layer ZIP created: $LAMBDA_LAYER_ZIP" -ForegroundColor Green

# Step 7: Deploy with Terraform
Write-Host "🔧 Step 7: Deploying with Terraform..." -ForegroundColor Cyan
Set-Location terraform

# Initialize Terraform if needed
if (-not (Test-Path ".terraform")) {
    Write-Host "   Initializing Terraform..." -ForegroundColor Yellow
    terraform init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Terraform initialization failed" -ForegroundColor Red
        Set-Location $PROJECT_ROOT
        exit 1
    }
}

# Delete existing Lambda function if it exists (to avoid conflicts)
Write-Host "   Checking for existing Lambda function..." -ForegroundColor Yellow
try {
    $EXISTING_FUNCTION = aws lambda get-function --function-name "easy-video-share-ai-video-processor" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Found existing Lambda function, deleting it..." -ForegroundColor Yellow
        aws lambda delete-function --function-name "easy-video-share-ai-video-processor"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Existing Lambda function deleted" -ForegroundColor Green
            # Wait a moment for deletion to complete
            Start-Sleep -Seconds 5
        } else {
            Write-Host "   ⚠️  Failed to delete existing function, continuing anyway..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "   No existing Lambda function found" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Error checking for existing function, continuing anyway..." -ForegroundColor Yellow
}

# Plan the deployment
Write-Host "   Planning deployment..." -ForegroundColor Yellow
terraform plan -out=tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform plan failed" -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}

# Apply the deployment
Write-Host "   Applying deployment..." -ForegroundColor Yellow
terraform apply tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform apply failed" -ForegroundColor Red
    Set-Location $PROJECT_ROOT
    exit 1
}

# Step 8: Get API Gateway URL
Write-Host "🔧 Step 8: Getting API Gateway URL..." -ForegroundColor Cyan
$API_URL = (Set-Location terraform; terraform output -raw api_gateway_endpoint 2>$null)
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ API Gateway URL: $API_URL" -ForegroundColor Green
    Write-Host "   AI Video endpoint: $API_URL/ai-video" -ForegroundColor Green
} else {
    Write-Host "⚠️  Could not get API Gateway URL" -ForegroundColor Yellow
}
Set-Location $PROJECT_ROOT 