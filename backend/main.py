from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uuid
import traceback
from models import (
    InitiateUploadRequest,
    InitiateUploadResponse,
    CompleteUploadRequest,
    JobCreatedResponse,
    JobStatusResponse,
    AnalyzeDurationRequest,
    AnalyzeDurationResponse,
    CuttingOptions,
    ProgressUpdate,
    InitiateMultipartUploadRequest,
    InitiateMultipartUploadResponse,
    UploadPartRequest,
    UploadPartResponse,
    CompleteMultipartUploadRequest,
    AbortMultipartUploadRequest,
    # Segment models
    VideoSegment,
    SegmentCreateRequest,
    SegmentUpdateRequest,
    SegmentListResponse,
    SegmentFilters,
    SocialMediaSyncRequest,
    SocialMediaAnalyticsResponse,
    SegmentType,
    SocialMediaPlatform,
    SocialMediaUsage
)
from s3_utils import (
    generate_presigned_url, 
    generate_s3_key, 
    calculate_optimal_chunk_size,
    initiate_multipart_upload as s3_initiate_multipart_upload,
    generate_presigned_url_for_part as s3_generate_presigned_url_for_part,
    complete_multipart_upload as s3_complete_multipart_upload,
    abort_multipart_upload as s3_abort_multipart_upload
)
import dynamodb_service
from dynamodb_service import iso_utc_now
from tasks import process_video_task, celery_app
from video_processing_utils import get_video_duration_from_s3, calculate_segments
from config import settings
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
import asyncio
import json

# Initialize FastAPI app
app = FastAPI(
    title="Easy Video Share API",
    description="AI-powered video processing and sharing platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debug
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
router = APIRouter(prefix="/api")

# --- MODIFIED REDIS CLIENT SETUP START ---
# Global async Redis client connection pool (initialized on app startup)
# This prevents creating a new connection for every SSE request
_redis_connection_pool = None

@app.on_event("startup")
async def startup_event():
    global _redis_connection_pool
    print("DEBUG: Initializing async Redis client pool on startup.")
    _redis_connection_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    print("DEBUG: Closing async Redis client pool on shutdown.")
    if _redis_connection_pool:
        await _redis_connection_pool.disconnect()

# Helper to get an async Redis client from the global pool
async def get_async_redis_client_from_pool():
    if not _redis_connection_pool:
        raise RuntimeError("Redis connection pool not initialized.")
    return redis.Redis(connection_pool=_redis_connection_pool)
# --- MODIFIED REDIS CLIENT SETUP END ---

@router.post("/upload/initiate", response_model=InitiateUploadResponse)
async def initiate_upload(request: InitiateUploadRequest) -> InitiateUploadResponse:
    """
    Initiate video upload by generating S3 presigned URL

    This endpoint generates a presigned URL for direct upload to S3,
    allowing the frontend to upload large video files directly to S3
    without going through the backend server.
    """
    try:
        print(f"DEBUG: initiate_upload called with request: {request}")
        print(f"DEBUG: AWS_REGION = {settings.AWS_REGION}")
        print(f"DEBUG: AWS_BUCKET_NAME = {settings.AWS_BUCKET_NAME}")
        print(f"DEBUG: AWS_ACCESS_KEY_ID = {'SET' if settings.AWS_ACCESS_KEY_ID else 'NOT SET'}")
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        print(f"DEBUG: Generated job_id = {job_id}")

        # Generate S3 key for the upload
        s3_key = generate_s3_key(request.filename, job_id)
        print(f"DEBUG: Generated s3_key = {s3_key}")

        # Generate presigned URL for S3 upload
        print(f"DEBUG: Calling generate_presigned_url with bucket={settings.AWS_BUCKET_NAME}, key={s3_key}")
        presigned_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=s3_key,
            client_method='put_object',  # Use 'put_object' for uploads
            content_type=request.content_type,
            expiration=3600  # 1 hour
        )
        print(f"DEBUG: Generated presigned_url = {presigned_url[:50]}...")

        response = InitiateUploadResponse(
            presigned_url=presigned_url,
            s3_key=s3_key,
            job_id=job_id
        )
        print(f"DEBUG: Returning response: {response}")
        return response

    except Exception as e:
        print(f"DEBUG: ERROR in initiate_upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}")


# === MULTI-PART UPLOAD ENDPOINTS ===

@router.post("/upload/initiate-multipart", response_model=InitiateMultipartUploadResponse)
async def initiate_multipart_upload(request: InitiateMultipartUploadRequest) -> InitiateMultipartUploadResponse:
    """
    Initiate multi-part video upload for large files
    
    This endpoint initiates a multi-part upload to S3, which is more efficient
    for large video files (especially on mobile devices) as it allows parallel
    upload of chunks and better error recovery.
    """
    try:
        print(f"DEBUG: initiate_multipart_upload called with request: {request}")
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        print(f"DEBUG: Generated job_id = {job_id}")

        # Generate S3 key for the upload
        s3_key = generate_s3_key(request.filename, job_id)
        print(f"DEBUG: Generated s3_key = {s3_key}")

        # Calculate optimal chunk size and concurrent uploads
        # For now, assume mobile if file is large (>100MB)
        is_mobile = request.file_size > 100 * 1024 * 1024  # 100MB threshold
        chunk_size, max_concurrent = calculate_optimal_chunk_size(request.file_size, is_mobile)
        
        print(f"DEBUG: File size: {request.file_size}, Mobile: {is_mobile}")
        print(f"DEBUG: Chunk size: {chunk_size}, Max concurrent: {max_concurrent}")

        # Initiate multi-part upload
        upload_id = s3_initiate_multipart_upload(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=s3_key,
            content_type=request.content_type
        )
        print(f"DEBUG: Generated upload_id = {upload_id}")

        response = InitiateMultipartUploadResponse(
            upload_id=upload_id,
            s3_key=s3_key,
            job_id=job_id,
            chunk_size=chunk_size,
            max_concurrent_uploads=max_concurrent
        )
        print(f"DEBUG: Returning response: {response}")
        return response

    except Exception as e:
        print(f"DEBUG: ERROR in initiate_multipart_upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to initiate multipart upload: {str(e)}")


@router.post("/upload/part", response_model=UploadPartResponse)
async def get_upload_part_url(request: UploadPartRequest) -> UploadPartResponse:
    """
    Get presigned URL for uploading a specific part
    
    This endpoint generates a presigned URL for uploading a specific chunk
    of the multi-part upload.
    """
    try:
        print(f"DEBUG: get_upload_part_url called with request: {request}")
        
        # Generate presigned URL for this part
        presigned_url = s3_generate_presigned_url_for_part(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=request.s3_key,
            upload_id=request.upload_id,
            part_number=request.part_number,
            expiration=3600  # 1 hour
        )
        
        print(f"DEBUG: Generated presigned URL for part {request.part_number}")

        return UploadPartResponse(
            presigned_url=presigned_url,
            part_number=request.part_number
        )

    except Exception as e:
        print(f"DEBUG: ERROR in get_upload_part_url: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get upload part URL: {str(e)}")


@router.post("/upload/finalize-multipart")
async def finalize_multipart_upload(request: CompleteMultipartUploadRequest):
    """
    Finalize multi-part upload (S3 only, no processing)
    
    This endpoint only completes the S3 multi-part upload without
    starting any video processing. It's called when the upload finishes.
    """
    try:
        print(f"DEBUG: finalize_multipart_upload called with request: {request}")
        
        # Validate that we have parts to complete the upload
        if not request.parts or len(request.parts) == 0:
            raise HTTPException(status_code=400, detail="No parts provided to complete multipart upload")
        
        # Complete the multi-part upload
        s3_url = s3_complete_multipart_upload(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=request.s3_key,
            upload_id=request.upload_id,
            parts=request.parts
        )
        print(f"DEBUG: Multi-part upload finalized: {s3_url}")
        
        return {"message": "Multi-part upload finalized successfully", "s3_url": s3_url}

    except Exception as e:
        print(f"DEBUG: ERROR in finalize_multipart_upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to finalize multipart upload: {str(e)}")


@router.post("/upload/complete-multipart", response_model=JobCreatedResponse)
async def complete_multipart_upload(request: CompleteMultipartUploadRequest) -> JobCreatedResponse:
    """
    Complete multi-part upload and start video processing
    
    This endpoint completes the multi-part upload and then dispatches
    the video processing task, similar to the single-part complete endpoint.
    """
    try:
        print(f"DEBUG: complete_multipart_upload called with request: {request}")
        
        # Validate that we have parts to complete the upload
        if not request.parts or len(request.parts) == 0:
            raise HTTPException(status_code=400, detail="No parts provided to complete multipart upload")
        
        # Complete the multi-part upload
        s3_url = s3_complete_multipart_upload(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=request.s3_key,
            upload_id=request.upload_id,
            parts=request.parts
        )
        print(f"DEBUG: Multi-part upload completed: {s3_url}")
        
        # Get video duration and store it for later use
        video_duration = None
        try:
            print(f"DEBUG: Getting video duration for s3_key: {request.s3_key}")
            video_duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, request.s3_key)
            print(f"DEBUG: Video duration: {video_duration} seconds")
        except Exception as duration_error:
            print(f"DEBUG: Failed to get video duration: {duration_error}")
            # Continue without duration - it will be calculated later if needed
        
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
            text_input_dict,
            request.user_id or "anonymous"  # Use provided user_id or default to "anonymous"
        )

        # Immediately create DynamoDB job entry (QUEUED) with video duration
        try:
            from datetime import datetime, timezone
            now_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            
            dynamodb_service.create_job_entry(
                job_id=request.job_id,
                user_id=request.user_id,
                upload_date=now_iso,
                status="QUEUED",
                created_at=now_iso,
                updated_at=now_iso,
                video_duration=video_duration,  # Store the duration if available
                # Additional video metadata fields
                filename=request.filename,
                file_size=request.file_size,
                title=request.title,
                user_email=request.user_email,
                content_type=request.content_type,
                bucket_location=request.s3_key
            )
        except Exception as e:
            print(f"[DynamoDB] Failed to create job entry in /upload/complete-multipart for job_id={request.job_id}: {e}")

        return JobCreatedResponse(
            job_id=request.job_id,
            status="QUEUED",
            message="Video processing job has been queued successfully"
        )

    except Exception as e:
        print(f"DEBUG: ERROR in complete_multipart_upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to complete multipart upload: {str(e)}")


@router.post("/upload/abort-multipart")
async def abort_multipart_upload(request: AbortMultipartUploadRequest):
    """
    Abort a multi-part upload
    
    This endpoint aborts an in-progress multi-part upload, cleaning up
    any uploaded parts and freeing up S3 storage.
    """
    try:
        print(f"DEBUG: abort_multipart_upload called with request: {request}")
        
        # Abort the multi-part upload
        s3_abort_multipart_upload(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=request.s3_key,
            upload_id=request.upload_id
        )
        
        print(f"DEBUG: Multi-part upload aborted successfully")
        return {"message": "Multi-part upload aborted successfully"}

    except Exception as e:
        print(f"DEBUG: ERROR in abort_multipart_upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to abort multipart upload: {str(e)}")


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
        print(f"DEBUG: complete_upload called with request: {request}")
        
        # Get video duration and store it for later use
        video_duration = None
        try:
            print(f"DEBUG: Getting video duration for s3_key: {request.s3_key}")
            video_duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, request.s3_key)
            print(f"DEBUG: Video duration: {video_duration} seconds")
        except Exception as duration_error:
            print(f"DEBUG: Failed to get video duration: {duration_error}")
            # Continue without duration - it will be calculated later if needed
        
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
            text_input_dict,
            request.user_id or "anonymous"  # Use provided user_id or default to "anonymous"
        )

        # Immediately create DynamoDB job entry (QUEUED) with video duration
        try:
            from datetime import datetime, timezone
            now_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            
            dynamodb_service.create_job_entry(
                job_id=request.job_id,
                user_id=request.user_id,
                upload_date=now_iso,
                status="QUEUED",
                created_at=now_iso,
                updated_at=now_iso,
                video_duration=video_duration,  # Store the duration if available
                # Additional video metadata fields
                filename=request.filename,
                file_size=request.file_size,
                title=request.title,
                user_email=request.user_email,
                content_type=request.content_type,
                bucket_location=request.s3_key
            )
        except Exception as e:
            print(f"[DynamoDB] Failed to create job entry in /upload/complete for job_id={request.job_id}: {e}")

        return JobCreatedResponse(
            job_id=request.job_id,
            status="QUEUED",
            message="Video processing job has been queued successfully"
        )

    except Exception as e:
        print(f"DEBUG: ERROR in complete_upload: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a video processing job (Sprint 5: DynamoDB + presigned download URLs)
    """
    # --- DEBUGGING PRINTS START ---
    print(f"DEBUG: Entering get_job_status for job_id: {job_id}")
    # --- DEBUGGING PRINTS END ---

    try:
        # Fetch job status from DynamoDB
        # --- DEBUGGING PRINTS START ---
        print(f"DEBUG: Attempting to fetch job {job_id} from DynamoDB.")
        # --- DEBUGGING PRINTS END ---
        job = dynamodb_service.get_job_status(job_id)
        # --- DEBUGGING PRINTS START ---
        print(f"DEBUG: DynamoDB raw response for {job_id}: {job}")
        # --- DEBUGGING PRINTS END ---

        if not job:
            # --- DEBUGGING PRINTS START ---
            print(f"DEBUG: Job {job_id} NOT found in DynamoDB. Raising 404.")
            # --- DEBUGGING PRINTS END ---
            raise HTTPException(status_code=404, detail="Job not found")

        status = job.get("status", "UNKNOWN")
        output_urls = job.get("output_s3_urls")
        error_message = job.get("error_message")
        created_at = job.get("created_at")
        updated_at = job.get("updated_at")
        video_duration = job.get("video_duration")
        # Convert Decimal back to float for API response
        if video_duration is not None and hasattr(video_duration, 'as_tuple'):
            video_duration = float(video_duration)

        # --- DEBUGGING PRINTS START ---
        print(f"DEBUG: Job {job_id} found. Status: '{status}', raw output_urls: {output_urls}, video_duration: {video_duration}")
        # --- DEBUGGING PRINTS END ---


        # If job is completed, generate presigned download URLs
        presigned_urls = None
        if status == "COMPLETED" and output_urls:
            # --- DEBUGGING PRINTS START ---
            print(f"DEBUG: Job {job_id} is COMPLETED and has output_urls. Attempting to generate presigned URLs.")
            # --- DEBUGGING PRINTS END ---
            presigned_urls = []

            # --- DEBUGGING BLOCK START: Wrap loop in try/except ---
            try:
                for s3_key in output_urls: # Now these are S3 keys, not URLs
                    # --- DEBUGGING PRINTS START ---
                    print(f"DEBUG: Processing S3 key for presigning: {s3_key}")
                    # --- DEBUGGING PRINTS END ---

                    # Generate presigned URL directly from S3 key
                    presigned = generate_presigned_url(
                        bucket_name=settings.AWS_BUCKET_NAME,
                        object_key=s3_key,
                        client_method='get_object',
                        content_type=None, # For GET operations, content_type is often not needed
                        expiration=3600  # 1 hour
                    )
                    presigned_urls.append(presigned)
                    # --- DEBUGGING PRINTS START ---
                    print(f"DEBUG: Generated presigned URL for {s3_key}: {presigned[:60]}...") # Print truncated URL
                    # --- DEBUGGING PRINTS END ---
            except Exception as inner_e:
                # --- DEBUGGING PRINTS START ---
                print(f"DEBUG: ERROR CAUGHT DURING PRESIGNED URL GENERATION LOOP FOR JOB {job_id}: {type(inner_e).__name__}: {str(inner_e)}")
                traceback.print_exc() # Print inner traceback
                # --- DEBUGGING PRINTS END ---
                # Re-raise the exception to be caught by the outer handler for the 500
                raise

        # --- DEBUGGING PRINTS START ---
        print(f"DEBUG: Returning JobStatusResponse for {job_id}. Final presigned_urls count: {len(presigned_urls) if presigned_urls else 0}")
        # --- DEBUGGING PRINTS END ---
        return JobStatusResponse(
            job_id=job_id,
            status=status,
            output_urls=presigned_urls if presigned_urls else None,
            error_message=error_message,
            created_at=created_at,
            updated_at=updated_at,
            video_duration=video_duration
        )
    except HTTPException:
        # Re-raise explicit HTTPExceptions (like the 404)
        raise
    except Exception as e:
        # Catch-all for unexpected errors, log explicitly before raising 500
        # --- DEBUGGING PRINTS START ---
        print(f"DEBUG: CRITICAL UNHANDLED ERROR IN get_job_status FOR JOB {job_id}: {type(e).__name__}: {str(e)}")
        traceback.print_exc() # Print full traceback to console
        # --- DEBUGGING PRINTS END ---
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")



@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Video processing API is running"}


@router.get("/routes")
async def list_routes():
    """List all available routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"routes": routes}


@router.get("/debug/aws")
async def debug_aws():
    """Debug endpoint to test AWS configuration"""
    try:
        print(f"DEBUG: AWS_REGION = {settings.AWS_REGION}")
        print(f"DEBUG: AWS_BUCKET_NAME = {settings.AWS_BUCKET_NAME}")
        print(f"DEBUG: AWS_ACCESS_KEY_ID = {'SET' if settings.AWS_ACCESS_KEY_ID else 'NOT SET'}")
        print(f"DEBUG: AWS_SECRET_ACCESS_KEY = {'SET' if settings.AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
        
        # Test S3 connection
        from s3_utils import generate_presigned_url
        test_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key="test.txt",
            client_method='get_object',
            content_type=None,
            expiration=60
        )
        
        return {
            "status": "success",
            "aws_region": settings.AWS_REGION,
            "aws_bucket": settings.AWS_BUCKET_NAME,
            "aws_credentials": "SET" if settings.AWS_ACCESS_KEY_ID else "NOT SET",
            "test_presigned_url": test_url[:50] + "..." if test_url else None
        }
    except Exception as e:
        print(f"DEBUG: AWS test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "aws_region": getattr(settings, 'AWS_REGION', 'NOT SET'),
            "aws_bucket": getattr(settings, 'AWS_BUCKET_NAME', 'NOT SET'),
            "aws_credentials": "SET" if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else "NOT SET"
        }


@router.post("/video/analyze-duration", response_model=AnalyzeDurationResponse)
async def analyze_duration(request: AnalyzeDurationRequest) -> AnalyzeDurationResponse:
    """
    Analyze video duration and calculate segment count based on cutting options

    This endpoint allows the frontend to preview how many segments will be created
    for a given video and cutting parameters before starting the actual processing job.
    """
    print(f"DEBUG: analyze-duration called with request: {request}")
    print(f"DEBUG: AWS_BUCKET_NAME = {settings.AWS_BUCKET_NAME}")
    print(f"DEBUG: s3_key = {request.s3_key}")
    
    try:
        # Test if file exists in S3 first
        from s3_utils import get_s3_client
        try:
            print(f"DEBUG: Testing if file exists in S3: {settings.AWS_BUCKET_NAME}/{request.s3_key}")
            s3_client = get_s3_client()
            response = s3_client.head_object(Bucket=settings.AWS_BUCKET_NAME, Key=request.s3_key)
            print(f"DEBUG: S3 file exists, size: {response.get('ContentLength', 'unknown')}")
        except Exception as s3_error:
            print(f"DEBUG: S3 head_object failed: {type(s3_error).__name__}: {str(s3_error)}")
            raise HTTPException(status_code=404, detail=f"Video file not found in S3: {str(s3_error)}")
        
        # Try to get duration from DynamoDB first (if it was stored during upload)
        total_duration = None
        try:
            # Extract job_id from s3_key: uploads/{job_id}/{filename}
            job_id = request.s3_key.split('/')[1] if len(request.s3_key.split('/')) > 2 else None
            if job_id:
                print(f"DEBUG: Trying to get duration from DynamoDB for job_id: {job_id}")
                job_data = dynamodb_service.get_job_status(job_id)
                if job_data and job_data.get('video_duration'):
                    total_duration = job_data['video_duration']
                    # Convert Decimal back to float for calculations
                    if total_duration is not None and hasattr(total_duration, 'as_tuple'):
                        total_duration = float(total_duration)
                    print(f"DEBUG: Found duration in DynamoDB: {total_duration} seconds")
        except Exception as db_error:
            print(f"DEBUG: Failed to get duration from DynamoDB: {db_error}")
        
        # If not found in DynamoDB, get it from S3 using FFmpeg
        if total_duration is None:
            print(f"DEBUG: Duration not in DynamoDB, getting from S3 using FFmpeg")
            total_duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, request.s3_key)
            print(f"DEBUG: Video duration from S3: {total_duration} seconds")
        else:
            print(f"DEBUG: Using cached duration: {total_duration} seconds")

        # Calculate segments based on cutting options
        print(f"DEBUG: Cutting options: {request.cutting_options}")
        num_segments, segment_times = calculate_segments(total_duration, request.cutting_options)
        print(f"DEBUG: Calculated {num_segments} segments")

        # Extract just the durations for the response
        segment_durations = [end - start for start, end in segment_times]

        response = AnalyzeDurationResponse(
            total_duration=total_duration,
            num_segments=num_segments,
            segment_durations=segment_durations
        )
        print(f"DEBUG: Returning response: {response}")
        return response

    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    except FileNotFoundError:
        print(f"DEBUG: FileNotFoundError caught")
        raise HTTPException(status_code=404, detail="Video file not found in S3")
    except Exception as e:
        print(f"DEBUG: Unexpected error in analyze-duration: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
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


# --- Redis PubSub utility for SSE ---
# This function should return the async Redis client, not the pubsub object
async def get_async_redis_client(): # Renamed for clarity
    """
    Returns an async Redis client connected to the configured Redis URL.
    """
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client

@router.get("/job-progress/{job_id}/stream", response_class=EventSourceResponse)
async def job_progress_stream(job_id: str):
    """
    SSE endpoint to stream job progress updates from Redis Pub/Sub to the frontend.
    Uses pubsub.listen() async iterator for robust message streaming.
    """
    print(f"DEBUG: SSE endpoint called for job_id: {job_id}")
    print(f"DEBUG: REDIS_URL = {settings.REDIS_URL}")
    
    async def event_generator():
        try:
            print(f"DEBUG: Creating Redis connection for job {job_id}")
            redis_conn = await get_async_redis_client_from_pool()
            print(f"DEBUG: Redis connection created successfully for job {job_id}")
            
            pubsub = redis_conn.pubsub()
            channel = f"job_progress_{job_id}"
            print(f"DEBUG: Subscribing to Redis channel: {channel}")
            await pubsub.subscribe(channel)
            print(f"DEBUG: SSE subscribed to {channel}")
            
            # Send initial connection message
            yield {"event": "connected", "data": json.dumps({"message": f"Connected to progress stream for job {job_id}"})}
            
            try:
                async for message in pubsub.listen():
                    print(f"DEBUG: SSE Generator - Received message from Redis on channel {channel}: {message}")
                    if message is None:
                        continue
                    if message["type"] == "message":
                        print(f"DEBUG: SSE Generator - Yielding message to client: {message['data']}")
                        yield {"event": "progress", "data": message["data"]}
            except asyncio.CancelledError:
                print(f"DEBUG: SSE client disconnected from {channel}")
            except Exception as e:
                print(f"DEBUG: ERROR in SSE event_generator for job {job_id}: {type(e).__name__}: {str(e)}")
                yield {"event": "error", "data": json.dumps({"message": f"Server error: {e}"})}
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception as cleanup_error:
                    print(f"DEBUG: Error during pubsub cleanup: {cleanup_error}")
                print(f"DEBUG: SSE pubsub unsubscribed and connections closed for {job_id}")
        except Exception as e:
            print(f"DEBUG: CRITICAL ERROR in SSE setup for job {job_id}: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            yield {"event": "error", "data": json.dumps({"message": f"Failed to setup SSE: {str(e)}"})}
    
    return EventSourceResponse(event_generator())



@router.options("/videos")
async def options_videos():
    from fastapi.responses import Response
    return Response(status_code=200)

@router.get("/videos")
async def list_videos(user_id: str = None):
    """
    List all video metadata entries for the current user (or all users if user_id is not provided).
    Returns a list of VideoMetadata dicts.
    """
    try:
        # If you have authentication, extract user_id from token/session instead of query param
        videos = dynamodb_service.list_videos(user_id=user_id)
        # Optionally filter/transform to match VideoMetadata interface
        return videos
    except Exception as e:
        print(f"[ERROR] Failed to list videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")


# === SEGMENT MANAGEMENT ENDPOINTS ===

@router.post("/segments", response_model=VideoSegment)
async def create_segment(request: SegmentCreateRequest, user_id: str):
    """
    Create a new video segment.
    """
    try:
        # Generate unique segment ID
        segment_id = f"seg_{uuid.uuid4().hex[:12]}"
        
        # Create segment data
        segment_data = VideoSegment(
            segment_id=segment_id,
            video_id=request.video_id,
            user_id=user_id,
            segment_type=request.segment_type,
            segment_number=request.segment_number,
            s3_key=request.s3_key,
            duration=request.duration,
            file_size=request.file_size,
            content_type=request.content_type,
            title=request.title,
            description=request.description,
            tags=request.tags or []
        )
        
        # Save to DynamoDB
        created_segment = dynamodb_service.create_segment(segment_data)
        return created_segment
        
    except Exception as e:
        print(f"[ERROR] Failed to create segment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create segment: {str(e)}")


@router.get("/segments/{segment_id}", response_model=VideoSegment)
async def get_segment(segment_id: str):
    """
    Get a specific video segment by ID.
    """
    try:
        segment = dynamodb_service.get_segment(segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        return segment
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get segment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get segment: {str(e)}")


@router.get("/videos/{video_id}/segments", response_model=SegmentListResponse)
async def list_video_segments(video_id: str, segment_type: SegmentType = None):
    """
    List all segments for a specific video.
    """
    try:
        segments = dynamodb_service.list_segments_by_video(video_id, segment_type)
        return SegmentListResponse(
            segments=segments,
            total_count=len(segments),
            page=1,
            page_size=len(segments)
        )
    except Exception as e:
        print(f"[ERROR] Failed to list video segments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list video segments: {str(e)}")


@router.get("/segments", response_model=SegmentListResponse)
async def list_user_segments(
    user_id: str,
    segment_type: SegmentType = None,
    min_duration: float = None,
    max_duration: float = None,
    tags: str = None,
    has_social_media: bool = None,
    platform: SocialMediaPlatform = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """
    List all segments for a user with filtering options.
    """
    try:
        # Build filters
        filters = {}
        if segment_type:
            filters["segment_type"] = segment_type
        if min_duration:
            filters["min_duration"] = min_duration
        if max_duration:
            filters["max_duration"] = max_duration
        if tags:
            filters["tags"] = tags.split(",")
        if has_social_media is not None:
            filters["has_social_media"] = has_social_media
        if platform:
            filters["platform"] = platform
        
        segments = dynamodb_service.list_segments_by_user(user_id, filters)
        
        # Apply sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "created_at":
            segments.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "duration":
            segments.sort(key=lambda x: x.duration, reverse=reverse)
        elif sort_by == "file_size":
            segments.sort(key=lambda x: x.file_size, reverse=reverse)
        
        return SegmentListResponse(
            segments=segments,
            total_count=len(segments),
            page=1,
            page_size=len(segments)
        )
    except Exception as e:
        print(f"[ERROR] Failed to list user segments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list user segments: {str(e)}")


@router.put("/segments/{segment_id}", response_model=VideoSegment)
async def update_segment(segment_id: str, request: SegmentUpdateRequest):
    """
    Update a video segment.
    """
    try:
        # Build update data
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.description is not None:
            update_data["description"] = request.description
        if request.tags is not None:
            update_data["tags"] = request.tags
        
        updated_segment = dynamodb_service.update_segment(segment_id, update_data)
        if not updated_segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        return updated_segment
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to update segment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update segment: {str(e)}")


@router.delete("/segments/{segment_id}")
async def delete_segment(segment_id: str):
    """
    Delete a video segment.
    """
    try:
        success = dynamodb_service.delete_segment(segment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        return {"message": "Segment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to delete segment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete segment: {str(e)}")


@router.post("/segments/{segment_id}/social-media", response_model=VideoSegment)
async def sync_social_media(segment_id: str, request: SocialMediaSyncRequest):
    """
    Sync social media metrics for a segment.
    """
    try:
        # Create social media usage data
        social_media_usage = SocialMediaUsage(
            platform=request.platform,
            post_id=request.post_id,
            post_url=request.post_url,
            posted_at=iso_utc_now(),
            views=0,
            likes=0,
            shares=0,
            comments=0
        )
        
        # Add to segment
        updated_segment = dynamodb_service.add_social_media_usage(segment_id, social_media_usage)
        if not updated_segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        return updated_segment
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to sync social media: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync social media: {str(e)}")


@router.get("/segments/{segment_id}/analytics", response_model=SocialMediaAnalyticsResponse)
async def get_segment_analytics(segment_id: str):
    """
    Get social media analytics for a segment.
    """
    try:
        analytics = dynamodb_service.get_social_media_analytics(segment_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Segment not found or no social media data")
        
        return SocialMediaAnalyticsResponse(**analytics)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get segment analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get segment analytics: {str(e)}")


@router.get("/segments/{segment_id}/download")
async def get_segment_download_url(segment_id: str):
    """
    Get a presigned download URL for a segment.
    """
    try:
        segment = dynamodb_service.get_segment(segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")
        
        # Generate presigned URL for download
        presigned_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=segment.s3_key,
            client_method='get_object',
            expiration=3600  # 1 hour
        )
        
        return {
            "segment_id": segment_id,
            "download_url": presigned_url,
            "expires_in": 3600
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get segment download URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get segment download URL: {str(e)}")


# Include router in app
app.include_router(router)

# Add debug endpoint directly to app (without /api prefix)
@app.get("/debug/aws")
async def debug_aws_direct():
    """Debug endpoint to test AWS configuration (direct route)"""
    try:
        print(f"DEBUG: AWS_REGION = {settings.AWS_REGION}")
        print(f"DEBUG: AWS_BUCKET_NAME = {settings.AWS_BUCKET_NAME}")
        print(f"DEBUG: AWS_ACCESS_KEY_ID = {'SET' if settings.AWS_ACCESS_KEY_ID else 'NOT SET'}")
        print(f"DEBUG: AWS_SECRET_ACCESS_KEY = {'SET' if settings.AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
        
        return {
            "status": "success",
            "aws_region": settings.AWS_REGION,
            "aws_bucket": settings.AWS_BUCKET_NAME,
            "aws_credentials": "SET" if settings.AWS_ACCESS_KEY_ID else "NOT SET"
        }
    except Exception as e:
        print(f"DEBUG: AWS test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "aws_region": getattr(settings, 'AWS_REGION', 'NOT SET'),
            "aws_bucket": getattr(settings, 'AWS_BUCKET_NAME', 'NOT SET'),
            "aws_credentials": "SET" if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else "NOT SET"
        }


@app.get("/debug/redis")
async def debug_redis():
    """Debug endpoint to test Redis connection"""
    try:
        print(f"DEBUG: REDIS_URL = {settings.REDIS_URL}")
        
        # Test Redis connection
        redis_conn = await get_async_redis_client_from_pool()
        await redis_conn.ping()
        
        # Test pubsub
        pubsub = redis_conn.pubsub()
        test_channel = "test_channel"
        await pubsub.subscribe(test_channel)
        
        # Send a test message
        await redis_conn.publish(test_channel, "test_message")
        
        # Wait for message
        message = await pubsub.get_message(timeout=1)
        
        await pubsub.unsubscribe(test_channel)
        await pubsub.close()
        
        return {
            "status": "success",
            "redis_url": settings.REDIS_URL,
            "connection": "OK",
            "pubsub_test": "OK" if message else "FAILED"
        }
    except Exception as e:
        print(f"DEBUG: Redis test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "redis_url": getattr(settings, 'REDIS_URL', 'NOT SET')
        }


@app.get("/debug/ffmpeg")
async def debug_ffmpeg():
    """Debug endpoint to test FFmpeg installation"""
    try:
        import subprocess
        
        # Test if ffprobe is available
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return {
                "status": "success",
                "ffmpeg_available": True,
                "version": version_line,
                "ffprobe_path": "available"
            }
        else:
            return {
                "status": "error",
                "ffmpeg_available": False,
                "error": result.stderr
            }
    except FileNotFoundError:
        return {
            "status": "error",
            "ffmpeg_available": False,
            "error": "ffprobe not found in PATH"
        }
    except Exception as e:
        return {
            "status": "error",
            "ffmpeg_available": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
