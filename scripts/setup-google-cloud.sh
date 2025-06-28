#!/bin/bash

# Google Cloud Setup Script for Easy Video Share AI Features
# Run this script to set up Workload Identity Federation and required services

echo "🚀 Setting up Google Cloud for Easy Video Share AI Video Features"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

GCLOUD_VERSION=$(gcloud version --format="value(basic.version)" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Google Cloud CLI found: $GCLOUD_VERSION"
else
    echo "❌ Google Cloud CLI not working properly"
    exit 1
fi

# Configuration
PROJECT_ID="easy-video-share"
LOCATION="us-central1"
SERVICE_ACCOUNT_NAME="easy-video-share-sa"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
WORKLOAD_IDENTITY_POOL="easy-video-share"
WORKLOAD_IDENTITY_PROVIDER="easy-video-share"
AWS_ACCOUNT_ID="571960159088"

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Location: $LOCATION"
echo "   Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "   AWS Account ID: $AWS_ACCOUNT_ID"
echo ""

# Step 1: Set the project
echo "🔧 Step 1: Setting Google Cloud project..."
gcloud config set project $PROJECT_ID
if [ $? -ne 0 ]; then
    echo "❌ Failed to set project. Please check your authentication."
    exit 1
fi
echo "✅ Project set to: $PROJECT_ID"

# Step 2: Enable required APIs
echo "🔧 Step 2: Enabling required APIs..."
APIS=(
    "aiplatform.googleapis.com"
    "storage.googleapis.com"
    "iamcredentials.googleapis.com"
    "iam.googleapis.com"
)

for API in "${APIS[@]}"; do
    echo "   Enabling $API..."
    gcloud services enable $API --quiet
    if [ $? -eq 0 ]; then
        echo "   ✅ $API enabled"
    else
        echo "   ⚠️  $API may already be enabled or failed"
    fi
done

# Step 3: Create Workload Identity Pool
echo "🔧 Step 3: Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create $WORKLOAD_IDENTITY_POOL --location=global --quiet
if [ $? -eq 0 ]; then
    echo "✅ Workload Identity Pool created: $WORKLOAD_IDENTITY_POOL"
else
    echo "⚠️  Workload Identity Pool may already exist"
fi

# Step 4: Create Workload Identity Provider
echo "🔧 Step 4: Creating Workload Identity Provider..."
gcloud iam workload-identity-pools providers create-aws $WORKLOAD_IDENTITY_PROVIDER \
    --workload-identity-pool=$WORKLOAD_IDENTITY_POOL \
    --account-id=$AWS_ACCOUNT_ID \
    --role-session-name=lambda-session \
    --quiet
if [ $? -eq 0 ]; then
    echo "✅ Workload Identity Provider created"
else
    echo "⚠️  Workload Identity Provider may already exist"
fi

# Step 5: Create Service Account
echo "🔧 Step 5: Creating Service Account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Easy Video Share Service Account" \
    --quiet
if [ $? -eq 0 ]; then
    echo "✅ Service Account created: $SERVICE_ACCOUNT_EMAIL"
else
    echo "⚠️  Service Account may already exist"
fi

# Step 6: Get Project Number
echo "🔧 Step 6: Getting Project Number..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
if [ $? -eq 0 ]; then
    echo "✅ Project Number: $PROJECT_NUMBER"
else
    echo "❌ Failed to get project number"
    exit 1
fi

# Step 7: Grant Workload Identity User role
echo "🔧 Step 7: Granting Workload Identity User role..."
MEMBER="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$WORKLOAD_IDENTITY_POOL/attribute.service_account/$SERVICE_ACCOUNT_EMAIL"

gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="$MEMBER" \
    --quiet
if [ $? -eq 0 ]; then
    echo "✅ Workload Identity User role granted"
else
    echo "⚠️  Role may already be granted"
fi

# Step 8: Grant required roles to service account
echo "🔧 Step 8: Granting required roles to service account..."
ROLES=(
    "roles/aiplatform.user"
    "roles/storage.objectViewer"
    "roles/storage.objectCreator"
)

for ROLE in "${ROLES[@]}"; do
    echo "   Granting $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$ROLE" \
        --quiet
    if [ $? -eq 0 ]; then
        echo "   ✅ $ROLE granted"
    else
        echo "   ⚠️  $ROLE may already be granted"
    fi
done

# Step 9: Create terraform.tfvars entries
echo "🔧 Step 9: Creating terraform.tfvars entries..."
TFVARS_CONTENT="# Google Cloud Configuration for AI Video Features
google_cloud_project_id = \"$PROJECT_ID\"
google_cloud_location = \"$LOCATION\"
google_cloud_service_account_email = \"$SERVICE_ACCOUNT_EMAIL\"

# OpenAI Configuration (you need to add your actual API key)
openai_api_key = \"YOUR_OPENAI_API_KEY_HERE\"
"

TFVARS_FILE="terraform/terraform.tfvars"
if [ -f "$TFVARS_FILE" ]; then
    echo "⚠️  terraform.tfvars already exists. Please add these variables manually:"
    echo "$TFVARS_CONTENT"
else
    echo "$TFVARS_CONTENT" > "$TFVARS_FILE"
    echo "✅ Created terraform.tfvars with Google Cloud configuration"
fi

# Step 10: Verification
echo "🔧 Step 10: Verifying setup..."

# Check if service account exists
SA_EXISTS=$(gcloud iam service-accounts list --filter="email:$SERVICE_ACCOUNT_EMAIL" --format="value(email)" --quiet)
if [ -n "$SA_EXISTS" ]; then
    echo "✅ Service account verified: $SA_EXISTS"
else
    echo "❌ Service account not found"
fi

# Check if APIs are enabled
AI_PLATFORM_ENABLED=$(gcloud services list --enabled --filter="name:aiplatform.googleapis.com" --format="value(name)" --quiet)
if [ -n "$AI_PLATFORM_ENABLED" ]; then
    echo "✅ Vertex AI API enabled"
else
    echo "❌ Vertex AI API not enabled"
fi

echo ""
echo "🎉 Google Cloud setup completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Run: terraform apply"
echo "   2. Test AI video generation in your Vue app"
echo ""
echo "🔗 Useful links:"
echo "   - Vertex AI Console: https://console.cloud.google.com/vertex-ai"
echo "   - IAM Admin: https://console.cloud.google.com/iam-admin"
echo "   - Workload Identity: https://console.cloud.google.com/iam-admin/workload-identity-pools" 