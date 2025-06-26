# Google Cloud Setup Guide for AI Video Generation

## Prerequisites

- Google Cloud account (free tier available)
- Billing enabled on your Google Cloud project

## Step 1: Create or Select Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** (you'll need this for `vertex_ai_project_id`)

## Step 2: Enable Required APIs

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable these APIs:
   - **Vertex AI API**
   - **Cloud Storage API** (if not already enabled)

## Step 3: Create Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name: `ai-video-generator`
4. Description: `Service account for AI video generation`
5. Click "Create and Continue"

## Step 4: Assign Permissions

1. Add these roles to the service account:

   - **Vertex AI User**
   - **Storage Object Viewer** (for reading audio files)
   - **Storage Object Creator** (for saving generated videos)

2. Click "Continue" and then "Done"

## Step 5: Create and Download JSON Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Click "Create"
6. The JSON file will download automatically

## Step 6: Configure Terraform

1. Open the downloaded JSON file
2. Copy the **entire** JSON content
3. Open `terraform/terraform.tfvars`
4. Replace `PASTE_YOUR_GOOGLE_CLOUD_SERVICE_ACCOUNT_JSON_HERE` with the JSON content
5. Replace `YOUR_GOOGLE_CLOUD_PROJECT_ID` with your actual project ID

## Step 7: Update OpenAI API Key

1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Replace the placeholder in `terraform.tfvars`

## Step 8: Deploy Infrastructure

```bash
cd terraform
terraform apply -auto-approve
```

## Example terraform.tfvars Configuration

```hcl
# Google Cloud Configuration
google_cloud_credentials_json = "{\"type\": \"service_account\", \"project_id\": \"your-project-id\", \"private_key_id\": \"abc123...\", \"private_key\": \"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n\", \"client_email\": \"ai-video-generator@your-project-id.iam.gserviceaccount.com\", \"client_id\": \"123456789\", \"auth_uri\": \"https://accounts.google.com/o/oauth2/auth\", \"token_uri\": \"https://oauth2.googleapis.com/token\", \"auth_provider_x509_cert_url\": \"https://www.googleapis.com/oauth2/v1/certs\", \"client_x509_cert_url\": \"https://www.googleapis.com/robot/v1/metadata/x509/ai-video-generator%40your-project-id.iam.gserviceaccount.com\"}"

# OpenAI Configuration
openai_api_key = "sk-your-actual-openai-api-key"

# Vertex AI Configuration
vertex_ai_project_id = "your-project-id"
vertex_ai_location = "us-central1"
```

## Troubleshooting

### Common Issues:

1. **"Permission denied" errors**: Make sure the service account has the correct roles
2. **"API not enabled" errors**: Ensure Vertex AI API is enabled
3. **"Invalid credentials" errors**: Check that the JSON key is copied correctly
4. **"Project not found" errors**: Verify the project ID is correct

### Cost Considerations:

- Vertex AI Veo 2: ~$0.05 per second of generated video
- OpenAI API: ~$0.03 per 1K tokens
- Estimated cost per 30-second video: $1.50-3.00

### Security Notes:

- Never commit `terraform.tfvars` to version control
- The service account has minimal required permissions
- Consider using Google Cloud Secret Manager for production
