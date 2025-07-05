import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key
from config import settings

from typing import List, Optional, Dict, Any
from models import VideoSegment, SegmentType, SocialMediaUsage, SocialMediaPlatform

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


# === SEGMENT MANAGEMENT FUNCTIONS ===

def create_segment(segment_data: VideoSegment) -> VideoSegment:
    """
    Create a new video segment in DynamoDB.
    """
    now = iso_utc_now()
    
    # Convert VideoSegment to DynamoDB item format
    item = {
        "segment_id": segment_data.segment_id,
        "video_id": segment_data.video_id,
        "user_id": segment_data.user_id,
        "segment_type": segment_data.segment_type.value,
        "segment_number": segment_data.segment_number,
        "s3_key": segment_data.s3_key,
        "duration": segment_data.duration,
        "file_size": segment_data.file_size,
        "content_type": segment_data.content_type,
        "created_at": segment_data.created_at or now,
        "updated_at": segment_data.updated_at or now,
    }
    
    # Add optional fields
    if segment_data.title:
        item["title"] = segment_data.title
    if segment_data.description:
        item["description"] = segment_data.description
    if segment_data.tags:
        item["tags"] = segment_data.tags
    if segment_data.thumbnail_url:
        item["thumbnail_url"] = segment_data.thumbnail_url
    if segment_data.social_media_usage:
        item["social_media_usage"] = [
            {
                "platform": usage.platform.value,
                "post_id": usage.post_id,
                "post_url": usage.post_url,
                "posted_at": usage.posted_at,
                "views": usage.views,
                "likes": usage.likes,
                "shares": usage.shares,
                "comments": usage.comments,
                "engagement_rate": usage.engagement_rate,
                "last_synced": usage.last_synced
            }
            for usage in segment_data.social_media_usage
        ]
    
    table.put_item(Item=item)
    return segment_data


def get_segment(segment_id: str) -> Optional[VideoSegment]:
    """
    Retrieve a video segment by segment_id.
    """
    resp = table.get_item(Key={"segment_id": segment_id})
    item = resp.get("Item")
    
    if not item:
        return None
    
    return _item_to_video_segment(item)


def list_segments_by_video(video_id: str, segment_type: Optional[SegmentType] = None) -> List[VideoSegment]:
    """
    List all segments for a specific video, optionally filtered by type.
    """
    if segment_type:
        # Query by video_id and segment_type
        resp = table.query(
            IndexName="video_id-segment_type-index",
            KeyConditionExpression=Key("video_id").eq(video_id) & Key("segment_type").eq(segment_type.value)
        )
    else:
        # Query by video_id only
        resp = table.query(
            IndexName="video_id-segment_type-index",
            KeyConditionExpression=Key("video_id").eq(video_id)
        )
    
    items = resp.get("Items", [])
    return [_item_to_video_segment(item) for item in items]


def list_segments_by_user(user_id: str, filters: Optional[Dict[str, Any]] = None) -> List[VideoSegment]:
    """
    List all segments for a user with optional filtering.
    """
    # Build query parameters
    query_params = {
        "IndexName": "user_id-segment_type-index",
        "KeyConditionExpression": Key("user_id").eq(user_id)
    }
    
    # Add segment type filter if provided
    if filters and filters.get("segment_type"):
        query_params["KeyConditionExpression"] = Key("user_id").eq(user_id) & Key("segment_type").eq(filters["segment_type"].value)
    
    resp = table.query(**query_params)
    items = resp.get("Items", [])
    
    # Apply additional filters
    segments = [_item_to_video_segment(item) for item in items]
    
    # Filter by duration
    if filters and filters.get("min_duration"):
        segments = [s for s in segments if s.duration >= filters["min_duration"]]
    if filters and filters.get("max_duration"):
        segments = [s for s in segments if s.duration <= filters["max_duration"]]
    
    # Filter by tags
    if filters and filters.get("tags"):
        required_tags = set(filters["tags"])
        segments = [s for s in segments if s.tags and required_tags.issubset(set(s.tags))]
    
    # Filter by social media usage
    if filters and filters.get("has_social_media"):
        if filters["has_social_media"]:
            segments = [s for s in segments if s.social_media_usage and len(s.social_media_usage) > 0]
        else:
            segments = [s for s in segments if not s.social_media_usage or len(s.social_media_usage) == 0]
    
    # Filter by platform
    if filters and filters.get("platform"):
        platform = filters["platform"].value
        segments = [s for s in segments if s.social_media_usage and any(u.platform.value == platform for u in s.social_media_usage)]
    
    return segments


def update_segment(segment_id: str, update_data: Dict[str, Any]) -> Optional[VideoSegment]:
    """
    Update a video segment.
    """
    update_expr = ["updated_at = :u"]
    expr_attr_values = {":u": iso_utc_now()}
    expr_attr_names = {}
    
    # Build update expression dynamically
    for key, value in update_data.items():
        if key in ["title", "description", "tags", "thumbnail_url"]:
            attr_name = f"#{key}"
            attr_value = f":{key}"
            update_expr.append(f"{attr_name} = {attr_value}")
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = value
    
    update_expression = "SET " + ", ".join(update_expr)
    
    try:
        resp = table.update_item(
            Key={"segment_id": segment_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        
        updated_item = resp.get("Attributes")
        return _item_to_video_segment(updated_item) if updated_item else None
    except Exception as e:
        print(f"Error updating segment {segment_id}: {e}")
        return None


def delete_segment(segment_id: str) -> bool:
    """
    Delete a video segment.
    """
    try:
        table.delete_item(Key={"segment_id": segment_id})
        return True
    except Exception as e:
        print(f"Error deleting segment {segment_id}: {e}")
        return False


def add_social_media_usage(segment_id: str, social_media_usage: SocialMediaUsage) -> Optional[VideoSegment]:
    """
    Add or update social media usage for a segment.
    """
    # Get current segment
    segment = get_segment(segment_id)
    if not segment:
        return None
    
    # Update or add social media usage
    current_usage = segment.social_media_usage or []
    
    # Check if platform already exists
    platform_exists = False
    for i, usage in enumerate(current_usage):
        if usage.platform == social_media_usage.platform:
            current_usage[i] = social_media_usage
            platform_exists = True
            break
    
    if not platform_exists:
        current_usage.append(social_media_usage)
    
    # Update segment
    return update_segment(segment_id, {"social_media_usage": current_usage})


def get_social_media_analytics(segment_id: str) -> Optional[Dict[str, Any]]:
    """
    Get social media analytics for a segment.
    """
    segment = get_segment(segment_id)
    if not segment or not segment.social_media_usage:
        return None
    
    total_views = sum(usage.views for usage in segment.social_media_usage)
    total_likes = sum(usage.likes for usage in segment.social_media_usage)
    total_shares = sum(usage.shares for usage in segment.social_media_usage)
    total_comments = sum(usage.comments for usage in segment.social_media_usage)
    total_engagement = total_likes + total_shares + total_comments
    
    # Calculate average engagement rate
    engagement_rates = [usage.engagement_rate for usage in segment.social_media_usage if usage.engagement_rate]
    average_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
    
    # Find top performing platform
    top_platform = None
    max_engagement = 0
    for usage in segment.social_media_usage:
        engagement = usage.likes + usage.shares + usage.comments
        if engagement > max_engagement:
            max_engagement = engagement
            top_platform = usage.platform
    
    return {
        "segment_id": segment_id,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_shares": total_shares,
        "total_comments": total_comments,
        "total_engagement": total_engagement,
        "average_engagement_rate": average_engagement_rate,
        "platform_breakdown": segment.social_media_usage,
        "top_performing_platform": top_platform,
        "last_updated": segment.updated_at
    }


def _item_to_video_segment(item: Dict[str, Any]) -> VideoSegment:
    """
    Convert DynamoDB item to VideoSegment model.
    """
    # Convert social media usage
    social_media_usage = []
    if "social_media_usage" in item:
        for usage_data in item["social_media_usage"]:
            social_media_usage.append(SocialMediaUsage(
                platform=SocialMediaPlatform(usage_data["platform"]),
                post_id=usage_data.get("post_id"),
                post_url=usage_data.get("post_url"),
                posted_at=usage_data.get("posted_at"),
                views=usage_data.get("views", 0),
                likes=usage_data.get("likes", 0),
                shares=usage_data.get("shares", 0),
                comments=usage_data.get("comments", 0),
                engagement_rate=usage_data.get("engagement_rate"),
                last_synced=usage_data.get("last_synced")
            ))
    
    return VideoSegment(
        segment_id=item["segment_id"],
        video_id=item["video_id"],
        user_id=item["user_id"],
        segment_type=SegmentType(item["segment_type"]),
        segment_number=item["segment_number"],
        s3_key=item["s3_key"],
        duration=float(item["duration"]) if isinstance(item["duration"], Decimal) else item["duration"],
        file_size=item["file_size"],
        content_type=item.get("content_type", "video/mp4"),
        thumbnail_url=item.get("thumbnail_url"),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
        title=item.get("title"),
        description=item.get("description"),
        tags=item.get("tags", []),
        social_media_usage=social_media_usage
    )
