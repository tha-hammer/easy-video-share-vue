from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uuid
from models import (
    InitiateUploadRequest, 
    InitiateUploadResponse, 
    CompleteUploadRequest, 
    JobCreatedResponse
)
from s3_utils import generate_presigned_url, generate_s3_key
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Easy Video Share API",
    description="AI-powered video processing and sharing platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
router = APIRouter(prefix="/api")


@router.post("/upload/initiate", response_model=InitiateUploadResponse)
async def initiate_upload(request: InitiateUploadRequest) -> InitiateUploadResponse:
    """
    Initiate video upload by generating S3 presigned URL
    
    This endpoint generates a presigned URL for direct upload to S3,
    allowing the frontend to upload large video files directly to S3
    without going through the backend server.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Generate S3 key for the upload
        s3_key = generate_s3_key(request.filename, job_id)
        
        # Generate presigned URL for S3 upload
        presigned_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=s3_key,
            content_type=request.content_type,
            expiration=3600  # 1 hour
        )
        
        return InitiateUploadResponse(
            presigned_url=presigned_url,
            s3_key=s3_key,
            job_id=job_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}")


@router.post("/upload/complete", response_model=JobCreatedResponse)
async def complete_upload(request: CompleteUploadRequest) -> JobCreatedResponse:
    """
    Complete upload and start video processing
    
    This endpoint is called after the frontend successfully uploads
    the video to S3 using the presigned URL. It dispatches the video
    processing task to the Celery worker.
    """
    try:
        # For Sprint 1 testing, we'll simulate task dispatch without Redis
        print(f"📋 Would dispatch video processing task for job: {request.job_id}")
        print(f"📋 S3 key: {request.s3_key}")
        
        # TODO: Uncomment when Redis is running
        # from tasks import process_video_task
        # task = process_video_task.delay(request.s3_key, request.job_id)
        
        return JobCreatedResponse(
            job_id=request.job_id,
            status="QUEUED",
            message="Video processing job has been queued successfully (simulated for Sprint 1)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Video processing API is running"}


# Include router in app
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
