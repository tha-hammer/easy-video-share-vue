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
from dynamodb_service import iso_utc_now, table
from tasks import process_video_task, celery_app
from video_processor import get_video_duration_from_s3, calculate_segments
from config import settings
from lambda_integration import use_lambda_processing, trigger_lambda_processing, test_lambda_connectivity, validate_lambda_config, trigger_thumbnail_generation, trigger_text_overlay_processing
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as redis
import asyncio
import json
from datetime import datetime,timedelta, timezone
import os
import time
import boto3

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
        print(f"DEBUG: Redis URL: {settings.REDIS_URL}")
        print(f"DEBUG: REDISHOST: {settings.REDISHOST}")
        print(f"DEBUG: REDISPORT: {settings.REDISPORT}")
        print(f"DEBUG: REDIS_PASSWORD: {'SET' if settings.REDIS_PASSWORD else 'NOT SET'}")
        
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

        # Test Redis connection before dispatching task
        try:
            print(f"DEBUG: Testing Redis connection before dispatching task...")
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            print(f"DEBUG: Redis connection test successful")
        except Exception as redis_error:
            print(f"DEBUG: Redis connection test failed: {type(redis_error).__name__}: {str(redis_error)}")
            raise HTTPException(status_code=500, detail=f"Redis connection failed: {str(redis_error)}")

        # Dispatch video processing task to Celery
        try:
            print(f"DEBUG: Dispatching Celery task...")
            task = process_video_task.delay(
                request.s3_key,
                request.job_id,
                cutting_options_dict,
                text_strategy_str,
                text_input_dict,
                request.user_id or "anonymous"  # Use provided user_id or default to "anonymous"
            )
            print(f"DEBUG: Celery task dispatched successfully: {task.id}")
        except Exception as celery_error:
            print(f"DEBUG: Celery task dispatch failed: {type(celery_error).__name__}: {str(celery_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to dispatch video processing task: {str(celery_error)}")

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
            print(f"DEBUG: DynamoDB job entry created successfully")
        except Exception as e:
            print(f"[DynamoDB] Failed to create job entry in /upload/complete-multipart for job_id={request.job_id}: {e}")

        return JobCreatedResponse(
            job_id=request.job_id,
            status="QUEUED",
            message="Video processing job has been queued successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
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

        # Determine processing method (Lambda vs Celery)
        request_data = {
            's3_key': request.s3_key,
            'job_id': request.job_id,
            'user_id': request.user_id or "anonymous",
            'file_size': request.file_size,
            'cutting_options': cutting_options_dict,
            'text_input': text_input_dict,
            'segment_duration': 30  # Default segment duration
        }
        
        if use_lambda_processing(request_data):
            # Use Lambda processing
            print(f"DEBUG: Using Lambda processing for job {request.job_id}")
            try:
                lambda_result = await trigger_lambda_processing(request_data)
                print(f"DEBUG: Lambda processing triggered: {lambda_result}")
            except Exception as lambda_error:
                print(f"DEBUG: Lambda processing failed, falling back to Celery: {lambda_error}")
                # Fallback to Celery if Lambda fails
                task = process_video_task.delay(
                    request.s3_key,
                    request.job_id,
                    cutting_options_dict,
                    text_strategy_str,
                    text_input_dict,
                    request.user_id or "anonymous"
                )
        else:
            # Use Celery processing
            print(f"DEBUG: Using Celery processing for job {request.job_id}")
            task = process_video_task.delay(
                request.s3_key,
                request.job_id,
                cutting_options_dict,
                text_strategy_str,
                text_input_dict,
                request.user_id or "anonymous"
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

@router.get("/lambda/status")
async def lambda_status():
    """Get Lambda processing status and configuration"""
    try:
        # Validate Lambda configuration
        config = validate_lambda_config()
        
        # Test Lambda connectivity
        connectivity = await test_lambda_connectivity()
        
        return {
            "lambda_enabled": config['use_lambda_processing'],
            "function_name": config['lambda_function_name'],
            "configuration": config,
            "connectivity": connectivity,
            "processing_method": "Lambda" if config['use_lambda_processing'] else "Celery"
        }
    except Exception as e:
        return {
            "error": str(e),
            "lambda_enabled": False,
            "processing_method": "Celery (fallback)"
        }


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


@router.post("/videos/url")
async def get_video_url(request: dict):
    """
    Get a presigned URL for a video file.
    """
    try:
        bucket_location = request.get("bucket_location")
        if not bucket_location:
            raise HTTPException(status_code=400, detail="bucket_location is required")
        
        # Generate presigned URL for video access
        presigned_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=bucket_location,
            client_method='get_object',
            expiration=3600  # 1 hour
        )
        
        return {
            "url": presigned_url,
            "expires_in": 3600
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get video URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get video URL: {str(e)}")


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
        current_time = iso_utc_now()
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
            tags=request.tags or [],
            created_at=current_time,
            updated_at=current_time
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
        print(f"[DEBUG] API endpoint called with video_id: {video_id}")
        print(f"[DEBUG] Segment type parameter: {segment_type}")
        
        segments = dynamodb_service.list_segments_by_video(video_id, segment_type)
        
        print(f"[DEBUG] API returning {len(segments)} segments")
        
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
    user_id: str = None,
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
    This endpoint aggregates segments from video records using output_s3_urls.
    """
    try:
        if not user_id:
            # If no user_id provided, return empty list
            return SegmentListResponse(
                segments=[],
                total_count=0,
                page=1,
                page_size=0
            )
        
        # Get all videos for the user and extract segments from output_s3_urls
        all_segments = []
        
        # Get user's videos
        user_videos = dynamodb_service.list_videos(user_id)
        
        for video in user_videos:
            output_s3_urls = video.get("output_s3_urls", [])
            if not output_s3_urls:
                continue
                
            # Create segment objects from output_s3_urls
            for i, s3_key in enumerate(output_s3_urls, 1):
                try:
                    # Generate segment ID
                    segment_id = f"seg_{video['video_id']}_{i:03d}"
                    
                    # Extract filename from s3_key
                    filename = s3_key.split("/")[-1] if s3_key else None
                    
                    # Create segment data
                    segment_data = VideoSegment(
                        segment_id=segment_id,
                        video_id=video["video_id"],
                        user_id=video.get("user_id", ""),
                        segment_type=SegmentType.PROCESSED,
                        segment_number=i,
                        s3_key=s3_key,
                        duration=30.0,  # Default duration, could be enhanced to get from S3
                        file_size=0,    # Default size, could be enhanced to get from S3
                        content_type="video/mp4",
                        title=f"{video.get('title', 'Video')} - Part {i}",
                        description=f"Processed segment {i} of {len(output_s3_urls)}",
                        tags=video.get("tags", []),
                        created_at=video.get("created_at", ""),
                        updated_at=video.get("updated_at", ""),
                        filename=filename,
                        download_count=0,
                        social_media_usage=[]
                    )
                    
                    all_segments.append(segment_data)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to create segment {i} for video {video['video_id']}: {e}")
                    continue
        
        # Apply filters
        filtered_segments = all_segments
        
        # Filter by segment type
        if segment_type:
            filtered_segments = [s for s in filtered_segments if s.segment_type == segment_type]
        
        # Filter by duration
        if min_duration is not None:
            filtered_segments = [s for s in filtered_segments if s.duration >= min_duration]
        if max_duration is not None:
            filtered_segments = [s for s in filtered_segments if s.duration <= max_duration]
        
        # Filter by tags
        if tags:
            required_tags = set(tags.split(","))
            filtered_segments = [s for s in filtered_segments if s.tags and required_tags.issubset(set(s.tags))]
        
        # Filter by social media usage (not implemented for output_s3_urls approach)
        if has_social_media is not None:
            # For now, return all segments since social media usage is not stored in video records
            pass
        
        # Filter by platform (not implemented for output_s3_urls approach)
        if platform:
            # For now, return all segments since social media usage is not stored in video records
            pass
        
        # Apply sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "created_at":
            filtered_segments.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "duration":
            filtered_segments.sort(key=lambda x: x.duration, reverse=reverse)
        elif sort_by == "file_size":
            filtered_segments.sort(key=lambda x: x.file_size, reverse=reverse)
        elif sort_by == "name":
            filtered_segments.sort(key=lambda x: x.title or x.filename or "", reverse=reverse)
        
        return SegmentListResponse(
            segments=filtered_segments,
            total_count=len(filtered_segments),
            page=1,
            page_size=len(filtered_segments)
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
    Get a presigned download URL for a segment and increment download count.
    """
    try:
        # Parse segment_id to extract video_id and segment number
        # Format: seg_{video_id}_{segment_number:03d}
        if not segment_id.startswith("seg_"):
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        # Remove "seg_" prefix
        segment_id_without_prefix = segment_id[4:]
        
        # Find the last underscore to separate video_id from segment_number
        last_underscore_index = segment_id_without_prefix.rfind("_")
        if last_underscore_index == -1:
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        video_id = segment_id_without_prefix[:last_underscore_index]
        segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
        
        try:
            segment_number = int(segment_number_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid segment number format")
        
        # Get the video record to find the segment
        video_resp = dynamodb_service.table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get the output_s3_urls array
        output_s3_urls = video_item.get("output_s3_urls", [])
        if not output_s3_urls:
            raise HTTPException(status_code=404, detail="No segments found for this video")
        
        # Check if segment number is valid
        if segment_number < 1 or segment_number > len(output_s3_urls):
            raise HTTPException(status_code=404, detail="Segment not found")
        
        # Get the s3_key for this segment
        s3_key_or_url = output_s3_urls[segment_number - 1]  # Convert to 0-based index
        
        # Extract object key from URL if it's a full URL
        if s3_key_or_url.startswith('http'):
            # It's a full URL, extract the object key
            from urllib.parse import urlparse, unquote
            parsed_url = urlparse(s3_key_or_url)
            s3_key = unquote(parsed_url.path.lstrip('/'))
        else:
            # It's already an object key
            s3_key = s3_key_or_url
        
        # Generate presigned URL for download
        presigned_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=s3_key,
            client_method='get_object',
            expiration=3600  # 1 hour
        )
        
        # For now, return download count as 0 since we're not storing it separately
        # In a future enhancement, we could store download counts in a separate table
        download_count = 0
        
        return {
            "segment_id": segment_id,
            "download_url": presigned_url,
            "download_count": download_count,
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get segment download URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get segment download URL: {str(e)}")


@router.post("/segments/{segment_id}/generate-thumbnail")
async def generate_segment_thumbnail(segment_id: str):
    """
    Generate a thumbnail for a video segment using Lambda processing
    """
    try:
        print(f"[DEBUG] Generating thumbnail for segment: {segment_id}")
        
        # Parse segment_id to extract video_id
        if not segment_id.startswith("seg_"):
            raise HTTPException(status_code=400, detail="Invalid segment ID format - must start with 'seg_'")
        
        # Extract video_id from segment_id
        segment_id_without_prefix = segment_id[4:]  # Remove "seg_" prefix
        last_underscore_index = segment_id_without_prefix.rfind("_")
        if last_underscore_index == -1:
            raise HTTPException(status_code=400, detail="Invalid segment ID format - missing segment number")
        
        video_id = segment_id_without_prefix[:last_underscore_index]
        segment_number = segment_id_without_prefix[last_underscore_index + 1:]
        
        print(f"[DEBUG] Parsed segment ID: video_id='{video_id}', segment_number='{segment_number}'")
        
        # Validate video_id format (should be a UUID or similar)
        if not video_id or len(video_id) < 10:
            raise HTTPException(status_code=400, detail=f"Invalid video ID extracted: '{video_id}'")
        
        # Check if Lambda integration is available
        try:
            from lambda_integration import trigger_thumbnail_generation
        except ImportError as e:
            print(f"[ERROR] Lambda integration import failed: {e}")
            raise HTTPException(status_code=500, detail="Lambda integration not available")
        
        print(f"[DEBUG] Triggering Lambda thumbnail generation...")
        
        # Trigger Lambda thumbnail generation
        try:
            result = await trigger_thumbnail_generation(video_id, segment_id)
            print(f"[DEBUG] Lambda result: {result}")
        except Exception as lambda_error:
            print(f"[ERROR] Lambda invocation failed: {lambda_error}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Lambda invocation failed: {str(lambda_error)}")
        
        if result['status'] == 'success':
            # Extract thumbnail URL from Lambda response
            lambda_response = result['lambda_response']
            print(f"[DEBUG] Lambda response: {lambda_response}")
            
            if lambda_response.get('statusCode') == 200:
                response_body = json.loads(lambda_response['body'])
                thumbnail_url = response_body.get('thumbnail_url')
                
                if not thumbnail_url:
                    raise HTTPException(status_code=500, detail="Lambda response missing thumbnail_url")
                
                print(f"[DEBUG] Thumbnail generated successfully: {thumbnail_url}")
                
                return {
                    "segment_id": segment_id,
                    "thumbnail_url": thumbnail_url,
                    "status": "success",
                    "message": "Thumbnail generated successfully"
                }
            else:
                error_detail = f"Lambda returned status {lambda_response.get('statusCode')}"
                if lambda_response.get('body'):
                    try:
                        error_body = json.loads(lambda_response['body'])
                        error_detail += f": {error_body}"
                    except:
                        error_detail += f": {lambda_response['body']}"
                
                print(f"[ERROR] Lambda thumbnail generation failed: {error_detail}")
                raise HTTPException(status_code=500, detail=f"Lambda thumbnail generation failed: {error_detail}")
        else:
            error_detail = f"Lambda invocation failed with status: {result.get('status')}"
            print(f"[ERROR] {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in thumbnail generation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/segments/{segment_id}/text-overlays")
async def save_text_overlays(segment_id: str, request: dict):
    """
    Save text overlays for a video segment
    """
    try:
        overlays = request.get("overlays", [])
        print(f"[DEBUG] Saving text overlays for segment: {segment_id}")
        print(f"[DEBUG] Number of overlays: {len(overlays)}")
        
        # Parse segment_id to extract video_id and segment number
        if not segment_id.startswith("seg_"):
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        # Remove "seg_" prefix
        segment_id_without_prefix = segment_id[4:]
        
        # Find the last underscore to separate video_id from segment_number
        last_underscore_index = segment_id_without_prefix.rfind("_")
        if last_underscore_index == -1:
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        video_id = segment_id_without_prefix[:last_underscore_index]
        segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
        
        try:
            segment_number = int(segment_number_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid segment number format")
        
        print(f"[DEBUG] Extracted video_id: {video_id}, segment_number: {segment_number}")
        
        # Store text overlays in DynamoDB
        # For now, we'll store them in the video_segments table
        # In a production system, you might want a separate table for text overlays
        
        try:
            # Update the segment with text overlays
            segments_table = boto3.resource('dynamodb', region_name='us-east-1').Table('easy-video-share-video-segments')
            
            # Store the overlays data
            timestamp = datetime.now().isoformat()
            
            response = segments_table.put_item(
                Item={
                    'segment_id': segment_id,
                    'video_id': video_id,
                    'segment_number': segment_number,
                    'text_overlays': overlays,
                    'updated_at': timestamp,
                    'created_at': timestamp
                }
            )
            
            print(f"[DEBUG] Text overlays saved successfully for segment: {segment_id}")
            
            return {
                "segment_id": segment_id,
                "video_id": video_id,
                "segment_number": segment_number,
                "overlays_count": len(overlays),
                "message": "Text overlays saved successfully",
                "updated_at": timestamp
            }
            
        except Exception as dynamo_error:
            print(f"[ERROR] Failed to save to DynamoDB: {dynamo_error}")
            # Fall back to simple success response if DynamoDB fails
            return {
                "segment_id": segment_id,
                "video_id": video_id,
                "segment_number": segment_number,
                "overlays_count": len(overlays),
                "message": "Text overlays received successfully (temporary storage)",
                "note": "DynamoDB storage temporarily unavailable"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to save text overlays: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save text overlays: {str(e)}")


@router.get("/segments/{segment_id}/text-overlays")
async def get_text_overlays(segment_id: str):
    """
    Get text overlays for a video segment
    """
    try:
        print(f"[DEBUG] Getting text overlays for segment: {segment_id}")
        
        # Parse segment_id to extract video_id and segment number
        if not segment_id.startswith("seg_"):
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        # Remove "seg_" prefix
        segment_id_without_prefix = segment_id[4:]
        
        # Find the last underscore to separate video_id from segment_number
        last_underscore_index = segment_id_without_prefix.rfind("_")
        if last_underscore_index == -1:
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        video_id = segment_id_without_prefix[:last_underscore_index]
        segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
        
        try:
            segment_number = int(segment_number_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid segment number format")
        
        print(f"[DEBUG] Extracted video_id: {video_id}, segment_number: {segment_number}")
        
        # Get text overlays from DynamoDB
        try:
            segments_table = boto3.resource('dynamodb', region_name='us-east-1').Table('easy-video-share-video-segments')
            
            response = segments_table.get_item(
                Key={'segment_id': segment_id}
            )
            
            item = response.get('Item', {})
            text_overlays = item.get('text_overlays', [])
            
            print(f"[DEBUG] Retrieved {len(text_overlays)} text overlays for segment: {segment_id}")
            
            return {
                "segment_id": segment_id,
                "video_id": video_id,
                "segment_number": segment_number,
                "text_overlays": text_overlays,
                "overlays_count": len(text_overlays),
                "updated_at": item.get('updated_at'),
                "created_at": item.get('created_at')
            }
            
        except Exception as dynamo_error:
            print(f"[ERROR] Failed to retrieve from DynamoDB: {dynamo_error}")
            return {
                "segment_id": segment_id,
                "video_id": video_id,
                "segment_number": segment_number,
                "text_overlays": [],
                "overlays_count": 0,
                "message": "No text overlays found or DynamoDB temporarily unavailable"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get text overlays: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get text overlays: {str(e)}")


@router.post("/segments/{segment_id}/process-with-text-overlays")
async def process_segment_with_text_overlays(segment_id: str, request: dict):
    """
    Process a video segment with text overlays applied using Lambda
    """
    try:
        # Handle both request formats - overlays array or ffmpeg_filters array
        overlays = request.get("overlays", [])
        ffmpeg_filters = request.get("ffmpeg_filters", [])
        ffmpeg_command = request.get("ffmpeg_command", "")
        processing_type = request.get("processing_type", "text_overlays")
        
        print(f"[DEBUG] Processing segment with text overlays: {segment_id}")
        print(f"[DEBUG] Request data: {request}")
        print(f"[DEBUG] Number of overlays: {len(overlays)}")
        print(f"[DEBUG] Number of ffmpeg_filters: {len(ffmpeg_filters)}")
        print(f"[DEBUG] Processing type: {processing_type}")
        
        # Parse segment_id to extract video_id and segment number
        if not segment_id.startswith("seg_"):
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        # Remove "seg_" prefix
        segment_id_without_prefix = segment_id[4:]
        
        # Find the last underscore to separate video_id from segment_number
        last_underscore_index = segment_id_without_prefix.rfind("_")
        if last_underscore_index == -1:
            raise HTTPException(status_code=400, detail="Invalid segment ID format")
        
        video_id = segment_id_without_prefix[:last_underscore_index]
        segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
        
        try:
            segment_number = int(segment_number_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid segment number format")
        
        print(f"[DEBUG] Extracted video_id: {video_id}, segment_number: {segment_number}")
        
        # Prepare text overlays for Lambda processing
        text_overlays = []
        
        if overlays:
            # Convert overlays to Lambda format
            for overlay in overlays:
                text_overlay = {
                    'segment_id': segment_id,
                    'text': overlay.get('text', ''),
                    'x': overlay.get('x', 0),
                    'y': overlay.get('y', 0),
                    'fontSize': overlay.get('fontSize', 24),
                    'color': overlay.get('color', '#ffffff'),
                    'fontFamily': overlay.get('fontFamily', 'Arial'),
                    'shadow': overlay.get('shadow', {}),
                    'stroke': overlay.get('stroke', {})
                }
                text_overlays.append(text_overlay)
        
        if not text_overlays:
            raise HTTPException(status_code=400, detail="No valid text overlays to apply")
        
        # Import lambda integration
        from lambda_integration import trigger_text_overlay_processing
        
        # Trigger Lambda text overlay processing
        result = await trigger_text_overlay_processing(video_id, text_overlays)
        
        if result['status'] == 'success':
            # Generate a job_id for tracking
            job_id = f"job_{video_id}_{segment_number}_{uuid.uuid4().hex[:8]}"
            
            return {
                "job_id": job_id,
                "status": "processing",
                "segment_id": segment_id,
                "overlays_applied": len(text_overlays),
                "message": f"Successfully started processing segment with {len(text_overlays)} text overlays",
                "lambda_function": result['function_name'],
                "processing_type": result['processing_type']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger text overlay processing")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to process segment with text overlays: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process segment with text overlays: {str(e)}")


@router.post("/videos/{video_id}/process-segments-without-text")
async def process_segments_without_text(video_id: str, request: dict):
    """
    Process video segments WITHOUT text overlays (Phase 1)
    """
    try:
        segments = request.get("segments", [])
        text_data = request.get("textData", {})
        
        print(f"[DEBUG] Processing segments without text for video: {video_id}")
        print(f"[DEBUG] Number of segments: {len(segments)}")
        
        if not segments:
            raise HTTPException(status_code=400, detail="No segments provided")
        
        # Get the video record to find the source S3 key
        video_resp = table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get the source S3 key
        s3_key = video_item.get("s3_key")
        if not s3_key:
            raise HTTPException(status_code=400, detail="Source video S3 key not found")
        
        print(f"[DEBUG] Source video S3 key: {s3_key}")
        
        # Import lambda integration
        from lambda_integration import trigger_segment_processing_without_text
        
        # Generate job ID
        job_id = f"job_{video_id}_{int(time.time())}"
        
        # Trigger Lambda segment processing
        result = await trigger_segment_processing_without_text(video_id, s3_key, segments, job_id)
        
        if result['status'] == 'success':
            # Store text data for later use
            # TODO: Store text_data in DynamoDB for later text overlay processing
            
            return {
                "job_id": job_id,
                "status": "processing",
                "video_id": video_id,
                "segments_count": len(segments),
                "message": "Successfully started processing segments without text overlays",
                "lambda_function": result['function_name'],
                "processing_type": result['processing_type']
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to trigger segment processing")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to process segments without text: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process segments without text: {str(e)}")


@router.get("/videos/{video_id}/segments-status")
async def get_segments_status(video_id: str):
    """
    Check if segments are ready for text overlay design
    """
    try:
        print(f"[DEBUG] Getting segments status for video: {video_id}")
        
        # Get video job status
        video_resp = table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get segments from DynamoDB (simulated for now)
        # TODO: Implement actual DynamoDB segment retrieval
        segments = []
        segments_ready = False
        
        # For now, simulate segments based on video metadata
        if video_item.get("status") == "COMPLETED":
            output_s3_urls = video_item.get("output_s3_urls", [])
            for i, url in enumerate(output_s3_urls):
                segments.append({
                    "segment_id": f"seg_{video_id}_{i+1:03d}",
                    "segment_number": i + 1,
                    "duration": 30,  # Default duration
                    "raw_segment_ready": True,
                    "thumbnail_generated": False,
                    "text_overlays": []
                })
            segments_ready = True
        
        return {
            "video_id": video_id,
            "segments_ready": segments_ready,
            "segments": segments,
            "status": video_item.get("status", "UNKNOWN"),
            "can_design_text": segments_ready
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get segments status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get segments status: {str(e)}")


@router.post("/videos/{video_id}/save-text-data")
async def save_text_data(video_id: str, request: dict):
    """
    Save text data without processing (for later use)
    """
    try:
        text_data = request.get("textData", {})
        
        print(f"[DEBUG] Saving text data for video: {video_id}")
        print(f"[DEBUG] Text data: {text_data}")
        
        # TODO: Store text data in DynamoDB
        # For now, just update the video record
        video_resp = table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Update video record with text data
        table.update_item(
            Key={"video_id": video_id},
            UpdateExpression="SET text_data = :text_data, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":text_data": text_data,
                ":updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {
            "video_id": video_id,
            "status": "success",
            "message": "Text data saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to save text data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save text data: {str(e)}")


@router.get("/videos/{video_id}/text-data")
async def get_text_data(video_id: str):
    """
    Get saved text data for a video
    """
    try:
        print(f"[DEBUG] Getting text data for video: {video_id}")
        
        # Get video record
        video_resp = table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            raise HTTPException(status_code=404, detail="Video not found")
        
        text_data = video_item.get("text_data", {})
        
        return {
            "video_id": video_id,
            "text_data": text_data,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to get text data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get text data: {str(e)}")


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
        print(f"DEBUG: REDISHOST = {settings.REDISHOST}")
        print(f"DEBUG: REDISPORT = {settings.REDISPORT}")
        print(f"DEBUG: REDIS_PASSWORD = {'SET' if settings.REDIS_PASSWORD else 'NOT SET'}")
        
        # Test Redis connection with detailed error handling
        import redis
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            ping_result = redis_client.ping()
            print(f"DEBUG: Redis ping result: {ping_result}")
            
            if not ping_result:
                return {
                    "status": "error",
                    "error": "Redis ping failed",
                    "error_type": "RedisError",
                    "redis_url": settings.REDIS_URL,
                    "redis_host": settings.REDISHOST,
                    "redis_port": settings.REDISPORT,
                    "redis_password_set": bool(settings.REDIS_PASSWORD)
                }
        except redis.AuthenticationError as auth_error:
            print(f"DEBUG: Redis authentication error: {auth_error}")
            return {
                "status": "error",
                "error": f"Redis authentication failed: {str(auth_error)}",
                "error_type": "AuthenticationError",
                "redis_url": settings.REDIS_URL,
                "redis_host": settings.REDISHOST,
                "redis_port": settings.REDISPORT,
                "redis_password_set": bool(settings.REDIS_PASSWORD)
            }
        except redis.ConnectionError as conn_error:
            print(f"DEBUG: Redis connection error: {conn_error}")
            return {
                "status": "error",
                "error": f"Redis connection failed: {str(conn_error)}",
                "error_type": "ConnectionError",
                "redis_url": settings.REDIS_URL,
                "redis_host": settings.REDISHOST,
                "redis_port": settings.REDISPORT,
                "redis_password_set": bool(settings.REDIS_PASSWORD)
            }
        
        # Test pubsub
        try:
            pubsub = redis_client.pubsub()
            test_channel = "test_channel"
            await pubsub.subscribe(test_channel)
            
            # Send a test message
            await redis_client.publish(test_channel, "test_message")
            
            # Wait for message
            message = await pubsub.get_message(timeout=1)
            
            await pubsub.unsubscribe(test_channel)
            await pubsub.close()
            
            return {
                "status": "success",
                "redis_url": settings.REDIS_URL,
                "redis_host": settings.REDISHOST,
                "redis_port": settings.REDISPORT,
                "redis_password_set": bool(settings.REDIS_PASSWORD),
                "connection": "OK",
                "pubsub_test": "OK" if message else "FAILED"
            }
        except Exception as pubsub_error:
            return {
                "status": "partial_success",
                "redis_url": settings.REDIS_URL,
                "redis_host": settings.REDISHOST,
                "redis_port": settings.REDISPORT,
                "redis_password_set": bool(settings.REDIS_PASSWORD),
                "connection": "OK",
                "pubsub_test": f"FAILED: {str(pubsub_error)}"
            }
            
    except Exception as e:
        print(f"DEBUG: Redis test failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "redis_url": getattr(settings, 'REDIS_URL', 'NOT SET'),
            "redis_host": getattr(settings, 'REDISHOST', 'NOT SET'),
            "redis_port": getattr(settings, 'REDISPORT', 'NOT SET'),
            "redis_password_set": bool(getattr(settings, 'REDIS_PASSWORD', None))
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


@app.get("/debug/railway-video")
async def debug_railway_video():
    """Debug endpoint to test Railway video processing"""
    try:
        import subprocess
        import tempfile
        import os
        
        # Test 1: Check FFmpeg installation
        ffmpeg_result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        ffmpeg_ok = ffmpeg_result.returncode == 0
        
        # Test 2: Check FFprobe installation
        ffprobe_result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=10)
        ffprobe_ok = ffprobe_result.returncode == 0
        
        # Test 3: Create a simple test video
        test_video_path = None
        test_video_ok = False
        
        try:
            test_video_path = "test_railway_video.mp4"
            cmd = [
                'ffmpeg',
                '-y',
                '-f', 'lavfi',
                '-i', 'testsrc=duration=10:size=640x480:rate=30',
                '-f', 'lavfi',
                '-i', 'sine=frequency=440:duration=10',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'ultrafast',
                '-crf', '30',
                test_video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            test_video_ok = result.returncode == 0 and os.path.exists(test_video_path)
            
        except Exception as e:
            test_video_ok = False
            test_video_error = str(e)
        
        # Test 4: Test Railway video processing
        processing_ok = False
        processing_error = None
        
        if test_video_ok and test_video_path:
            try:
                from video_processor import (
                    split_video_with_precise_timing_and_dynamic_text,
                    get_video_info
                )
                from models import TextStrategy
                
                # Get video info
                video_info = get_video_info(test_video_path)
                
                # Process video with simple parameters
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_prefix = os.path.join(temp_dir, "processed_test")
                    segment_times = [(0, 5), (5, 10)]  # Two 5-second segments
                    
                    output_paths = split_video_with_precise_timing_and_dynamic_text(
                        input_path=test_video_path,
                        output_prefix=output_prefix,
                        segment_times=segment_times,
                        text_strategy=TextStrategy.ONE_FOR_ALL
                    )
                    
                    processing_ok = len(output_paths) == 2
                    
            except Exception as e:
                processing_ok = False
                processing_error = str(e)
        
        # Clean up test video
        if test_video_path and os.path.exists(test_video_path):
            try:
                os.remove(test_video_path)
            except:
                pass
        
        return {
            "status": "success" if all([ffmpeg_ok, ffprobe_ok, test_video_ok, processing_ok]) else "partial_success",
            "tests": {
                "ffmpeg_installation": {
                    "status": "success" if ffmpeg_ok else "error",
                    "details": ffmpeg_result.stdout.split('\n')[0] if ffmpeg_ok else ffmpeg_result.stderr
                },
                "ffprobe_installation": {
                    "status": "success" if ffprobe_ok else "error",
                    "details": ffprobe_result.stdout.split('\n')[0] if ffprobe_ok else ffprobe_result.stderr
                },
                "test_video_creation": {
                    "status": "success" if test_video_ok else "error",
                    "details": "Test video created successfully" if test_video_ok else getattr(locals(), 'test_video_error', 'Unknown error')
                },
                "video_processing": {
                    "status": "success" if processing_ok else "error",
                    "details": "Video processing successful" if processing_ok else processing_error
                }
            },
            "video_info": video_info if test_video_ok else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.get("/debug/test")
async def debug_test():
    """Simple test endpoint to verify backend is running"""
    print("DEBUG: Test endpoint called")
    return {"status": "success", "message": "Backend is running", "timestamp": iso_utc_now()}


@app.get("/debug/test-segment-play")
async def debug_test_segment_play():
    """Debug endpoint to test segment play functionality"""
    try:
        segment_id = "seg_5e910883-ebc9-4d44-91a9-162eff750d46_001"
        
        # Test parsing
        if not segment_id.startswith("seg_"):
            return {"error": "Invalid segment ID format"}
        
        segment_id_without_prefix = segment_id[4:]
        last_underscore_index = segment_id_without_prefix.rfind("_")
        
        if last_underscore_index == -1:
            return {"error": "Invalid segment ID format"}
        
        video_id = segment_id_without_prefix[:last_underscore_index]
        segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
        
        try:
            segment_number = int(segment_number_str)
        except ValueError:
            return {"error": "Invalid segment number format"}
        
        # Test database lookup
        video_resp = table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            return {"error": f"Video not found: {video_id}"}
        
        output_s3_urls = video_item.get("output_s3_urls", [])
        if not output_s3_urls:
            return {"error": f"No output_s3_urls found for video: {video_id}"}
        
        if segment_number < 1 or segment_number > len(output_s3_urls):
            return {"error": f"Invalid segment number: {segment_number}, max: {len(output_s3_urls)}"}
        
        s3_key_or_url = output_s3_urls[segment_number - 1]
        
        # Extract object key from URL if it's a full URL
        if s3_key_or_url.startswith('http'):
            # It's a full URL, extract the object key
            from urllib.parse import urlparse, unquote
            parsed_url = urlparse(s3_key_or_url)
            s3_key = unquote(parsed_url.path.lstrip('/'))
        else:
            # It's already an object key
            s3_key = s3_key_or_url
        
        # Test S3 URL generation
        try:
            presigned_url = generate_presigned_url(
                bucket_name=settings.AWS_BUCKET_NAME,
                object_key=s3_key,
                client_method='get_object',
                expiration=3600
            )
            
            return {
                "status": "success",
                "segment_id": segment_id,
                "video_id": video_id,
                "segment_number": segment_number,
                "s3_key": s3_key,
                "presigned_url": presigned_url[:100] + "..." if len(presigned_url) > 100 else presigned_url,
                "aws_bucket": settings.AWS_BUCKET_NAME,
                "aws_region": settings.AWS_REGION
            }
        except Exception as s3_error:
            return {
                "error": f"S3 URL generation failed: {str(s3_error)}",
                "s3_key": s3_key,
                "aws_bucket": settings.AWS_BUCKET_NAME,
                "aws_region": settings.AWS_REGION
            }
            
    except Exception as e:
        import traceback
        return {
            "error": f"Debug test failed: {str(e)}",
            "traceback": traceback.format_exc()
        }


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "status": "success",
        "environment_variables": {
            "REDISHOST": os.getenv("REDISHOST"),
            "REDISPORT": os.getenv("REDISPORT"),
            "REDIS_PASSWORD": "SET" if os.getenv("REDIS_PASSWORD") else "NOT SET",
            "REDIS_URL": os.getenv("REDIS_URL"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
            "RAILWAY_STATIC_URL": os.getenv("RAILWAY_STATIC_URL")
        },
        "settings": {
            "REDISHOST": settings.REDISHOST,
            "REDISPORT": settings.REDISPORT,
            "REDIS_PASSWORD": "SET" if settings.REDIS_PASSWORD else "NOT SET",
            "REDIS_URL": settings.REDIS_URL,
            "RAILWAY_ENVIRONMENT": settings.RAILWAY_ENVIRONMENT
        }
    }

@router.post("/test/lambda")
async def test_lambda_invoke():
    """Test endpoint to verify Lambda connectivity (Phase 1B)"""
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='RequestResponse',  # Synchronous for testing
            Payload=json.dumps({"test": "data", "source": "railway"})
        )

        # Read the response payload
        response_payload = response['Payload'].read()
        response_data = json.loads(response_payload)

        return {
            "status": "success",
            "lambda_response": response_data,
            "status_code": response['StatusCode'],
            "function_name": f"{settings.PROJECT_NAME}-video-processor-test"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/test/lambda-s3")
async def test_lambda_s3_operations(request: dict):
    """Test endpoint to verify Lambda S3 operations (Phase 2B)"""
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        # Get test parameters from request
        s3_bucket = request.get('s3_bucket', settings.AWS_BUCKET_NAME)
        s3_key = request.get('s3_key', 'uploads/test-file.txt')

        payload = {
            "test_type": "s3_operations",
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "source": "railway"
        }

        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Read the response payload
        response_payload = response['Payload'].read()
        response_data = json.loads(response_payload)

        return {
            "status": "success",
            "lambda_response": response_data,
            "status_code": response['StatusCode'],
            "function_name": f"{settings.PROJECT_NAME}-video-processor-test",
            "test_parameters": payload
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/test/lambda-ffmpeg")
async def test_lambda_ffmpeg_operations():
    """Test endpoint to verify Lambda FFmpeg operations (Phase 3A)"""
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        payload = {
            "test_type": "ffmpeg_test",
            "source": "railway"
        }

        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Read the response payload
        response_payload = response['Payload'].read()
        response_data = json.loads(response_payload)

        return {
            "status": "success",
            "lambda_response": response_data,
            "status_code": response['StatusCode'],
            "function_name": f"{settings.PROJECT_NAME}-video-processor-test",
            "test_parameters": payload
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/test/lambda-video-cutting")
async def test_lambda_video_cutting(request: dict):
    """Test endpoint to verify Lambda video cutting operations (Phase 3B)"""
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        # Get test parameters from request
        s3_bucket = request.get('s3_bucket', 'easy-video-share-silmari-dev')
        s3_key = request.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')

        payload = {
            "test_type": "video_cutting",
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "source": "railway"
        }

        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Read the response payload
        response_payload = response['Payload'].read()
        response_data = json.loads(response_payload)

        return {
            "status": "success",
            "lambda_response": response_data,
            "status_code": response['StatusCode'],
            "function_name": f"{settings.PROJECT_NAME}-video-processor-test",
            "test_parameters": payload
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/test/lambda-dynamodb")
async def test_lambda_dynamodb_operations():
    """Test endpoint to verify Lambda DynamoDB operations (Phase 3C)"""
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        payload = {
            "test_type": "dynamodb_test",
            "source": "railway"
        }

        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Read the response payload
        response_payload = response['Payload'].read()
        response_data = json.loads(response_payload)

        return {
            "status": "success",
            "lambda_response": response_data,
            "status_code": response['StatusCode'],
            "function_name": f"{settings.PROJECT_NAME}-video-processor-test",
            "test_parameters": payload
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/test/lambda-full-integration")
async def test_lambda_full_integration(request: dict):
    """Test endpoint for complete end-to-end Lambda video processing (Phase 4)"""
    try:
        import boto3
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        # Get test parameters from request
        s3_bucket = request.get('s3_bucket', 'easy-video-share-silmari-dev')
        s3_key = request.get('s3_key', 'uploads/f5657863-5078-481c-b4c5-99ffa1dd1ad5/20250706_155512_IMG_0899.mov')
        segment_duration = request.get('segment_duration', 30)  # 30 seconds for social media

        payload = {
            "test_type": "full_integration",
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "segment_duration": segment_duration,
            "source": "railway"
        }

        # Use async invocation for long-running video processing
        response = lambda_client.invoke(
            FunctionName=f"{settings.PROJECT_NAME}-video-processor-test",
            InvocationType='Event',  # Async
            Payload=json.dumps(payload)
        )

        return {
            "status": "processing_started",
            "message": "Lambda processing started asynchronously",
            "status_code": response['StatusCode'],
            "function_name": f"{settings.PROJECT_NAME}-video-processor-test",
            "test_parameters": payload,
            "instructions": "Check DynamoDB for job progress updates"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "error_type": type(e).__name__
        }

# Include router in app (after all endpoints are defined)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
