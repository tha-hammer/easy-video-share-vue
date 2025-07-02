import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key
from config import settings

from typing import List, Optional

# Table name from settings or environment
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "easy-video-share-video-metadata")
dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


def iso_utc_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def create_job_entry(
    job_id: str, 
    user_id: Optional[str] = None, 
    upload_date: Optional[str] = None, 
    status: str = "QUEUED", 
    created_at: Optional[str] = None, 
    updated_at: Optional[str] = None, 
    video_duration: Optional[float] = None,
    # Additional video metadata fields
    filename: Optional[str] = None,
    file_size: Optional[int] = None,
    title: Optional[str] = None,
    user_email: Optional[str] = None,
    content_type: Optional[str] = None,
    bucket_location: Optional[str] = None
):
    """
    Create a new job entry in DynamoDB for job status tracking with complete video metadata.
    """
    now = iso_utc_now()
    item = {
        "video_id": job_id,
        "user_id": user_id or "anonymous",
        "upload_date": upload_date or now,
        "status": status,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
    }
    
    # Add video_duration if provided (convert float to Decimal for DynamoDB)
    if video_duration is not None:
        item["video_duration"] = Decimal(str(video_duration))
    
    # Add additional video metadata fields
    if filename is not None:
        item["filename"] = filename
    if file_size is not None:
        item["file_size"] = file_size
    if title is not None:
        item["title"] = title
    if user_email is not None:
        item["user_email"] = user_email
    if content_type is not None:
        item["content_type"] = content_type
    if bucket_location is not None:
        item["bucket_location"] = bucket_location
    
    table.put_item(Item=item)
    return item


def update_job_status(job_id: str, status: str, output_s3_urls: Optional[List[str]] = None, error_message: Optional[str] = None, updated_at: Optional[str] = None):
    """
    Update job status and optionally output URLs or error message.
    """
    update_expr = ["#s = :s", "updated_at = :u"]
    expr_attr_names = {"#s": "status"}
    expr_attr_values = {":s": status, ":u": updated_at or iso_utc_now()}
    
    if output_s3_urls is not None:
        update_expr.append("output_s3_urls = :o")
        expr_attr_values[":o"] = output_s3_urls
    if error_message is not None:
        update_expr.append("error_message = :e")
        expr_attr_values[":e"] = error_message
    
    update_expression = "SET " + ", ".join(update_expr)
    
    table.update_item(
        Key={"video_id": job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values
    )


def get_job_status(job_id: str) -> Optional[dict]:
    """
    Retrieve job status and metadata from DynamoDB.
    """
    resp = table.get_item(Key={"video_id": job_id})
    return resp.get("Item")


def list_videos(user_id: Optional[str] = None) -> list:
    """
    List all video/job entries for a user (or all users if user_id is None).
    Returns a list of dicts matching VideoMetadata interface expected by frontend.
    """
    if user_id:
        # Query by user_id (assumes GSI on user_id)
        resp = table.query(
            IndexName="user_id-index",  # Make sure this GSI exists
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        items = resp.get("Items", [])
    else:
        # Scan all (for demo/dev; not recommended for prod with large tables)
        resp = table.scan()
        items = resp.get("Items", [])
    
    # Transform items to match VideoMetadata interface expected by frontend
    transformed_items = []
    for item in items:
        # Convert DynamoDB Decimal to float for duration
        duration = None
        if "video_duration" in item:
            duration = float(item["video_duration"])
        elif "duration" in item:
            duration = float(item["duration"]) if isinstance(item["duration"], Decimal) else item["duration"]
        
        # Determine if this is a processed video (has output_s3_urls) or original upload
        has_processed_segments = item.get("output_s3_urls") and len(item.get("output_s3_urls", [])) > 0
        is_processed_video = has_processed_segments and item.get("status") in ["COMPLETED", "PROCESSING"]
        
        # For processed videos, try to extract metadata from the first output URL
        filename = item.get("filename")
        title = item.get("title")
        
        if is_processed_video and (not filename or filename == "unknown.mp4"):
            # Try to extract filename from output_s3_urls
            output_urls = item.get("output_s3_urls", [])
            if output_urls:
                first_url = output_urls[0]
                # Extract job_id from URL path
                if "/processed/" in first_url:
                    job_id = first_url.split("/processed/")[1].split("/")[0]
                    filename = f"processed_{job_id}_segment_001.mp4"
                    title = f"Processed Video - {job_id[:8]}"
        
        # Create transformed item with expected field names
        transformed_item = {
            "video_id": item.get("video_id"),
            "user_id": item.get("user_id"),
            "user_email": item.get("user_email", "unknown@example.com"),  # Default fallback
            "title": title or item.get("filename", "Untitled Video"),  # Use filename as fallback title
            "filename": filename or "unknown.mp4",  # Default fallback
            "bucket_location": item.get("bucket_location", ""),
            "upload_date": item.get("upload_date"),
            "file_size": item.get("file_size", 0),  # Default to 0 if not present
            "content_type": item.get("content_type", "video/mp4"),  # Default fallback
            "duration": duration,  # Converted from video_duration
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "status": item.get("status", "UNKNOWN"),  # Job status
            "output_s3_urls": item.get("output_s3_urls", []),  # Processed video segments
            "error_message": item.get("error_message")  # Error if job failed
        }
        
        transformed_items.append(transformed_item)
    
    return transformed_items
