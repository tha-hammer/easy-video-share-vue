# Workload Identity Federation Setup Guide

## AWS Lambda ↔ Google Cloud Vertex AI

This guide shows how to set up Workload Identity Federation so your AWS Lambda functions can securely access Google Cloud Vertex AI without sharing long-lived credentials.

## Prerequisites

- Google Cloud project with Vertex AI API enabled
- AWS account with Lambda functions
- Google Cloud CLI (gcloud) installed and authenticated
- AWS CLI installed and configured

## Step 1: Verify Your ADC File

First, let's check your ADC file:

```bash
# Check if ADC file exists
ls -la ~/.config/gcloud/application_default_credentials.json

# On Windows:
dir "%APPDATA%\gcloud\application_default_credentials.json"

# View the structure (don't share the actual content)
cat ~/.config/gcloud/application_default_credentials.json | jq 'keys'
```

Your ADC file should contain:

- `client_id`
- `client_secret`
- `refresh_token`
- `type` (should be "authorized_user")

## Step 2: Create Workload Identity Pool

```bash
# Set your project
export PROJECT_ID="easy-video-share"
export POOL_ID="easy-video-share"
export PROVIDER_ID="easy-video-share"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create $POOL_ID \
  --project=$PROJECT_ID \
  --location="global" \
  --display-name="AWS Lambda Pool"

# Create Workload Identity Provider for AWS
gcloud iam workload-identity-pools providers create-aws $PROVIDER_ID \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool=$POOL_ID \
  --account-id="571960159088" \
  --role-session-name="lambda-session"
```

## Step 3: Create Service Account

```bash
# Create service account for Lambda
gcloud iam service-accounts create easy-video-share-sa \
  --project=$PROJECT_ID \
  --display-name="Easy Video Share Service Account"

# Get the service account email
export SERVICE_ACCOUNT_EMAIL="easy-vide-share-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

## Step 4: Grant Permissions

```bash
# Allow AWS to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/$POOL_ID/attribute.service_account/$SERVICE_ACCOUNT_EMAIL"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"

# Grant Storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectCreator"
```

## Step 5: Update Terraform Configuration

Update your `terraform/terraform.tfvars`:

```hcl
# Google Cloud Configuration (Workload Identity Federation)
google_cloud_project_id = "easy-video-share"
google_cloud_location = "us-central1"
google_cloud_service_account_email = "lambda-vertex-ai@easy-video-share.iam.gserviceaccount.com"

# Workload Identity Federation
workload_identity_pool_id = "aws-lambda-pool"
workload_identity_provider_id = "aws-provider"

# OpenAI Configuration
openai_api_key = "sk-your-actual-openai-api-key"
```

## Step 6: Update Lambda Function

The Lambda function will use the Google Auth library to automatically handle Workload Identity Federation:

```javascript
// In your Lambda function
const { GoogleAuth } = require('google-auth-library')
const { VertexAI } = require('@google-cloud/vertexai')

async function initializeGoogleCloud() {
  try {
    // This will automatically use Workload Identity Federation
    // when running in AWS Lambda
    const auth = new GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform'],
      // The library will automatically detect AWS environment
      // and use Workload Identity Federation
    })

    const vertexAI = new VertexAI({
      project: process.env.GOOGLE_CLOUD_PROJECT_ID,
      location: process.env.GOOGLE_CLOUD_LOCATION,
      googleAuth: auth,
    })

    console.log('✅ Google Cloud initialized with Workload Identity Federation')
    return vertexAI
  } catch (error) {
    console.error('❌ Error initializing Google Cloud:', error)
    throw error
  }
}
```

## Step 7: Set Lambda Environment Variables

Add these environment variables to your Lambda function:

```bash
GOOGLE_CLOUD_PROJECT_ID=easy-video-share
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL=lambda-vertex-ai@easy-video-share.iam.gserviceaccount.com
WORKLOAD_IDENTITY_POOL_ID=aws-lambda-pool
WORKLOAD_IDENTITY_PROVIDER_ID=aws-provider
```

## Step 8: Test the Setup

Create a test script to verify the setup:

```javascript
// test-workload-identity.js
const { GoogleAuth } = require('google-auth-library')
const { VertexAI } = require('@google-cloud/vertexai')

async function testWorkloadIdentity() {
  try {
    console.log('🔐 Testing Workload Identity Federation...')

    const auth = new GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform'],
    })

    // Get credentials
    const client = await auth.getClient()
    const projectId = await auth.getProjectId()

    console.log('✅ Authentication successful!')
    console.log('Project ID:', projectId)

    // Test Vertex AI access
    const vertexAI = new VertexAI({
      project: projectId,
      location: 'us-central1',
    })

    console.log('✅ Vertex AI initialized successfully!')

    // Test a simple API call
    const model = vertexAI.getGenerativeModel({ model: 'gemini-pro' })
    console.log('✅ Model access successful!')
  } catch (error) {
    console.error('❌ Test failed:', error)
  }
}

testWorkloadIdentity()
```

## Step 9: Deploy and Test

```bash
# Deploy your infrastructure
cd terraform
terraform apply -auto-approve

# Test the Lambda function
aws lambda invoke \
  --function-name your-ai-video-function \
  --payload '{"test": "workload-identity"}' \
  response.json

cat response.json
```

## Troubleshooting

### Common Issues:

1. **"Permission denied" errors**:

   ```bash
   # Check if service account has correct roles
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --format="table(bindings.role)" \
     --filter="bindings.members:$SERVICE_ACCOUNT_EMAIL"
   ```

2. **"Workload Identity Pool not found"**:

   ```bash
   # List pools
   gcloud iam workload-identity-pools list --location=global
   ```

3. **"AWS account not configured"**:
   ```bash
   # Get your AWS account ID
   aws sts get-caller-identity --query Account --output text
   ```

### Verification Commands:

```bash
# Check Workload Identity Pool
gcloud iam workload-identity-pools describe $POOL_ID --location=global

# Check Workload Identity Provider
gcloud iam workload-identity-pools providers describe $PROVIDER_ID \
  --workload-identity-pool=$POOL_ID \
  --location=global

# Check service account permissions
gcloud iam service-accounts get-iam-policy $SERVICE_ACCOUNT_EMAIL
```

## Security Benefits

✅ **No long-lived credentials** - Tokens are automatically rotated  
✅ **Fine-grained permissions** - Only the specific Lambda can access  
✅ **Audit trail** - All access is logged  
✅ **Automatic token refresh** - No manual credential management

## Cost Considerations

- Workload Identity Federation is **free**
- Only pay for Vertex AI usage
- No additional charges for cross-cloud authentication

## Next Steps

1. Run the setup commands above
2. Update your Terraform configuration
3. Deploy the infrastructure
4. Test the Lambda function
5. Monitor logs for any authentication issues

Your AWS Lambda functions can now securely access Google Cloud Vertex AI using modern, secure authentication!
