from celery import Celery
from config import settings
import redis
import json
from datetime import datetime, timezone
from models import ProgressUpdate

# Initialize Celery app
celery_app = Celery(
    "video_processor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

def publish_progress(job_id: str, progress: ProgressUpdate):
    """
    Publishes a ProgressUpdate to the Redis channel for SSE.
    Uses synchronous Redis client.
    """
    r = redis.StrictRedis.from_url(settings.REDIS_URL, decode_responses=True)
    channel = f"job_progress_{job_id}"
    r.publish(channel, progress.model_dump_json())

@celery_app.task(bind=True)
def process_video_task(self, s3_input_key: str, job_id: str, cutting_options: dict = None, text_strategy: str = None, text_input: dict = None, user_id: str = "anonymous_fallback"):
    """
    Celery task for processing video - Sprint 5: DynamoDB job status tracking
    
    Downloads video from S3, splits into segments based on cutting options,
    adds text overlay based on text strategy with LLM integration, 
    and uploads processed segments back to S3.
    
    Args:
        s3_input_key: S3 key of the uploaded video
        job_id: Unique job identifier
        cutting_options: Dictionary representing cutting parameters (fixed or random)
        text_strategy: Text overlay strategy ("one_for_all", "base_vary", "unique_for_all")
        text_input: Dictionary containing text input data for the strategy
    """
    import tempfile
    import os
    import uuid
    from s3_utils import download_file_from_s3, upload_file_to_s3
    from video_processing_utils import calculate_segments, validate_video_file, get_video_duration_from_s3
    from video_processing_utils_sprint4 import split_video_with_precise_timing_and_dynamic_text
    from models import CuttingOptions, FixedCuttingParams, RandomCuttingParams, TextStrategy, TextInput
    import dynamodb_service

    temp_dir = None
    local_input_path = None
    output_paths = []
    uploaded_urls = []
    now_iso = lambda: datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    # 1. Job received
    publish_progress(job_id, ProgressUpdate(
        job_id=job_id,
        stage="queued",
        message="Job received, initializing...",
        progress_percentage=0.0,
        timestamp=now_iso()
    ))

    # Create DynamoDB job entry (QUEUED)
    try:
        
        dynamodb_service.create_job_entry(
            job_id=job_id,
            user_id=user_id,
            upload_date=now_iso(),
            status="QUEUED",
            created_at=now_iso(),
            updated_at=now_iso()
        )
    except Exception as e:
        print(f"[DynamoDB] Failed to create job entry for job_id={job_id}: {e}")

    try:
        # Mark job as PROCESSING
        try:
            dynamodb_service.update_job_status(job_id, status="PROCESSING")
        except Exception as e:
            print(f"[DynamoDB] Failed to update job status to PROCESSING for job_id={job_id}: {e}")

        # 2. Downloading video
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="downloading_video",
            message="Downloading video from S3...",
            progress_percentage=2.0,
            timestamp=now_iso()
        ))

        temp_dir = tempfile.mkdtemp(prefix=f"video_proc_{job_id}_")
        input_filename = os.path.basename(s3_input_key)
        local_input_path = os.path.join(temp_dir, f"input_{input_filename}")
        download_file_from_s3(
            bucket=settings.AWS_BUCKET_NAME,
            key=s3_input_key,
            local_path=local_input_path
        )

        # 3. Analyzing duration
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="analyzing_duration",
            message="Analyzing video duration...",
            progress_percentage=5.0,
            timestamp=now_iso()
        ))

        if not validate_video_file(local_input_path):
            raise Exception("Downloaded file is not a valid video")

        # Parse cutting options
        if cutting_options:
            if cutting_options.get("type") == "fixed":
                cutting_params = FixedCuttingParams(**cutting_options)
            elif cutting_options.get("type") == "random":
                cutting_params = RandomCuttingParams(**cutting_options)
            else:
                cutting_params = FixedCuttingParams(duration_seconds=30)
        else:
            cutting_params = FixedCuttingParams(duration_seconds=30)

        text_strategy_enum = TextStrategy(text_strategy) if text_strategy else TextStrategy.ONE_FOR_ALL
        text_input_obj = TextInput(**text_input) if text_input else None

        total_duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, s3_input_key)
        num_segments, segment_times = calculate_segments(total_duration, cutting_params)

        # 4. Generating text (if needed)
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="generating_text",
            message="AI generating text variations...",
            progress_percentage=10.0,
            timestamp=now_iso()
        ))

        # 5. Processing segments
        for i, (start, end) in enumerate(segment_times):
            publish_progress(job_id, ProgressUpdate(
                job_id=job_id,
                stage="processing_segment",
                message=f"Processing segment {i+1}/{num_segments}...",
                current_segment=i+1,
                total_segments=num_segments,
                progress_percentage=((i+1)/num_segments)*80+10,  # 10-90%
                timestamp=now_iso()
            ))
            # Process segment
            output_prefix = os.path.join(temp_dir, f"processed_{job_id}")
            segment_output_paths = split_video_with_precise_timing_and_dynamic_text(
                input_path=local_input_path,
                output_prefix=output_prefix,
                segment_times=[(start, end)],
                text_strategy=text_strategy_enum,
                text_input=text_input_obj
            )
            output_path = segment_output_paths[0] if segment_output_paths else None
            if output_path and os.path.exists(output_path):
                segment_filename = os.path.basename(output_path)
                s3_output_key = f"processed/{job_id}/{segment_filename}"
                s3_url = upload_file_to_s3(
                    local_path=output_path,
                    bucket=settings.AWS_BUCKET_NAME,
                    key=s3_output_key
                )
                uploaded_urls.append(s3_url)
                publish_progress(job_id, ProgressUpdate(
                    job_id=job_id,
                    stage="segment_uploaded",
                    message=f"Segment {i+1} uploaded to S3.",
                    current_segment=i+1,
                    total_segments=num_segments,
                    progress_percentage=((i+1)/num_segments)*90,
                    timestamp=now_iso(),
                    output_urls=uploaded_urls.copy()
                ))
            else:
                print(f"Warning: Output file does not exist: {output_path}")

        # 6. Uploading results
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="uploading_results",
            message="Finalizing upload to S3...",
            progress_percentage=95.0,
            timestamp=now_iso(),
            output_urls=uploaded_urls.copy()
        ))

        # Mark job as COMPLETED in DynamoDB
        try:
            dynamodb_service.update_job_status(
                job_id,
                status="COMPLETED",
                output_s3_urls=uploaded_urls
            )
        except Exception as e:
            print(f"[DynamoDB] Failed to update job status to COMPLETED for job_id={job_id}: {e}")

        # 7. Completed
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="completed",
            message="Video processing completed successfully!",
            progress_percentage=100.0,
            timestamp=now_iso(),
            output_urls=uploaded_urls.copy()
        ))
        return {
            "status": "completed",
            "job_id": job_id,
            "output_urls": uploaded_urls,
            "segments_created": len(uploaded_urls)
        }
    except Exception as exc:
        print(f"Video processing failed for job {job_id}: {str(exc)}")
        # Mark job as FAILED in DynamoDB
        try:
            dynamodb_service.update_job_status(
                job_id,
                status="FAILED",
                error_message=str(exc)
            )
        except Exception as e:
            print(f"[DynamoDB] Failed to update job status to FAILED for job_id={job_id}: {e}")
        # 8. Failed
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="failed",
            message=f"Processing failed: {str(exc)}",
            progress_percentage=0.0,
            timestamp=now_iso(),
            error_message=str(exc)
        ))
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up temp directory: {cleanup_error}")
