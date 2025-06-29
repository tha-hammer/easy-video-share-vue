from celery import Celery
from config import settings

# Initialize Celery app
celery_app = Celery(
    "video_processor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks"]  # Changed from "backend.tasks" to "tasks"
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


@celery_app.task(bind=True)
def process_video_task(self, s3_input_key: str, job_id: str, cutting_options: dict = None, text_strategy: str = None, text_input: dict = None):
    """
    Celery task for processing video - Sprint 4 implementation
    
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
    from s3_utils import download_file_from_s3, upload_file_to_s3
    from video_processing_utils import calculate_segments, validate_video_file, get_video_duration_from_s3
    from video_processing_utils_sprint4 import split_video_with_precise_timing_and_dynamic_text
    from models import CuttingOptions, FixedCuttingParams, RandomCuttingParams, TextStrategy, TextInput
    from config import settings
    
    temp_dir = None
    local_input_path = None
    output_paths = []
    
    try:
        print(f"Processing video task started for job: {job_id}")
        print(f"Input S3 key: {s3_input_key}")
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix=f"video_proc_{job_id}_")
        print(f"Created temp directory: {temp_dir}")
        
        # Download video from S3
        input_filename = os.path.basename(s3_input_key)
        local_input_path = os.path.join(temp_dir, f"input_{input_filename}")
        
        print(f"Downloading video from S3: {s3_input_key}")
        download_file_from_s3(
            bucket=settings.AWS_BUCKET_NAME,
            key=s3_input_key,
            local_path=local_input_path
        )
        print(f"Downloaded to: {local_input_path}")
        
        # Validate the downloaded video
        if not validate_video_file(local_input_path):
            raise Exception("Downloaded file is not a valid video")
        
        # Parse cutting options or use defaults
        if cutting_options:
            # Convert dict back to Pydantic model
            if cutting_options.get("type") == "fixed":
                cutting_params = FixedCuttingParams(**cutting_options)
            elif cutting_options.get("type") == "random":
                cutting_params = RandomCuttingParams(**cutting_options)
            else:
                # Default to 30-second fixed segments for backward compatibility
                cutting_params = FixedCuttingParams(duration_seconds=30)
        else:
            # Default to 30-second fixed segments for backward compatibility
            cutting_params = FixedCuttingParams(duration_seconds=30)
        
        # Parse text strategy or use default
        text_strategy_enum = TextStrategy(text_strategy) if text_strategy else TextStrategy.ONE_FOR_ALL
        
        # Parse text input if provided
        text_input_obj = None
        if text_input:
            text_input_obj = TextInput(**text_input)
        
        print(f"Processing with cutting options: {cutting_params}")
        print(f"Text strategy: {text_strategy_enum}")
        print(f"Text input: {text_input_obj}")
        
        # Get video duration and calculate segments
        total_duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, s3_input_key)
        num_segments, segment_times = calculate_segments(total_duration, cutting_params)
        
        print(f"Video duration: {total_duration:.2f}s, will create {num_segments} segments")
        for i, (start, end) in enumerate(segment_times):
            print(f"Segment {i+1}: {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")
        
        # Process video with precise timing and dynamic text overlay
        output_prefix = os.path.join(temp_dir, f"processed_{job_id}")
        print(f"Starting Sprint 4 video processing with output prefix: {output_prefix}")
        
        # Use new Sprint 4 processing function with precise timing and dynamic text
        output_paths = split_video_with_precise_timing_and_dynamic_text(
            input_path=local_input_path,
            output_prefix=output_prefix,
            segment_times=segment_times,
            text_strategy=text_strategy_enum,
            text_input=text_input_obj
        )
        print(f"Video processing completed. Generated {len(output_paths)} segments")
        
        # Upload processed segments back to S3
        uploaded_urls = []
        for i, output_path in enumerate(output_paths):
            if os.path.exists(output_path):
                # Generate S3 key for processed segment
                segment_filename = os.path.basename(output_path)
                s3_output_key = f"processed/{job_id}/{segment_filename}"
                
                print(f"Uploading segment {i+1}/{len(output_paths)}: {segment_filename}")
                s3_url = upload_file_to_s3(
                    local_path=output_path,
                    bucket=settings.AWS_BUCKET_NAME,
                    key=s3_output_key
                )
                uploaded_urls.append(s3_url)
                print(f"Uploaded to: {s3_url}")
            else:
                print(f"Warning: Output file does not exist: {output_path}")
        
        print(f"Video processing completed for job: {job_id}")
        print(f"Generated {len(uploaded_urls)} processed video segments")
        
        return {
            "status": "completed",
            "job_id": job_id,
            "output_urls": uploaded_urls,
            "segments_created": len(uploaded_urls)
        }
        
    except Exception as exc:
        print(f"Video processing failed for job {job_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)
        
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            print(f"Cleaning up temporary directory: {temp_dir}")
            try:
                import shutil
                shutil.rmtree(temp_dir)
                print("Cleanup completed successfully")
            except Exception as cleanup_error:
                print(f"Warning: Failed to clean up temp directory: {cleanup_error}")
