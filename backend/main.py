from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uuid
from models import (
    InitiateUploadRequest, 
    InitiateUploadResponse, 
    CompleteUploadRequest, 
    JobCreatedResponse,
    JobStatusResponse,
    AnalyzeDurationRequest,
    AnalyzeDurationResponse,
    CuttingOptions
)
from s3_utils import generate_presigned_url, generate_s3_key
from tasks import process_video_task, celery_app
from video_processing_utils import get_video_duration_from_s3, calculate_segments
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
    processing task to the Celery worker with user-specified cutting
    options and text strategy.
    """
    try:
        # Convert Pydantic models to dicts for Celery serialization
        cutting_options_dict = None
        if request.cutting_options:
            cutting_options_dict = request.cutting_options.dict()
            
        text_strategy_str = None
        if request.text_strategy:
            text_strategy_str = request.text_strategy.value
        
        text_input_dict = None
        if request.text_input:
            text_input_dict = request.text_input.dict()
        
        # Dispatch video processing task to Celery
        task = process_video_task.delay(
            request.s3_key, 
            request.job_id,
            cutting_options_dict,
            text_strategy_str,
            text_input_dict
        )
        
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


@router.post("/analyze/duration", response_model=AnalyzeDurationResponse)
async def analyze_video_duration(request: AnalyzeDurationRequest) -> AnalyzeDurationResponse:
    """
    Analyze video duration and suggest cutting points
    
    This endpoint analyzes the video duration and suggests cutting points
    based on the specified options. It is used to prepare the video for
    sharing by generating shorter clips.
    """
    try:
        # Get video duration from S3
        duration = get_video_duration_from_s3(request.s3_key)
        
        # Calculate segments based on duration and cutting options
        segments = calculate_segments(duration, request.cutting_options)
        
        return AnalyzeDurationResponse(
            job_id=request.job_id,
            duration=duration,
            segments=segments
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze video duration: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Video processing API is running"}


@router.post("/video/analyze-duration", response_model=AnalyzeDurationResponse)
async def analyze_duration(request: AnalyzeDurationRequest) -> AnalyzeDurationResponse:
    """
    Analyze video duration and calculate segment count based on cutting options
    
    This endpoint allows the frontend to preview how many segments will be created
    for a given video and cutting parameters before starting the actual processing job.
    """
    try:
        # Get video duration from S3
        total_duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, request.s3_key)
        
        # Calculate segments based on cutting options
        num_segments, segment_times = calculate_segments(total_duration, request.cutting_options)
        
        # Extract just the durations for the response
        segment_durations = [end - start for start, end in segment_times]
        
        return AnalyzeDurationResponse(
            total_duration=total_duration,
            num_segments=num_segments,
            segment_durations=segment_durations
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video file not found in S3")
    except Exception as e:
        error_msg = str(e)
        # Check for S3 404 errors (from ClientError wrapped in Exception)
        if "404" in error_msg and "Not Found" in error_msg:
            raise HTTPException(status_code=404, detail="Video file not found in S3")
        elif "Invalid video file format" in error_msg or "corrupted" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        elif "too short" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail=f"Failed to analyze video: {error_msg}")


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
