from celery import Celery
from config import settings
import redis
import json
from datetime import datetime, timezone
from models import ProgressUpdate, VideoSegment, SegmentType, SocialMediaUsage, SocialMediaPlatform

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
    from video_processing_utils_railway import split_video_with_precise_timing_and_dynamic_text
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

    # Note: Job entry is already created in complete_upload endpoint with complete metadata
    # No need to create duplicate entry here

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
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="processing_segment",
            message=f"Processing {num_segments} segments...",
            current_segment=1,
            total_segments=num_segments,
            progress_percentage=10.0,
            timestamp=now_iso()
        ))
        
        # Process all segments at once
        output_prefix = os.path.join(temp_dir, f"processed_{job_id}")
        
        # Define progress callback function
        def progress_callback(current_segment, total_segments, message):
            progress_percentage = (current_segment / total_segments) * 80 + 10  # 10-90%
            publish_progress(job_id, ProgressUpdate(
                job_id=job_id,
                stage="processing_segment",
                message=message,
                current_segment=current_segment,
                total_segments=total_segments,
                progress_percentage=progress_percentage,
                timestamp=now_iso()
            ))
        
        all_output_paths = split_video_with_precise_timing_and_dynamic_text(
            input_path=local_input_path,
            output_prefix=output_prefix,
            segment_times=segment_times,  # Process all segments at once
            text_strategy=text_strategy_enum,
            text_input=text_input_obj,
            progress_callback=progress_callback
        )
        
        # Upload each segment to S3
        uploaded_s3_keys = []
        for i, output_path in enumerate(all_output_paths):
            if output_path and os.path.exists(output_path):
                segment_filename = os.path.basename(output_path)
                s3_output_key = f"processed/{job_id}/{segment_filename}"
                
                # Upload file to S3 (don't use the returned URL)
                upload_file_to_s3(
                    local_path=output_path,
                    bucket=settings.AWS_BUCKET_NAME,
                    key=s3_output_key
                )
                
                # Store the S3 key instead of direct URL
                uploaded_s3_keys.append(s3_output_key)
                
                publish_progress(job_id, ProgressUpdate(
                    job_id=job_id,
                    stage="segment_uploaded",
                    message=f"Segment {i+1} uploaded to S3.",
                    current_segment=i+1,
                    total_segments=num_segments,
                    progress_percentage=((i+1)/num_segments)*80+10,  # 10-90%
                    timestamp=now_iso(),
                    output_urls=uploaded_s3_keys.copy()  # Store S3 keys instead of URLs
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
                output_s3_urls=uploaded_s3_keys
            )
        except Exception as e:
            print(f"[DynamOdb] Failed to update job status to COMPLETED for job_id={job_id}: {e}")

        # Create segment records in DynamoDB
        try:
            # Get video metadata for segment creation
            video_metadata = dynamodb_service.get_job_status(job_id)
            if video_metadata:
                # Queue segment creation task
                create_segments_from_video_task.delay(
                    video_id=job_id,
                    user_id=user_id,
                    output_s3_keys=uploaded_s3_keys,
                    video_metadata={
                        "title": video_metadata.get("title", "Untitled Video"),
                        "tags": video_metadata.get("tags", [])
                    }
                )
                print(f"[SEGMENT CREATION] Queued segment creation task for video {job_id}")
        except Exception as e:
            print(f"[SEGMENT CREATION] Failed to queue segment creation task for job_id={job_id}: {e}")

        # 7. Completed
        publish_progress(job_id, ProgressUpdate(
            job_id=job_id,
            stage="completed",
            message="Video processing completed successfully!",
            progress_percentage=100.0,
            timestamp=now_iso(),
            output_urls=uploaded_s3_keys.copy()
        ))
        return {
            "status": "completed",
            "job_id": job_id,
            "output_urls": uploaded_s3_keys,
            "segments_created": len(uploaded_s3_keys)
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


@celery_app.task(bind=True)
def create_segments_from_video_task(self, video_id: str, user_id: str, output_s3_keys: list, video_metadata: dict):
    """
    Celery task for creating segment records in DynamoDB after video processing.
    
    This task is called after video processing is complete to create individual
    segment records for each processed video segment.
    """
    import os
    from s3_utils import get_file_size_from_s3, get_video_duration_from_s3
    import dynamodb_service
    from datetime import datetime, timezone
    
    try:
        print(f"[SEGMENT CREATION] Starting segment creation for video {video_id}")
        
        created_segments = []
        
        for i, s3_key in enumerate(output_s3_keys, 1):
            try:
                # Get file size from S3
                file_size = get_file_size_from_s3(settings.AWS_BUCKET_NAME, s3_key)
                
                # Get video duration from S3
                duration = get_video_duration_from_s3(settings.AWS_BUCKET_NAME, s3_key)
                
                # Generate segment ID
                segment_id = f"seg_{video_id}_{i:03d}"
                
                # Create segment data
                current_time = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
                segment_data = VideoSegment(
                    segment_id=segment_id,
                    video_id=video_id,
                    user_id=user_id,
                    segment_type=SegmentType.PROCESSED,
                    segment_number=i,
                    s3_key=s3_key,
                    duration=duration,
                    file_size=file_size,
                    content_type="video/mp4",
                    title=f"{video_metadata.get('title', 'Video')} - Part {i}",
                    description=f"Processed segment {i} of {len(output_s3_keys)}",
                    tags=video_metadata.get('tags', []),
                    created_at=current_time,
                    updated_at=current_time
                )
                
                # Save to DynamoDB
                created_segment = dynamodb_service.create_segment(segment_data)
                created_segments.append(created_segment)
                
                print(f"[SEGMENT CREATION] Created segment {segment_id}")
                
            except Exception as e:
                print(f"[SEGMENT CREATION] Failed to create segment {i}: {e}")
                continue
        
        print(f"[SEGMENT CREATION] Successfully created {len(created_segments)} segments for video {video_id}")
        return {
            "status": "completed",
            "video_id": video_id,
            "segments_created": len(created_segments),
            "segment_ids": [seg.segment_id for seg in created_segments]
        }
        
    except Exception as exc:
        print(f"[SEGMENT CREATION] Failed to create segments for video {video_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def sync_social_media_metrics_task(self, segment_id: str, platform: str):
    """
    Celery task for syncing social media metrics for a segment.
    
    This task will be expanded in the future to integrate with actual
    social media APIs (Instagram, TikTok, etc.) to fetch real metrics.
    """
    import dynamodb_service
    from datetime import datetime, timezone
    
    try:
        print(f"[SOCIAL MEDIA SYNC] Starting sync for segment {segment_id} on {platform}")
        
        # Get current segment
        segment = dynamodb_service.get_segment(segment_id)
        if not segment:
            raise Exception(f"Segment {segment_id} not found")
        
        # For now, simulate API call with mock data
        # TODO: Replace with actual social media API integration
        mock_metrics = {
            "instagram": {
                "views": 1500,
                "likes": 120,
                "shares": 25,
                "comments": 15,
                "engagement_rate": 8.5
            },
            "tiktok": {
                "views": 2500,
                "likes": 200,
                "shares": 40,
                "comments": 30,
                "engagement_rate": 10.8
            },
            "youtube": {
                "views": 800,
                "likes": 45,
                "shares": 12,
                "comments": 8,
                "engagement_rate": 8.1
            }
        }
        
        # Get mock data for the platform
        platform_metrics = mock_metrics.get(platform.lower(), {
            "views": 100,
            "likes": 10,
            "shares": 2,
            "comments": 1,
            "engagement_rate": 5.0
        })
        
        # Create social media usage data
        social_media_usage = SocialMediaUsage(
            platform=SocialMediaPlatform(platform),
            post_id=f"mock_post_{segment_id}_{platform}",
            post_url=f"https://{platform}.com/posts/mock_post_{segment_id}",
            posted_at=datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            views=platform_metrics["views"],
            likes=platform_metrics["likes"],
            shares=platform_metrics["shares"],
            comments=platform_metrics["comments"],
            engagement_rate=platform_metrics["engagement_rate"],
            last_synced=datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        )
        
        # Update segment with social media usage
        updated_segment = dynamodb_service.add_social_media_usage(segment_id, social_media_usage)
        
        print(f"[SOCIAL MEDIA SYNC] Successfully synced metrics for segment {segment_id} on {platform}")
        
        return {
            "status": "completed",
            "segment_id": segment_id,
            "platform": platform,
            "metrics": platform_metrics
        }
        
    except Exception as exc:
        print(f"[SOCIAL MEDIA SYNC] Failed to sync metrics for segment {segment_id} on {platform}: {str(exc)}")
        raise self.retry(exc=exc, countdown=300, max_retries=2)  # Retry every 5 minutes, max 2 retries


@celery_app.task(bind=True)
def batch_sync_social_media_task(self, user_id: str, platforms: list = None):
    """
    Celery task for batch syncing social media metrics for all user segments.
    
    This task will sync metrics for all segments of a user across specified platforms.
    """
    import dynamodb_service
    
    if not platforms:
        platforms = ["instagram", "tiktok", "youtube"]
    
    try:
        print(f"[BATCH SOCIAL MEDIA SYNC] Starting batch sync for user {user_id}")
        
        # Get all user segments
        segments = dynamodb_service.list_segments_by_user(user_id)
        
        if not segments:
            print(f"[BATCH SOCIAL MEDIA SYNC] No segments found for user {user_id}")
            return {
                "status": "completed",
                "user_id": user_id,
                "segments_synced": 0,
                "message": "No segments found"
            }
        
        # Sync each segment for each platform
        sync_tasks = []
        for segment in segments:
            for platform in platforms:
                # Queue individual sync task
                task = sync_social_media_metrics_task.delay(segment.segment_id, platform)
                sync_tasks.append(task)
        
        print(f"[BATCH SOCIAL MEDIA SYNC] Queued {len(sync_tasks)} sync tasks for user {user_id}")
        
        return {
            "status": "queued",
            "user_id": user_id,
            "segments_count": len(segments),
            "platforms": platforms,
            "tasks_queued": len(sync_tasks)
        }
        
    except Exception as exc:
        print(f"[BATCH SOCIAL MEDIA SYNC] Failed to batch sync for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=600, max_retries=2)  # Retry every 10 minutes, max 2 retries
