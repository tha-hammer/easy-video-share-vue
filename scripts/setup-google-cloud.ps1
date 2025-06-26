# Google Cloud Setup Script for Easy Video Share AI Features
# Run this script to set up Workload Identity Federation and required services

Write-Host "🚀 Setting up Google Cloud for Easy Video Share AI Video Features" -ForegroundColor Green
Write-Host ""

# Check if gcloud is installed
try {
    $gcloudVersion = gcloud version --format="value(basic.version)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Google Cloud CLI found: $gcloudVersion" -ForegroundColor Green
    } else {
        throw "gcloud not found"
    }
} catch {
    Write-Host "❌ Google Cloud CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Configuration
$PROJECT_ID = "easy-video-share"
$LOCATION = "us-central1"
$SERVICE_ACCOUNT_NAME = "easy-video-share-sa"
$SERVICE_ACCOUNT_EMAIL = "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
$WORKLOAD_IDENTITY_POOL = "easy-video-share"
$WORKLOAD_IDENTITY_PROVIDER = "easy-video-share"
$AWS_ACCOUNT_ID = "571960159088"

Write-Host "📋 Configuration:" -ForegroundColor Cyan
Write-Host "   Project ID: $PROJECT_ID" -ForegroundColor White
Write-Host "   Location: $LOCATION" -ForegroundColor White
Write-Host "   Service Account: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor White
Write-Host "   AWS Account ID: $AWS_ACCOUNT_ID" -ForegroundColor White
Write-Host ""

# Step 1: Set the project
Write-Host "🔧 Step 1: Setting Google Cloud project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set project. Please check your authentication." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Project set to: $PROJECT_ID" -ForegroundColor Green

# Step 2: Enable required APIs
Write-Host "🔧 Step 2: Enabling required APIs..." -ForegroundColor Yellow
$APIS = @(
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "iamcredentials.googleapis.com",
    "iam.googleapis.com"
)

foreach ($API in $APIS) {
    Write-Host "   Enabling $API..." -ForegroundColor White
    gcloud services enable $API --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $API enabled" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $API may already be enabled or failed" -ForegroundColor Yellow
    }
}

# Step 3: Create Workload Identity Pool
Write-Host "🔧 Step 3: Creating Workload Identity Pool..." -ForegroundColor Yellow
gcloud iam workload-identity-pools create $WORKLOAD_IDENTITY_POOL --location=global --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Workload Identity Pool created: $WORKLOAD_IDENTITY_POOL" -ForegroundColor Green
} else {
    Write-Host "⚠️  Workload Identity Pool may already exist" -ForegroundColor Yellow
}

# Step 4: Create Workload Identity Provider
Write-Host "🔧 Step 4: Creating Workload Identity Provider..." -ForegroundColor Yellow
gcloud iam workload-identity-pools providers create-aws $WORKLOAD_IDENTITY_PROVIDER `
    --workload-identity-pool=$WORKLOAD_IDENTITY_POOL `
    --account-id=$AWS_ACCOUNT_ID `
    --role-session-name=lambda-session `
    --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Workload Identity Provider created" -ForegroundColor Green
} else {
    Write-Host "⚠️  Workload Identity Provider may already exist" -ForegroundColor Yellow
}

# Step 5: Create Service Account
Write-Host "🔧 Step 5: Creating Service Account..." -ForegroundColor Yellow
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
    --display-name="Easy Video Share Service Account" `
    --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Service Account created: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Green
} else {
    Write-Host "⚠️  Service Account may already exist" -ForegroundColor Yellow
}

# Step 6: Get Project Number
Write-Host "🔧 Step 6: Getting Project Number..." -ForegroundColor Yellow
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Project Number: $PROJECT_NUMBER" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to get project number" -ForegroundColor Red
    exit 1
}

# Step 7: Grant Workload Identity User role
Write-Host "🔧 Step 7: Granting Workload Identity User role..." -ForegroundColor Yellow
$MEMBER = "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$WORKLOAD_IDENTITY_POOL/attribute.service_account/$SERVICE_ACCOUNT_EMAIL"

gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL `
    --role="roles/iam.workloadIdentityUser" `
    --member="$MEMBER" `
    --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Workload Identity User role granted" -ForegroundColor Green
} else {
    Write-Host "⚠️  Role may already be granted" -ForegroundColor Yellow
}

# Step 8: Grant required roles to service account
Write-Host "🔧 Step 8: Granting required roles to service account..." -ForegroundColor Yellow
$ROLES = @(
    "roles/aiplatform.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator"
)

foreach ($ROLE in $ROLES) {
    Write-Host "   Granting $ROLE..." -ForegroundColor White
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
        --role="$ROLE" `
        --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $ROLE granted" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $ROLE may already be granted" -ForegroundColor Yellow
    }
}

# Step 9: Create terraform.tfvars entries
Write-Host "🔧 Step 9: Creating terraform.tfvars entries..." -ForegroundColor Yellow
$TFVARS_CONTENT = @"

# Google Cloud Configuration for AI Video Features
google_cloud_project_id = "$PROJECT_ID"
google_cloud_location = "$LOCATION"
google_cloud_service_account_email = "$SERVICE_ACCOUNT_EMAIL"

# OpenAI Configuration (you need to add your actual API key)
openai_api_key = "sk-your-actual-openai-api-key"

"@

$TFVARS_FILE = "terraform/terraform.tfvars"
if (Test-Path $TFVARS_FILE) {
    Write-Host "⚠️  terraform.tfvars already exists. Please add these variables manually:" -ForegroundColor Yellow
    Write-Host $TFVARS_CONTENT -ForegroundColor Cyan
} else {
    $TFVARS_CONTENT | Out-File -FilePath $TFVARS_FILE -Encoding UTF8
    Write-Host "✅ Created terraform.tfvars with Google Cloud configuration" -ForegroundColor Green
}

# Step 10: Verification
Write-Host "🔧 Step 10: Verifying setup..." -ForegroundColor Yellow

# Check if service account exists
$SA_EXISTS = gcloud iam service-accounts list --filter="email:$SERVICE_ACCOUNT_EMAIL" --format="value(email)" --quiet
if ($SA_EXISTS) {
    Write-Host "✅ Service account verified: $SA_EXISTS" -ForegroundColor Green
} else {
    Write-Host "❌ Service account not found" -ForegroundColor Red
}

# Check if APIs are enabled
$AI_PLATFORM_ENABLED = gcloud services list --enabled --filter="name:aiplatform.googleapis.com" --format="value(name)" --quiet
if ($AI_PLATFORM_ENABLED) {
    Write-Host "✅ Vertex AI API enabled" -ForegroundColor Green
} else {
    Write-Host "❌ Vertex AI API not enabled" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Google Cloud setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Add your OpenAI API key to terraform.tfvars" -ForegroundColor White
Write-Host "   2. Run: terraform apply" -ForegroundColor White
Write-Host "   3. Test AI video generation in your Vue app" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Useful links:" -ForegroundColor Cyan
Write-Host "   - Vertex AI Console: https://console.cloud.google.com/vertex-ai" -ForegroundColor White
Write-Host "   - IAM Admin: https://console.cloud.google.com/iam-admin" -ForegroundColor White
Write-Host "   - Workload Identity: https://console.cloud.google.com/iam-admin/workload-identity-pools" -ForegroundColor White 