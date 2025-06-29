# Sprint 4 Vertex AI Migration Guide

## Overview

This guide helps you migrate from the Google AI SDK to Vertex AI for Sprint 4 implementation. Google has moved Gemini access to Vertex AI, which provides better enterprise features and integration.

## Migration Steps

### 1. Update Dependencies

The `requirements.txt` has been updated to use the new Vertex AI SDK:

```python
# OLD: google-generativeai==0.3.2
# NEW: google-genai==0.3.0
```

Install the new dependency:

```bash
pip install -r requirements.txt
```

### 2. Update Environment Variables

**Old `.env` configuration:**

```env
GEMINI_API_KEY=your_api_key_here
```

**New `.env` configuration:**

```env
GOOGLE_CLOUD_PROJECT=864074432175
GOOGLE_CLOUD_LOCATION=us-central1
```

### 3. Authentication Setup

Vertex AI uses Google Cloud authentication instead of API keys.

#### Option A: User Authentication (Development)

```bash
# Install Google Cloud CLI
# Windows: https://cloud.google.com/sdk/docs/install
# macOS: brew install google-cloud-sdk
# Linux: Follow installation guide

# Authenticate with your Google account
gcloud auth application-default login

# Set your project
gcloud config set project 864074432175
```

#### Option B: Service Account (Production)

```bash
# Create service account
gcloud iam service-accounts create vertex-ai-service

# Grant necessary roles
gcloud projects add-iam-policy-binding 864074432175 \
    --member="serviceAccount:vertex-ai-service@864074432175.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create vertex-ai-key.json \
    --iam-account=vertex-ai-service@864074432175.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/vertex-ai-key.json"
```

### 4. Enable Required APIs

Enable Vertex AI API in your Google Cloud project:

```bash
gcloud services enable aiplatform.googleapis.com
```

Or via Google Cloud Console:

1. Go to [APIs & Services](https://console.cloud.google.com/apis/dashboard)
2. Click "Enable APIs and Services"
3. Search for "Vertex AI API"
4. Click "Enable"

### 5. Test the Connection

Run the updated test script:

```bash
cd backend
python test_gemini_simple.py
```

Expected output:

```
Simple Vertex AI Connection Test
========================================
✅ Project ID found: 864074432175
✅ Location: us-central1
✅ Vertex AI client configured successfully
🔄 Testing API call...
✅ API call successful!
Response: API test successful

🚀 Ready for Sprint 4 LLM integration with Vertex AI!
```

## Code Changes Made

### 1. LLM Service (`llm_service_vertexai.py`)

**Key Changes:**

- Uses `google.genai.Client()` instead of `google.generativeai`
- Authentication via Google Cloud credentials
- Model: `gemini-2.5-flash` instead of `gemini-pro`

### 2. Configuration (`config.py`)

**Updated settings:**

```python
# OLD
GEMINI_API_KEY: Optional[str] = None

# NEW
GOOGLE_CLOUD_PROJECT: Optional[str] = None
GOOGLE_CLOUD_LOCATION: str = "us-central1"
```

### 3. Video Processing

Updated import in `video_processing_utils_sprint4.py`:

```python
from llm_service_vertexai import generate_text_variations
```

## Troubleshooting

### Authentication Errors

**Error:** `DefaultCredentialsError: Could not automatically determine credentials`

**Solution:**

```bash
gcloud auth application-default login
```

### Permission Errors

**Error:** `PermissionDenied: User does not have permission to access project`

**Solution:**

1. Ensure you have the "Vertex AI User" role
2. Check project permissions in IAM console
3. Verify project ID is correct

### API Not Enabled

**Error:** `Service 'aiplatform.googleapis.com' is not enabled`

**Solution:**

```bash
gcloud services enable aiplatform.googleapis.com
```

### Region Availability

**Error:** `Model not available in region`

**Solution:**
Try different regions in your `.env`:

```env
GOOGLE_CLOUD_LOCATION=us-central1  # or us-east1, europe-west1
```

## Verification Checklist

- [ ] ✅ Updated `requirements.txt` and installed `google-genai`
- [ ] ✅ Updated `.env` with `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`
- [ ] ✅ Authenticated with `gcloud auth application-default login`
- [ ] ✅ Enabled Vertex AI API with `gcloud services enable aiplatform.googleapis.com`
- [ ] ✅ Tested connection with `python test_gemini_simple.py`
- [ ] ✅ Sprint 4 LLM service working correctly

## Next Steps

Once Vertex AI is working:

1. **Test Sprint 4 functionality:**

   ```bash
   python test_sprint4_llm.py
   python test_sprint4_e2e.py
   ```

2. **Run actual video processing:**

   ```bash
   # Start Redis and Celery
   .\scripts\start-redis.ps1
   .\scripts\start-worker.ps1

   # Start API server
   python main.py
   ```

3. **Test with real video:**
   Upload a video through the API with `BASE_VARY` strategy to see LLM-generated text variations.

## Benefits of Vertex AI Migration

- **Better Authentication:** Uses Google Cloud IAM instead of API keys
- **Enterprise Features:** Enhanced security, monitoring, and scaling
- **Improved Reliability:** Better SLA and support
- **Advanced Models:** Access to latest Gemini models and features
- **Integration:** Better integration with other Google Cloud services
