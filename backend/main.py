from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uuid
from models import (
    InitiateUploadRequest, 
    InitiateUploadResponse, 
    CompleteUploadRequest, 
    JobCreatedResponse,
    JobStatusResponse
)
from s3_utils import generate_presigned_url, generate_s3_key
from tasks import process_video_task, celery_app
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
        # Dispatch video processing task to Celery
        task = process_video_task.delay(request.s3_key, request.job_id)
        
        # Use the Celery task ID as the job ID for tracking
        return JobCreatedResponse(
            job_id=task.id,  # Use Celery task ID instead of original job_id
            status="QUEUED",
            message="Video processing job has been queued successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a video processing job
    
    This endpoint allows the frontend to poll for job status updates
    and retrieve the results when processing is complete.
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(job_id)
        
        # Map Celery states to our status format
        status_mapping = {
            "PENDING": "QUEUED",
            "STARTED": "PROCESSING", 
            "SUCCESS": "COMPLETED",
            "FAILURE": "FAILED",
            "RETRY": "PROCESSING",
            "REVOKED": "CANCELLED"
        }
        
        status = status_mapping.get(task_result.state, "UNKNOWN")
        
        response_data = {
            "job_id": job_id,
            "status": status
        }
        
        if task_result.state == "SUCCESS":
            # Task completed successfully
            result = task_result.result
            if isinstance(result, dict):
                response_data["output_urls"] = result.get("output_urls", [])
        elif task_result.state == "FAILURE":
            # Task failed
            response_data["error_message"] = str(task_result.info)
        elif task_result.state == "STARTED":
            # Task is running, try to get progress if available
            if hasattr(task_result, 'info') and isinstance(task_result.info, dict):
                response_data["progress"] = task_result.info.get("progress")
        
        return JobStatusResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


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
