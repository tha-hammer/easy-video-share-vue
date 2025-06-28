# Sprint 2: Basic Video Splitting & Text Overlay

Sprint 2 implements the core video processing functionality where uploaded videos are automatically split into 30-second segments with hardcoded text overlays.

## 🎯 Sprint 2 Goals

- ✅ **Real Video Processing**: Download videos from S3, process with MoviePy, upload results back to S3
- ✅ **Video Splitting**: Split videos into 30-second segments
- ✅ **Text Overlay**: Add hardcoded "AI Generated Video" text overlay to each segment
- ✅ **Background Processing**: Celery task queue with Redis broker
- ✅ **External Dependencies**: Docker setup for Redis, FFmpeg for video processing

## 🛠️ External Dependencies

### Redis (Celery Broker)

Redis is required for Celery task queue management.

**Start Redis:**

```powershell
.\scripts\start-redis.ps1
```

**Stop Redis:**

```powershell
.\scripts\stop-redis.ps1
```

### FFmpeg (Video Processing)

FFmpeg is required by MoviePy for video encoding/decoding.

**Windows Installation Options:**

1. **Chocolatey:** `choco install ffmpeg`
2. **Winget:** `winget install Gyan.FFmpeg`
3. **Manual:** Download from https://www.gyan.dev/ffmpeg/builds/ and add to PATH

**Verify Installation:**

```powershell
.\scripts\verify-setup.ps1
```

## 🚀 Running Sprint 2

### 1. Start External Services

```powershell
# Start Redis
.\scripts\start-redis.ps1

# Verify setup (Redis + FFmpeg)
.\scripts\verify-setup.ps1
```

### 2. Start the Backend API

```powershell
cd backend
python main.py
```

### 3. Start the Celery Worker

```powershell
# In a new terminal
.\scripts\start-worker.ps1
```

### 4. Test the Pipeline

```powershell
cd backend
python test_sprint_2.py
```

## 📋 Video Processing Workflow

1. **Upload Initiation**: Frontend requests presigned S3 URL
2. **Direct S3 Upload**: Frontend uploads video directly to S3
3. **Job Dispatch**: Backend dispatches Celery task with S3 key
4. **Video Processing**:
   - Download video from S3 to temporary directory
   - Validate video file format
   - Split into 30-second segments
   - Add "AI Generated Video" text overlay to each segment
   - Upload processed segments back to S3 (`processed/{job_id}/` folder)
   - Clean up temporary files
5. **Result Storage**: Processed videos stored in S3 with public URLs

## 🧪 Testing

### API Integration Test

```powershell
cd backend
python test_sprint_2.py
```

Tests the complete API workflow without actual video processing.

### Video Processing Test

```powershell
cd backend
python test_video_processing.py path/to/your/video.mp4
```

Tests video processing logic with a real video file.

### Redis Connectivity Test

```powershell
cd backend
python test_redis_connection.py
```

Tests Redis connection for Celery.

## 📁 Key Files Created/Modified

### Core Processing

- `video_processing_utils.py` - MoviePy video processing logic
- `tasks.py` - Updated Celery task implementation
- `s3_utils.py` - S3 download/upload functions (extended)

### Infrastructure

- `docker-compose.yml` - Redis service configuration
- `scripts/start-redis.ps1` - Redis startup script
- `scripts/stop-redis.ps1` - Redis shutdown script
- `scripts/start-worker.ps1` - Enhanced Celery worker script
- `scripts/verify-setup.ps1` - Environment verification

### Testing

- `test_sprint_2.py` - Integration test for API workflow
- `test_video_processing.py` - Video processing unit test
- `test_redis_connection.py` - Redis connectivity test

## 🎥 Video Processing Details

### Hardcoded Parameters (Sprint 2)

- **Segment Duration**: 30 seconds
- **Text Overlay**: "AI Generated Video"
- **Text Style**: White text, black stroke, Arial Bold, 50px
- **Text Position**: Bottom center
- **Output Format**: MP4 with H.264 video and AAC audio

### S3 Structure

```
your-bucket/
├── uploads/{job_id}/           # Original uploaded videos
│   └── {timestamp}_{filename}
└── processed/{job_id}/         # Processed segments
    ├── processed_{job_id}_segment_001.mp4
    ├── processed_{job_id}_segment_002.mp4
    └── ...
```

## 🔧 Troubleshooting

### Common Issues

**FFmpeg not found:**

- Ensure FFmpeg is installed and in your PATH
- Run `.\scripts\verify-setup.ps1` to check installation

**Redis connection failed:**

- Make sure Docker is running
- Start Redis with `.\scripts\start-redis.ps1`
- Check Redis status: `docker ps | findstr redis`

**Video processing fails:**

- Check video file format (MP4, AVI, MOV supported)
- Ensure sufficient disk space for temporary files
- Monitor Celery worker logs for detailed error messages

**S3 upload/download fails:**

- Verify AWS credentials and region configuration
- Check S3 bucket permissions
- Ensure bucket exists and is accessible

### Log Monitoring

```powershell
# Monitor Celery worker
.\scripts\start-worker.ps1

# Monitor Redis logs
docker logs easy-video-share-redis -f

# Monitor FastAPI logs
cd backend && python main.py
```

## ➡️ Next Steps: Sprint 3

Sprint 3 will add:

- Dynamic user input for cutting parameters (fixed duration vs random range)
- Video duration analysis and segment count preview
- User-configurable text strategies
- Enhanced API endpoints for parameter validation

## 🔗 Related Documentation

- [Sprint 1: Upload Infrastructure](../README.md)
- [Overall Project Plan](../AI-BRoll-Short-Form-Video-Generation-Plan.md)
- [Updated Implementation Strategy](../Ai-BRoll-Short-Form-Video-Generation-Plan-UPDATE.md)
