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
def process_video_task(self, s3_input_key: str, job_id: str):
    """
    Celery task for processing video (placeholder for Sprint 1)
    
    Args:
        s3_input_key: S3 key of the uploaded video
        job_id: Unique job identifier
    """
    # Placeholder implementation for Sprint 1
    # Will be expanded in Sprint 2 with actual video processing
    try:
        # Update job status to processing
        # TODO: Implement actual video processing logic in Sprint 2
        print(f"Processing video task started for job: {job_id}")
        print(f"Input S3 key: {s3_input_key}")
        
        # Simulate processing time for now
        import time
        time.sleep(5)
        
        print(f"Video processing completed for job: {job_id}")
        return {"status": "completed", "job_id": job_id}
        
    except Exception as exc:
        print(f"Video processing failed for job {job_id}: {str(exc)}")
        # Update job status to failed
        raise self.retry(exc=exc, countdown=60, max_retries=3)
