# Easy Video Share - Backend (Sprint 3)

AI-powered video processing backend with dynamic cutting parameters and text strategies.

## Sprint 3 Overview

Sprint 3 implements dynamic user input for video processing with:

- **Dynamic Cutting Parameters**: User-defined segment durations (fixed or random ranges)
- **Text Strategy Framework**: Foundation for multiple text overlay strategies
- **Video Analysis API**: Preview segment counts before processing
- **Enhanced Processing**: User parameters passed to Celery workers
- **Backward Compatibility**: All Sprint 2 functionality preserved
- **Production Ready**: Real data processing, no mock/dummy data

## Quick Start

### 1. Start Services

Start all required services first. Use the automated service startup script:

```powershell
# Start Redis, Celery worker, and FastAPI server
powershell -File scripts/start-sprint2-services.ps1
```

Or start services manually (requires 3 separate terminals):

```bash
# Terminal 1: Start Redis
powershell -File scripts/start-redis.ps1

# Terminal 2: Start Celery worker
python run_worker.py

# Terminal 3: Start FastAPI server
python main.py
```

### 2. Validate Setup

**Important**: Services must be running before validation!

```bash
# Validate Sprint 3 functionality
python test_sprint3_validation.py

# Test video processing utilities independently
python test_sprint3_utils.py

# Legacy Sprint 2 validation (still supported)
python validate_sprint2.py
```

### 3. Test Sprint 3 Features

Test the new dynamic cutting and text strategy features:

```bash
# Test Sprint 3 API endpoints and features
python test_sprint3_validation.py

# Test Sprint 3 video processing utilities
python test_sprint3_utils.py
```

### 4. Run End-to-End Test

Test the complete workflow with a real video:

```bash
# Create test video and run full workflow (Sprint 2 compatible)
python test_sprint2_e2e.py
```

### 4. API Documentation

Visit the interactive API docs:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Architecture

### API Endpoints

**Core Endpoints:**

- `POST /api/upload/initiate` - Get S3 presigned URL for video upload
- `POST /api/upload/complete` - Complete upload and start processing (now accepts cutting options & text strategy)
- `GET /api/jobs/{job_id}/status` - Get job status and results
- `GET /api/health` - Health check

**Sprint 3 New Endpoints:**

- `POST /api/video/analyze-duration` - Analyze video and preview segment count with cutting options

### Workflow

**Basic Workflow (Sprint 2 Compatible):**

1. **Initiate Upload**: Frontend calls `/upload/initiate` with video metadata
2. **Upload to S3**: Frontend uploads video directly to S3 using presigned URL
3. **Start Processing**: Frontend calls `/upload/complete` to trigger processing
4. **Background Processing**: Celery worker downloads video, processes it, uploads results
5. **Poll Status**: Frontend polls `/jobs/{job_id}/status` for progress
6. **Retrieve Results**: Get S3 URLs of processed video segments

**Enhanced Workflow (Sprint 3):**

1. **Analyze Video** (Optional): Call `/video/analyze-duration` to preview segment count
2. **Initiate Upload**: Frontend calls `/upload/initiate` with video metadata
3. **Upload to S3**: Frontend uploads video directly to S3 using presigned URL
4. **Start Processing**: Frontend calls `/upload/complete` with cutting options and text strategy
5. **Dynamic Processing**: Celery worker uses user-defined cutting parameters
6. **Poll Status**: Frontend polls `/jobs/{job_id}/status` for progress
7. **Retrieve Results**: Get S3 URLs of processed video segments

### Video Processing

**Sprint 3 Enhanced Processing:**

The video processor now supports dynamic cutting parameters:

- **Fixed Duration Cutting**: Create segments of exact duration (e.g., 30 seconds each)
- **Random Duration Cutting**: Create segments with random durations within a specified range (e.g., 15-45 seconds)
- **Text Strategy Framework**: Foundation for multiple text overlay strategies (Sprint 4 will expand)
- **Video Analysis**: Fast duration analysis using ffprobe for segment preview
- **Backward Compatibility**: Default to 30-second segments if no options provided

**Cutting Options Examples:**

```json
// Fixed 20-second segments
{
  "type": "fixed",
  "duration_seconds": 20
}

// Random segments between 15-45 seconds
{
  "type": "random",
  "min_duration": 15,
  "max_duration": 45
}
```

**Text Strategies:**

- `ONE_FOR_ALL`: Single text overlay for all segments (current implementation)
- `BASE_VARY`: Base text with LLM variations (Sprint 4)
- `UNIQUE_FOR_ALL`: Unique text per segment (Sprint 4)

**Legacy Processing (Sprint 2):**

The robust video processor (`video_processing_utils_robust.py`) still handles core processing:

- **Split Video**: Creates segments with proper keyframe handling
- **Text Overlay**: Adds text overlay using FFmpeg filters
- **Error Handling**: Comprehensive error handling and logging
- **File Validation**: Validates input videos before processing

## Dependencies

### System Requirements

- **Python 3.8+**
- **FFmpeg** (for video processing)
- **Redis** (for Celery broker/backend)
- **AWS CLI** or credentials (for S3 access)

### Python Packages

```bash
pip install -r requirements.txt
```

Key packages:

- `fastapi` - Web API framework
- `celery` - Background task processing
- `redis` - Redis client for Celery
- `boto3` - AWS SDK for S3 operations
- `Pillow` - Image processing support

### Redis Setup

Redis is required for Celery. Use Docker:

```bash
# Start Redis with Docker Compose
docker-compose up -d redis

# Or use provided script
powershell -File scripts/start-redis.ps1
```

### AWS Configuration

Set up AWS credentials for S3 access:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
set AWS_ACCESS_KEY_ID=your_key_id
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_DEFAULT_REGION=us-east-1

# Option 3: AWS SSO (recommended)
aws sso login
```

## Configuration

Configuration is handled via environment variables in `config.py`:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AWS Configuration
AWS_BUCKET_NAME=your-video-bucket
AWS_ACCESS_KEY_ID=your_key_id
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# API Configuration
HOST=localhost
PORT=8000
DEBUG=True
```

## Testing

### Infrastructure Tests

```bash
# Test Redis connection
python test_redis_connection.py

# Test AWS credentials
python test_aws_auth.py

# Test FFmpeg setup
python diagnose_ffmpeg.py
```

### Video Processing Tests

```bash
# Test Sprint 3 features
python test_sprint3_validation.py    # Complete Sprint 3 API validation
python test_sprint3_utils.py         # Video processing utilities

# Test Sprint 2 compatibility
python validate_sprint2.py           # Infrastructure validation
python test_sprint2_e2e.py          # End-to-end workflow test

# Individual component tests
python create_test_video.py         # Create test video
```

## Production Cleanup

After validation, clean up test/debug files:

```bash
# Dry run - see what would be removed
python cleanup_test_files.py

# Actually remove test files
python cleanup_test_files.py --confirm
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**

   ```bash
   # Check if Redis is running
   redis-cli ping

   # Start Redis if needed
   powershell -File scripts/start-redis.ps1
   ```

2. **FFmpeg Not Found**

   ```bash
   # Install FFmpeg and add to PATH
   # Download from: https://ffmpeg.org/download.html
   ffmpeg -version
   ```

3. **AWS Credentials Invalid**

   ```bash
   # Check AWS configuration
   aws sts get-caller-identity

   # Reconfigure if needed
   aws configure
   ```

4. **Video Processing Failed**

   ```bash
   # Check video file format
   ffprobe your_video.mp4

   # Check Celery worker logs
   python run_worker.py
   ```

### Logs and Debugging

- **API Logs**: Check FastAPI server console output
- **Worker Logs**: Check Celery worker console output
- **Redis Logs**: Check Docker container logs
- **Processing Logs**: Detailed logging in video processing functions

## Sprint 4 Preparation

Sprint 3 provides the enhanced foundation for Sprint 4 features:

- ✅ **Dynamic Cutting**: User-defined segment durations (fixed/random)
- ✅ **Text Strategy Framework**: Extensible text overlay system
- ✅ **Video Analysis API**: Fast duration analysis and segment preview
- ✅ **Enhanced API**: Cutting options and text strategy parameters
- ✅ **Production Ready**: Real data processing, comprehensive error handling
- ✅ **Backward Compatibility**: All Sprint 2 functionality preserved

**Next Sprint 4 Features**:

- **LLM Text Generation**: AI-powered text variations using Gemini API
- **Advanced Text Strategies**:
  - `BASE_VARY`: Base text with LLM-generated variations
  - `UNIQUE_FOR_ALL`: Frontend UI for unique text per segment
- **Enhanced Video Processing**: Use precise segment timing from analysis
- **Frontend Integration**: Vue.js components for cutting options and text strategies

## Current Capabilities (Sprint 3)

### ✅ **Dynamic Video Analysis**

```bash
curl -X POST "http://localhost:8000/api/video/analyze-duration" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/my-video.mp4",
    "cutting_options": {
      "type": "random",
      "min_duration": 15,
      "max_duration": 45
    }
  }'
```

### ✅ **Enhanced Processing**

```bash
curl -X POST "http://localhost:8000/api/upload/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/my-video.mp4",
    "job_id": "user-generated-id",
    "cutting_options": {
      "type": "fixed",
      "duration_seconds": 20
    },
    "text_strategy": "one_for_all"
  }'
```

### ✅ **Production Results**

Your validation shows successful processing:

- **5 video segments** created from real video file
- **Dynamic cutting** working with user parameters
- **S3 URLs** generated for each processed segment
- **Job tracking** functioning correctly
- **Processing time**: ~35 seconds for complete workflow

## File Structure

```
backend/
├── main.py                           # FastAPI application (enhanced with Sprint 3 endpoints)
├── tasks.py                          # Celery tasks (enhanced with dynamic parameters)
├── models.py                         # Pydantic models (Sprint 3 cutting options & text strategies)
├── config.py                         # Configuration
├── s3_utils.py                       # S3 operations
├── video_processing_utils.py         # Sprint 3 video analysis & segment calculation
├── video_processing_utils_robust.py  # Core video processing (Sprint 2)
├── requirements.txt                  # Python dependencies
├── run_server.py                     # Server startup
├── run_worker.py                     # Worker startup
├── test_sprint3_validation.py        # Sprint 3 validation suite
├── test_sprint3_utils.py             # Sprint 3 utility tests
├── validate_sprint2.py               # Sprint 2 validation (legacy)
├── test_sprint2_e2e.py              # End-to-end test (legacy compatible)
├── create_test_video.py             # Test video creator
├── cleanup_test_files.py            # Cleanup utility
└── README-SPRINT-3.md               # Sprint 3 detailed documentation
```

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Run validation: `python validate_sprint2.py`
3. Check logs from all services
4. Review Sprint 2 planning documents
