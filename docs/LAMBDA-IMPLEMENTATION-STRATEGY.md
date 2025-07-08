# Lambda Video Processor - Step-by-Step Implementation Strategy

## Development Philosophy: Test Early, Test Often

The key is to build and validate each component in isolation before integrating them together. This prevents the "big bang" deployment problem where everything breaks at once.

## Phase 1: Foundation Testing (1-2 hours)

### Step 1A: Test Lambda Infrastructure Only
**Goal**: Verify AWS Lambda can be deployed and invoked
**Deliverable**: Simple "Hello World" Lambda function

```bash
# Create minimal test function
mkdir -p terraform/lambda-video-processor
echo 'def lambda_handler(event, context): 
    return {"statusCode": 200, "body": "Hello from Lambda"}' > terraform/lambda-video-processor/test_handler.py

# Add to terraform/main.tf (minimal version)
resource "aws_lambda_function" "video_processor_test" {
  filename         = "test_processor.zip"
  function_name    = "${var.project_name}-video-processor-test"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "test_handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 128
}

# Deploy and test
cd terraform
terraform workspace select main-simple
terraform plan    # Should show +1 resource
terraform apply
aws lambda invoke --function-name easy-video-share-video-processor-test response.json
cat response.json # Should show "Hello from Lambda"
```

**Success Criteria**: Lambda deploys, can be invoked, returns expected response
**If this fails**: Fix Terraform/AWS credentials before proceeding

### Step 1B: Test Railway → Lambda Communication
**Goal**: Verify Railway can trigger Lambda
**Deliverable**: Railway endpoint that calls Lambda

```python
# Add to Railway backend/main.py (temporary test endpoint)
@router.post("/test/lambda")
async def test_lambda_invoke():
    """Test endpoint to verify Lambda connectivity"""
    try:
        import boto3
        lambda_client = boto3.client('lambda')
        
        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='RequestResponse',  # Synchronous for testing
            Payload=json.dumps({"test": "data"})
        )
        
        return {
            "status": "success",
            "lambda_response": json.loads(response['Payload'].read()),
            "status_code": response['StatusCode']
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Test**: `POST /api/test/lambda` should return success
**Success Criteria**: Railway can successfully invoke Lambda and get response

## Phase 2: Video Processing Logic (2-3 hours)

### Step 2A: Test FFmpeg Layer Creation
**Goal**: Create and test FFmpeg layer without video processing
**Deliverable**: Lambda layer with FFmpeg that can run `ffmpeg -version`

```bash
# Download FFmpeg binaries for Lambda
mkdir -p terraform/layers/ffmpeg/bin
cd terraform/layers/ffmpeg/bin
wget https://github.com/vot/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-linux-64.zip
unzip ffmpeg-4.4.1-linux-64.zip
chmod +x ffmpeg
rm *.zip

# Test Lambda function with FFmpeg
echo 'import subprocess
def lambda_handler(event, context):
    try:
        result = subprocess.run(["/opt/bin/ffmpeg", "-version"], 
                               capture_output=True, text=True, timeout=10)
        return {
            "statusCode": 200, 
            "body": {"ffmpeg_available": result.returncode == 0, "version": result.stdout[:100]}
        }
    except Exception as e:
        return {"statusCode": 500, "body": {"error": str(e)}}' > terraform/lambda-video-processor/ffmpeg_test.py
```

**Test**: Invoke Lambda, should return FFmpeg version info
**Success Criteria**: FFmpeg runs successfully in Lambda environment

### Step 2B: Test S3 Video Download/Upload
**Goal**: Verify Lambda can download from S3 and upload results
**Deliverable**: Lambda that downloads a test video, checks it, uploads a copy

```python
# Test S3 operations in Lambda
import boto3
import tempfile
import os

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    
    try:
        # Test download
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'test_input.mp4')
            s3_client.download_file(
                event['s3_bucket'], 
                event['s3_key'], 
                input_path
            )
            
            # Verify file exists and get size
            file_size = os.path.getsize(input_path)
            
            # Test upload (copy with different name)
            output_key = f"test_output/{event['s3_key'].split('/')[-1]}"
            s3_client.upload_file(input_path, event['s3_bucket'], output_key)
            
            return {
                "statusCode": 200,
                "body": {
                    "downloaded_size": file_size,
                    "uploaded_key": output_key,
                    "success": True
                }
            }
    except Exception as e:
        return {"statusCode": 500, "body": {"error": str(e)}}
```

**Test**: Upload a small test video, invoke Lambda with S3 details
**Success Criteria**: Lambda downloads video, uploads copy successfully

## Phase 3: Basic Video Processing (2-3 hours)

### Step 3A: Test Simple Video Cutting
**Goal**: Cut one video into segments without text overlay
**Deliverable**: Lambda that creates basic segments

```python
# Simple video cutting test
def process_simple_segments(input_path, output_dir):
    import subprocess
    
    # Create 2 simple 10-second segments
    segments = []
    for i in range(2):
        start_time = i * 10
        output_path = os.path.join(output_dir, f'segment_{i:03d}.mp4')
        
        cmd = [
            '/opt/bin/ffmpeg', '-i', input_path,
            '-ss', str(start_time), '-t', '10',
            '-c', 'copy', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            segments.append(output_path)
    
    return segments
```

**Test**: Process a 30-second test video, should produce 2x 10-second segments
**Success Criteria**: Segments are created and playable

### Step 3B: Test DynamoDB Status Updates
**Goal**: Verify Lambda can update job status in DynamoDB
**Deliverable**: Lambda that updates processing status

```python
# DynamoDB integration test
def update_job_status_test(job_id, status):
    import boto3
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
    
    table.update_item(
        Key={'video_id': job_id},
        UpdateExpression='SET #status = :status, updated_at = :updated_at',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
    )
```

**Test**: Create test job in DynamoDB, update status via Lambda
**Success Criteria**: Job status updates correctly in database

## Phase 4: Integration Testing (2-3 hours)

### Step 4A: Test Complete Railway → Lambda → S3 → DynamoDB Flow
**Goal**: End-to-end test with real video
**Deliverable**: Complete processing pipeline

```python
# Railway test endpoint for full flow
@router.post("/test/lambda-processing")
async def test_lambda_processing(request: dict):
    """Test complete Lambda processing flow"""
    try:
        # 1. Create test job in DynamoDB
        job_id = str(uuid.uuid4())
        dynamodb_service.create_job_entry(
            job_id=job_id,
            user_id="test_user",
            status="QUEUED"
        )
        
        # 2. Trigger Lambda processing
        lambda_client = boto3.client('lambda')
        payload = {
            's3_bucket': settings.AWS_BUCKET_NAME,
            's3_key': request['s3_key'],  # User provides test video S3 key
            'job_id': job_id,
            'test_mode': True
        }
        
        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor",
            InvocationType='Event',  # Async
            Payload=json.dumps(payload)
        )
        
        return {
            "status": "processing_started",
            "job_id": job_id,
            "check_status_url": f"/api/jobs/{job_id}/status"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Test**: Upload video → call test endpoint → check job status → verify segments in S3
**Success Criteria**: Complete flow works, segments are created and downloadable

### Step 4B: Test Error Handling and Rollbacks
**Goal**: Verify system handles failures gracefully
**Deliverable**: Robust error handling

```python
# Test various failure scenarios:
# 1. Invalid S3 key → should update job status to FAILED
# 2. Processing timeout → should handle gracefully
# 3. Upload failure → should not leave partial results
```

## Phase 5: Production Integration (1-2 hours)

### Step 5A: Add Feature Flag for Lambda vs Celery
**Goal**: Allow gradual rollout
**Deliverable**: Configurable processing method

```python
# Add to Railway config
USE_LAMBDA_PROCESSING = os.getenv("USE_LAMBDA_PROCESSING", "false").lower() == "true"

# Update upload endpoint
@router.post("/upload/complete")
async def complete_upload(request: CompleteUploadRequest):
    if USE_LAMBDA_PROCESSING:
        await trigger_lambda_processing(request)
    else:
        process_video_task.delay(...)  # Existing Celery
```

### Step 5B: Monitor and Compare
**Goal**: Validate Lambda performs better than Celery
**Deliverable**: Performance comparison

```python
# Add monitoring to both paths
import time

processing_start = time.time()
# ... process video ...
processing_duration = time.time() - processing_start

# Log metrics for comparison
print(f"Processing method: {'Lambda' if USE_LAMBDA_PROCESSING else 'Celery'}")
print(f"Duration: {processing_duration:.2f}s")
print(f"Segments created: {len(output_urls)}")
```

## Testing Strategy for Each Phase

### Automated Testing
```bash
# Create test scripts for each phase
cd backend
python test_lambda_phase1.py  # Test Phase 1 components
python test_lambda_phase2.py  # Test Phase 2 components
# etc.
```

### Manual Testing Checklist
- [ ] Upload small test video (10MB)
- [ ] Upload medium test video (100MB)  
- [ ] Upload large test video (1GB)
- [ ] Test with different video formats
- [ ] Test error scenarios (invalid files, network issues)
- [ ] Compare processing times Lambda vs Celery

### Rollback Plan
At any phase, if something doesn't work:
1. **Terraform rollback**: `terraform workspace select main-simple && terraform destroy -target=aws_lambda_function.video_processor`
2. **Railway rollback**: Set `USE_LAMBDA_PROCESSING=false`
3. **Keep existing Celery**: Nothing breaks if Lambda fails

## Risk Mitigation

### What Could Go Wrong & How to Test
1. **Lambda timeout (15 min limit)**: Test with large videos first
2. **Memory issues (3GB limit)**: Test with high-resolution videos  
3. **FFmpeg compatibility**: Test various video formats
4. **S3 permissions**: Test download/upload with different bucket policies
5. **DynamoDB throttling**: Test rapid successive uploads

### Early Warning Signs
- Lambda timeout errors in CloudWatch
- High memory usage warnings
- S3 permission denied errors
- DynamoDB throttling exceptions

## Timeline Estimation

| Phase | Time | Risk Level | Can Rollback? |
|-------|------|------------|---------------|
| 1A: Lambda Hello World | 30 min | Low | ✅ Easy |
| 1B: Railway → Lambda | 30 min | Low | ✅ Easy |
| 2A: FFmpeg Layer | 1 hour | Medium | ✅ Easy |
| 2B: S3 Operations | 1 hour | Medium | ✅ Medium |
| 3A: Video Cutting | 2 hours | High | ✅ Medium |
| 3B: DynamoDB Updates | 1 hour | Low | ✅ Easy |
| 4A: Full Integration | 2 hours | High | ⚠️ Complex |
| 4B: Error Handling | 1 hour | Medium | ✅ Easy |
| 5A: Feature Flag | 30 min | Low | ✅ Easy |
| 5B: Monitoring | 30 min | Low | ✅ Easy |

**Total**: ~10 hours spread over 2-3 days

## Success Metrics

After each phase, ask:
1. **Does it work?** - Basic functionality test passes
2. **Is it reliable?** - Handles errors gracefully  
3. **Is it better?** - Performance improvement over current system
4. **Can we rollback?** - Quick path back to working state

This approach ensures you never have broken code in production and can stop/rollback at any point if issues arise.

---

*Incremental Implementation Strategy - Date: 2025-07-06*