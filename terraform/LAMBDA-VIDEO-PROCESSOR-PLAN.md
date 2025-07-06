# Lambda Video Processor - Terraform Deployment Plan

## Current Infrastructure Context

### Existing Setup (from `main-simple` workspace):

- **44 resources** in active use
- **S3 bucket**: `aws_s3_bucket.video_bucket` (existing)
- **DynamoDB table**: `aws_dynamodb_table.video_metadata` (existing)
- **Lambda execution role**: `aws_iam_role.lambda_execution_role` (existing)
- **Lambda policy**: `aws_iam_role_policy.lambda_policy` (existing)
- **Existing Lambda functions**: `video_metadata_api` and `admin_api` (unused for Railway)

## Integration Strategy

### Reuse Existing Infrastructure ✅

Since you already have Lambda infrastructure in place (even though you use Railway for API), we can:

1. **Reuse existing IAM role** (`lambda_execution_role`)
2. **Reuse existing S3 bucket** (`video_bucket`)
3. **Reuse existing DynamoDB table** (`video_metadata`)
4. **Add new Lambda function** for video processing

### New Resources Needed:

- 1 new Lambda function (`video_processor`)
- 1 Lambda layer for FFmpeg binaries
- Updates to existing IAM policy for additional permissions

## Terraform Implementation

### 1. Add Lambda Layer for FFmpeg

```hcl
# Add to main.tf

# Lambda layer with FFmpeg binaries
resource "aws_lambda_layer_version" "ffmpeg_layer" {
  filename         = "ffmpeg-layer.zip"
  layer_name       = "${var.project_name}-ffmpeg-layer"
  source_code_hash = data.archive_file.ffmpeg_layer_zip.output_base64sha256

  compatible_runtimes = ["python3.11", "python3.10"]
  description         = "FFmpeg binaries for video processing"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create FFmpeg layer deployment package
data "archive_file" "ffmpeg_layer_zip" {
  type        = "zip"
  output_path = "ffmpeg-layer.zip"
  source_dir  = "${path.module}/layers/ffmpeg"
}
```

### 2. Add Video Processing Lambda Function

```hcl
# Add to main.tf

# Lambda function for video processing
resource "aws_lambda_function" "video_processor" {
  filename         = "video_processor.zip"
  function_name    = "${var.project_name}-video-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "video_processor.lambda_handler"
  runtime         = "python3.11"
  timeout         = 900    # 15 minutes (max for Lambda)
  memory_size     = 3008   # Maximum memory for video processing

  # Use FFmpeg layer
  layers = [aws_lambda_layer_version.ffmpeg_layer.arn]

  source_code_hash = data.archive_file.video_processor_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.video_metadata.name
      S3_BUCKET_NAME     = aws_s3_bucket.video_bucket.bucket
      AWS_REGION         = var.aws_region
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create video processor deployment package
data "archive_file" "video_processor_zip" {
  type        = "zip"
  output_path = "video_processor.zip"
  source_dir  = "${path.module}/lambda-video-processor"
}
```

### 3. Update Existing IAM Policy

```hcl
# Update existing aws_iam_role_policy.lambda_policy to include:

# In the existing policy document, add Lambda invoke permissions:
{
  Effect = "Allow"
  Action = [
    "lambda:InvokeFunction"
  ]
  Resource = [
    aws_lambda_function.video_processor.arn
  ]
}

# Also add any additional S3 permissions needed for video processing:
{
  Effect = "Allow"
  Action = [
    "s3:GetObjectVersion",
    "s3:GetObjectVersionAcl"
  ]
  Resource = [
    "${aws_s3_bucket.video_bucket.arn}/*"
  ]
}
```

## Directory Structure Setup

### Create Lambda Function Directory:

```
terraform/
├── lambda-video-processor/          # NEW
│   ├── video_processor.py           # Main Lambda function
│   ├── requirements.txt             # Python dependencies
│   └── utils/
│       ├── __init__.py
│       ├── video_processing.py      # Video processing logic
│       └── s3_helpers.py            # S3 utilities
├── layers/                          # NEW
│   └── ffmpeg/
│       └── bin/
│           ├── ffmpeg               # FFmpeg binary
│           └── ffprobe              # FFprobe binary
├── lambda/                          # EXISTING (unused)
├── admin-lambda/                    # EXISTING (unused)
└── main.tf                          # Updated
```

## Railway Integration

### Update Railway Backend to Trigger Lambda:

```python
# In Railway backend/main.py
import boto3

@router.post("/upload/complete")
async def complete_upload(request: CompleteUploadRequest):
    # Existing DynamoDB job creation (unchanged)
    dynamodb_service.create_job_entry(...)

    # NEW: Trigger Lambda instead of Celery
    if use_lambda_processing(request):
        await trigger_lambda_processing(request)
    else:
        # Fallback to existing Celery processing
        process_video_task.delay(...)

    return JobCreatedResponse(...)

async def trigger_lambda_processing(request: CompleteUploadRequest):
    """Trigger AWS Lambda for video processing"""
    lambda_client = boto3.client('lambda')

    payload = {
        's3_bucket': settings.AWS_BUCKET_NAME,
        's3_key': request.s3_key,
        'job_id': request.job_id,
        'cutting_options': request.cutting_options.dict() if request.cutting_options else None,
        'text_input': request.text_input.dict() if request.text_input else None,
        'user_id': request.user_id
    }

    response = lambda_client.invoke(
        FunctionName=f"{settings.PROJECT_NAME}-video-processor",
        InvocationType='Event',  # Async invocation
        Payload=json.dumps(payload)
    )

    print(f"Lambda triggered for job {request.job_id}")

def use_lambda_processing(request: CompleteUploadRequest) -> bool:
    """Determine whether to use Lambda or Celery processing"""
    # Start with file size-based routing
    # Future: Add user preferences, processing complexity, etc.
    return True  # Use Lambda for all processing
```

## Lambda Function Implementation

### video_processor.py Structure:

```python
import json
import boto3
import tempfile
import subprocess
import os
from datetime import datetime, timezone

def lambda_handler(event, context):
    """
    AWS Lambda handler for video processing
    """
    try:
        # Extract parameters from event
        s3_bucket = event['s3_bucket']
        s3_key = event['s3_key']
        job_id = event['job_id']
        cutting_options = event.get('cutting_options')
        text_input = event.get('text_input')
        user_id = event.get('user_id', 'anonymous')

        # Update job status to PROCESSING
        update_job_status(job_id, "PROCESSING")

        # Process video
        result = process_video(s3_bucket, s3_key, job_id, cutting_options, text_input)

        # Update job status to COMPLETED
        update_job_status(job_id, "COMPLETED", result['output_s3_keys'])

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Video processing completed successfully',
                'job_id': job_id,
                'segments_created': len(result['output_s3_keys'])
            })
        }

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        update_job_status(job_id, "FAILED", error_message=str(e))

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'job_id': job_id
            })
        }






def process_video(s3_bucket, s3_key, job_id, cutting_options, text_input):
    """
    Main video processing logic (migrated from Railway Celery task)
    """
    s3_client = boto3.client('s3')

    with tempfile.TemporaryDirectory() as temp_dir:
        # Download video from S3
        input_path = os.path.join(temp_dir, 'input.mp4')
        s3_client.download_file(s3_bucket, s3_key, input_path)

        # Process video (same logic as current Celery task)
        segments = create_video_segments(input_path, cutting_options, text_input)

        # Upload segments back to S3
        output_s3_keys = []
        for i, segment_path in enumerate(segments):
            output_key = f"processed/{job_id}/segment_{i:03d}.mp4"
            s3_client.upload_file(segment_path, s3_bucket, output_key)
            output_s3_keys.append(output_key)

    return {'output_s3_keys': output_s3_keys}
```

## Deployment Steps

### 1. Prepare Lambda Layer (FFmpeg):

```bash
# Create FFmpeg layer directory
mkdir -p terraform/layers/ffmpeg/bin

# Download FFmpeg static builds for Lambda
cd terraform/layers/ffmpeg/bin
wget https://github.com/vot/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-linux-64.zip
wget https://github.com/vot/ffbinaries-prebuilt/releases/download/v4.4.1/ffprobe-4.4.1-linux-64.zip
unzip ffmpeg-4.4.1-linux-64.zip
unzip ffprobe-4.4.1-linux-64.zip
chmod +x ffmpeg ffprobe
rm *.zip
```

### 2. Create Lambda Function Code:

```bash
mkdir -p terraform/lambda-video-processor
# Copy video processing logic from Railway backend
# Adapt for Lambda environment
```

### 3. Deploy with Terraform:

```bash
cd terraform
terraform workspace select main-simple
terraform plan    # Should show +2 resources (function + layer)
terraform apply
```

## Testing Strategy

### 1. Test Lambda Function Directly:

```bash
# Create test event
aws lambda invoke \
  --function-name easy-video-share-video-processor \
  --payload file://test-event.json \
  response.json
```

### 2. Test Railway Integration:

```bash
# Upload video through Railway API
# Verify Lambda gets triggered
# Check CloudWatch logs
```

## Benefits of This Approach

### Infrastructure Benefits:

- **Reuses existing resources** (no infrastructure duplication)
- **Minimal new resources** (+2 to existing 44)
- **Fits existing workspace strategy** (`main-simple`)
- **Leverages existing IAM roles and policies**

### Operational Benefits:

- **No S3 data transfer costs** (Lambda ↔ S3 in same region)
- **Serverless scaling** (parallel processing)
- **Railway focuses on API** (its strength)
- **Lambda handles compute** (its strength)

### Cost Benefits:

- **Pay-per-execution** (vs. continuous Railway compute)
- **No bandwidth charges** for video processing
- **Optimal resource utilization**

## Migration Path

### Phase 1: Parallel Deployment

- Deploy Lambda alongside existing Celery
- Route based on file size or user preference
- Gradual migration of processing load

### Phase 2: Full Migration

- Route all processing to Lambda
- Keep Celery as emergency fallback
- Monitor performance and costs

### Phase 3: Optimization

- Remove Celery dependencies from Railway
- Optimize Lambda memory/timeout settings
- Add advanced features (Step Functions, etc.)

## Workspace Impact

This addition will change your `main-simple` workspace from:

- **Current**: 44 resources
- **After**: 46 resources (+Lambda function, +Lambda layer)

This is a minimal, clean addition that fits perfectly with your existing infrastructure strategy.

---

_Lambda Video Processor Plan for main-simple Workspace - Date: 2025-07-06_
