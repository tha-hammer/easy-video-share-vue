# Modern Google Cloud Setup Guide (No JSON Keys!)

## Overview

This guide uses modern Google Cloud authentication methods:

- **Application Default Credentials (ADC)** for local development
- **Service Account Impersonation** for cross-cloud authentication
- **Workload Identity** for production (AWS Lambda to Google Cloud)

## Prerequisites

- Google Cloud account with billing enabled
- AWS account (for Lambda functions)
- Google Cloud CLI (gcloud) installed

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your **Project ID** (e.g., `my-ai-video-project`)

## Step 2: Enable Required APIs

```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iamcredentials.googleapis.com
```

## Step 3: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create ai-video-generator \
  --display-name="AI Video Generator" \
  --description="Service account for AI video generation"

# Get the service account email
SERVICE_ACCOUNT_EMAIL="ai-video-generator@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

## Step 4: Grant Permissions

```bash
# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"

# Grant Storage permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectCreator"

# Grant IAM permissions for impersonation
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountTokenCreator"
```

## Step 5: Configure AWS for Cross-Cloud Authentication

### Option A: Using AWS IAM Role (Recommended for Production)

1. **Create AWS IAM Role for Lambda**:

```bash
# Create trust policy for Google Cloud
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "accounts.google.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "accounts.google.com:aud": "$SERVICE_ACCOUNT_EMAIL"
        }
      }
    }
  ]
}
EOF
```

2. **Create IAM Role**:

```bash
aws iam create-role \
  --role-name GoogleCloudAIVideoRole \
  --assume-role-policy-document file://trust-policy.json
```

### Option B: Using Application Default Credentials (Development)

For local development, you can use ADC:

```bash
# Set up ADC
gcloud auth application-default login

# Set the project
gcloud config set project YOUR_PROJECT_ID
```

## Step 6: Configure Terraform

Update your `terraform/terraform.tfvars`:

```hcl
# Google Cloud Configuration (Modern Authentication)
google_cloud_project_id = "your-project-id"
google_cloud_location = "us-central1"
google_cloud_service_account_email = "ai-video-generator@your-project-id.iam.gserviceaccount.com"

# OpenAI Configuration
openai_api_key = "sk-your-actual-openai-api-key"

# Optional: Legacy JSON key (only if you prefer JSON keys)
# google_cloud_credentials_json = "{\"type\": \"service_account\", ...}"
```

## Step 7: Update Environment Variables

Add these to your `.env` file:

```bash
# Google Cloud Configuration
VITE_GOOGLE_CLOUD_PROJECT_ID=your-project-id
VITE_GOOGLE_CLOUD_LOCATION=us-central1
VITE_GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL=ai-video-generator@your-project-id.iam.gserviceaccount.com

# OpenAI Configuration
VITE_OPENAI_API_KEY=sk-your-actual-openai-api-key
```

## Step 8: Deploy Infrastructure

```bash
cd terraform
terraform apply -auto-approve
```

## Step 9: Test Authentication

Create a test script to verify authentication:

```javascript
// test-auth.js
const { GoogleAuth } = require('google-auth-library')
const { VertexAI } = require('@google-cloud/vertexai')

async function testAuth() {
  try {
    const auth = new GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform'],
    })

    const client = await auth.getClient()
    const projectId = await auth.getProjectId()

    console.log('✅ Authentication successful!')
    console.log('Project ID:', projectId)

    const vertexAI = new VertexAI({
      project: projectId,
      location: 'us-central1',
    })

    console.log('✅ Vertex AI initialized successfully!')
  } catch (error) {
    console.error('❌ Authentication failed:', error)
  }
}

testAuth()
```

## Troubleshooting

### Common Issues:

1. **"Permission denied" errors**:

   - Ensure service account has correct roles
   - Check project ID is correct
   - Verify API is enabled

2. **"Authentication failed" errors**:

   - Run `gcloud auth application-default login`
   - Check service account email is correct
   - Verify IAM permissions

3. **"API not enabled" errors**:
   - Enable Vertex AI API: `gcloud services enable aiplatform.googleapis.com`

### Cost Optimization:

- Use Vertex AI quotas to limit usage
- Set up billing alerts
- Monitor usage in Google Cloud Console

### Security Best Practices:

- Use least privilege principle
- Rotate service account keys regularly
- Monitor access logs
- Use Workload Identity for production

## Next Steps

1. Deploy your infrastructure: `terraform apply`
2. Test the AI video generation endpoint
3. Monitor costs and usage
4. Set up production Workload Identity if needed

## Support

- [Google Cloud IAM Documentation](https://cloud.google.com/iam/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
