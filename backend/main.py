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
    ProgressUpdate
)
from s3_utils import generate_presigned_url, generate_s3_key
import dynamodb_service
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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vue dev server
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
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Generate S3 key for the upload
        s3_key = generate_s3_key(request.filename, job_id)

        # Generate presigned URL for S3 upload
        presigned_url = generate_presigned_url(
            bucket_name=settings.AWS_BUCKET_NAME,
            object_key=s3_key,
            client_method='put_object',  # Use 'put_object' for uploads
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

        # Immediately create DynamoDB job entry (QUEUED)
        try:
            from datetime import datetime, timezone
            now_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            dynamodb_service.create_job_entry(
                job_id=request.job_id,
                user_id="anonymous",
                upload_date=now_iso,
                status="QUEUED",
                created_at=now_iso,
                updated_at=now_iso
            )
        except Exception as e:
            print(f"[DynamoDB] Failed to create job entry in /upload/complete for job_id={request.job_id}: {e}")

        return JobCreatedResponse(
            job_id=request.job_id,
            status="QUEUED",
            message="Video processing job has been queued successfully"
        )

    except Exception as e:
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

        # --- DEBUGGING PRINTS START ---
        print(f"DEBUG: Job {job_id} found. Status: '{status}', raw output_urls: {output_urls}")
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
                for s3_url in output_urls: # This is a likely failure point if output_urls isn't iterable
                    # --- DEBUGGING PRINTS START ---
                    print(f"DEBUG: Processing S3 URL for presigning: {s3_url}")
                    # --- DEBUGGING PRINTS END ---

                    # Parse bucket and key from S3 URL
                    if s3_url.startswith("s3://"):
                        _, bucket, *key_parts = s3_url.split("/")
                        key = "/".join(key_parts)
                    else:
                        # Assume https://bucket.s3.amazonaws.com/key format
                        parts = s3_url.split("/")
                        # This line is brittle if the URL format isn't exactly as assumed
                        bucket = parts[2].split(".")[0]
                        key = "/".join(parts[3:])

                    # --- DEBUGGING PRINTS START ---
                    print(f"DEBUG: Parsed Bucket: '{bucket}', Key: '{key}' for URL: {s3_url}")
                    # --- DEBUGGING PRINTS END ---

                    # This is another likely failure point if permissions are wrong or key/bucket are bad
                    presigned = generate_presigned_url(
                        bucket_name=bucket,
                        object_key=key,
                        client_method='get_object',
                        content_type=None, # For GET operations, content_type is often not needed
                        expiration=3600  # 1 hour
                    )
                    presigned_urls.append(presigned)
                    # --- DEBUGGING PRINTS START ---
                    print(f"DEBUG: Generated presigned URL for {s3_url}: {presigned[:60]}...") # Print truncated URL
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
            updated_at=updated_at
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
    async def event_generator():
        redis_conn = await get_async_redis_client_from_pool()
        pubsub = redis_conn.pubsub()
        channel = f"job_progress_{job_id}"
        await pubsub.subscribe(channel)
        print(f"DEBUG: SSE subscribed to {channel}")
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
    return EventSourceResponse(event_generator())

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
