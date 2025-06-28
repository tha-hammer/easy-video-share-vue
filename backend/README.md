# Easy Video Share - Backend (Sprint 2)

AI-powered video processing backend for splitting videos and adding text overlays.

## Sprint 2 Overview

Sprint 2 implements a robust, production-ready video processing workflow with:

- **Direct S3 Upload**: Frontend uploads videos directly to S3 using presigned URLs
- **Background Processing**: Celery workers process videos asynchronously
- **Robust Video Processing**: FFmpeg-based splitting and text overlay (bypasses MoviePy issues)
- **Real Video Support**: Handles actual video files with proper error handling
- **S3 Integration**: Seamless upload/download with AWS authentication fallback
- **Job Status Tracking**: Poll job status and retrieve results via API

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
# Validate all dependencies and infrastructure
python validate_sprint2.py
```

### 3. Run End-to-End Test

Test the complete workflow with a real video:

```bash
# Create test video and run full workflow
python test_sprint2_e2e.py
```

### 4. API Documentation

Visit the interactive API docs:

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Architecture

### API Endpoints

- `POST /api/upload/initiate` - Get S3 presigned URL for video upload
- `POST /api/upload/complete` - Complete upload and start processing
- `GET /api/jobs/{job_id}/status` - Get job status and results
- `GET /api/health` - Health check

### Workflow

1. **Initiate Upload**: Frontend calls `/upload/initiate` with video metadata
2. **Upload to S3**: Frontend uploads video directly to S3 using presigned URL
3. **Start Processing**: Frontend calls `/upload/complete` to trigger processing
4. **Background Processing**: Celery worker downloads video, processes it, uploads results
5. **Poll Status**: Frontend polls `/jobs/{job_id}/status` for progress
6. **Retrieve Results**: Get S3 URLs of processed video segments

### Video Processing

The robust video processor (`video_processing_utils_robust.py`) uses direct FFmpeg calls:

- **Split Video**: Creates 30-second segments with proper keyframe handling
- **Text Overlay**: Adds hardcoded text overlay ("Amazing content!") using FFmpeg filters
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
# Test video processing pipeline
python validate_sprint2.py

# Create test video
python create_test_video.py

# Run end-to-end workflow test
python test_sprint2_e2e.py
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

## Sprint 3 Preparation

Sprint 2 provides the foundation for Sprint 3 features:

- ✅ **Infrastructure**: Redis, Celery, S3 integration
- ✅ **Video Processing**: Robust splitting and text overlay
- ✅ **API Framework**: RESTful endpoints with job tracking
- ✅ **Error Handling**: Comprehensive error handling and recovery

**Next Sprint 3 Features**:

- Dynamic text overlays (user-provided text)
- Configurable segment durations
- Multiple processing strategies
- Advanced overlay positioning
- Batch processing support

## File Structure

```
backend/
├── main.py                           # FastAPI application
├── tasks.py                          # Celery tasks
├── models.py                         # Pydantic models
├── config.py                         # Configuration
├── s3_utils.py                       # S3 operations
├── video_processing_utils_robust.py  # Video processing
├── requirements.txt                  # Python dependencies
├── run_server.py                     # Server startup
├── run_worker.py                     # Worker startup
├── validate_sprint2.py               # Validation suite
├── test_sprint2_e2e.py              # End-to-end test
├── create_test_video.py             # Test video creator
└── cleanup_test_files.py            # Cleanup utility
```

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Run validation: `python validate_sprint2.py`
3. Check logs from all services
4. Review Sprint 2 planning documents
