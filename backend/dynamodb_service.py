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
        # Query by user_id using the correct GSI
        resp = table.query(
            IndexName="user_id-created_at-index",  # Use the existing GSI
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

def get_segment(segment_id: str) -> Optional[VideoSegment]:
    """
    Get a specific video segment by ID.
    This function gets segments from the video-metadata table (output_s3_urls)
    and can also check the video-segments table for additional text overlay data.
    """
    print(f"[DEBUG] Getting segment: {segment_id}")
    
    # Parse segment_id to extract video_id and segment number
    # Format: seg_{video_id}_{segment_number:03d}
    if not segment_id.startswith("seg_"):
        print(f"[DEBUG] Invalid segment ID format: {segment_id}")
        return None
    
    # Remove "seg_" prefix
    segment_id_without_prefix = segment_id[4:]
    
    # Find the last underscore to separate video_id from segment_number
    last_underscore_index = segment_id_without_prefix.rfind("_")
    if last_underscore_index == -1:
        print(f"[DEBUG] Invalid segment ID format: {segment_id}")
        return None
    
    video_id = segment_id_without_prefix[:last_underscore_index]
    segment_number_str = segment_id_without_prefix[last_underscore_index + 1:]
    
    try:
        segment_number = int(segment_number_str)
    except ValueError:
        print(f"[DEBUG] Invalid segment number format: {segment_number_str}")
        return None
    
    print(f"[DEBUG] Parsed segment ID: video_id='{video_id}', segment_number={segment_number}")
    
    # Get the video record to find the segment from output_s3_urls
    try:
        video_resp = table.get_item(Key={"video_id": video_id})
        video_item = video_resp.get("Item")
        
        if not video_item:
            print(f"[DEBUG] Video not found: {video_id}")
            return None
        
        # Get the output_s3_urls array
        output_s3_urls = video_item.get("output_s3_urls", [])
        if not output_s3_urls:
            print(f"[DEBUG] No output_s3_urls found for video: {video_id}")
            return None
        
        # Check if segment number is valid
        if segment_number < 1 or segment_number > len(output_s3_urls):
            print(f"[DEBUG] Invalid segment number: {segment_number}, max: {len(output_s3_urls)}")
            return None
        
        # Get the s3_key for this segment
        s3_key = output_s3_urls[segment_number - 1]  # Convert to 0-based index
        
        # Extract filename from s3_key
        filename = s3_key.split("/")[-1] if s3_key else None
        
        # Check if there's additional data in the video-segments table
        additional_data = {}
        try:
            segments_table = boto3.resource('dynamodb', region_name=settings.AWS_REGION).Table('easy-video-share-video-segments')
            response = segments_table.get_item(Key={'segment_id': segment_id})
            segment_item = response.get('Item')
            
            if segment_item:
                print(f"[DEBUG] Found additional data in video-segments table: {segment_id}")
                additional_data = {
                    'thumbnail_url': segment_item.get('thumbnail_url'),
                    'text_overlays': segment_item.get('text_overlays', []),
                    'download_count': segment_item.get('download_count', 0),
                    'social_media_usage': segment_item.get('social_media_usage', [])
                }
        except Exception as e:
            print(f"[DEBUG] Error querying video-segments table for additional data: {e}")
            # Continue without additional data
        
        # Create segment data
        segment_data = VideoSegment(
            segment_id=segment_id,
            video_id=video_id,
            user_id=video_item.get("user_id", ""),
            segment_type=SegmentType.PROCESSED,
            segment_number=segment_number,
            s3_key=s3_key,
            duration=30.0,  # Default duration, could be enhanced to get from S3
            file_size=0,    # Default size, could be enhanced to get from S3
            content_type="video/mp4",
            title=f"{video_item.get('title', 'Video')} - Part {segment_number}",
            description=f"Processed segment {segment_number} of {len(output_s3_urls)}",
            tags=video_item.get("tags", []),
            created_at=video_item.get("created_at", ""),
            updated_at=video_item.get("updated_at", ""),
            filename=filename,
            download_count=additional_data.get('download_count', 0),
            social_media_usage=additional_data.get('social_media_usage', []),
            thumbnail_url=additional_data.get('thumbnail_url')
        )
        
        print(f"[DEBUG] Created segment from output_s3_urls with additional data: {segment_id}")
        return segment_data
        
    except Exception as e:
        print(f"[DEBUG] Error getting segment: {e}")
        return None


def _item_to_video_segment(item: dict) -> VideoSegment:
    """
    Convert DynamoDB item to VideoSegment model.
    """
    try:
        return VideoSegment(
            segment_id=item.get("segment_id"),
            video_id=item.get("video_id"),
            user_id=item.get("user_id"),
            segment_type=SegmentType(item.get("segment_type", "PROCESSED")),
            segment_number=item.get("segment_number", 1),
            s3_key=item.get("s3_key"),
            duration=float(item.get("duration", 30.0)),
            file_size=item.get("file_size", 0),
            content_type=item.get("content_type", "video/mp4"),
            title=item.get("title"),
            description=item.get("description"),
            tags=item.get("tags", []),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
            filename=item.get("filename"),
            download_count=item.get("download_count", 0),
            social_media_usage=item.get("social_media_usage", [])
        )
    except Exception as e:
        print(f"[ERROR] Failed to convert item to VideoSegment: {e}")
        raise e


def list_segments_by_video(video_id: str, segment_type: Optional[SegmentType] = None) -> List[VideoSegment]:
    """
    List all segments for a specific video, optionally filtered by type.
    """
    print(f"[DEBUG] Querying segments for video_id: {video_id}")
    print(f"[DEBUG] Segment type filter: {segment_type}")
    
    # First, get the video record to extract output_s3_urls
    video_resp = table.get_item(Key={"video_id": video_id})
    video_item = video_resp.get("Item")
    
    if not video_item:
        print(f"[DEBUG] Video not found: {video_id}")
        return []
    
    # Check if video has output_s3_urls (processed segments)
    output_s3_urls = video_item.get("output_s3_urls", [])
    if not output_s3_urls:
        print(f"[DEBUG] No output_s3_urls found for video: {video_id}")
        return []
    
    print(f"[DEBUG] Found {len(output_s3_urls)} output URLs for video: {video_id}")
    
    # Create segment objects from the output_s3_urls
    segments = []
    for i, s3_key in enumerate(output_s3_urls, 1):
        try:
            # Generate segment ID
            segment_id = f"seg_{video_id}_{i:03d}"
            
            # Extract filename from s3_key
            filename = s3_key.split("/")[-1] if s3_key else None
            
            # Create segment data
            segment_data = VideoSegment(
                segment_id=segment_id,
                video_id=video_id,
                user_id=video_item.get("user_id", ""),
                segment_type=SegmentType.PROCESSED,
                segment_number=i,
                s3_key=s3_key,
                duration=30.0,  # Default duration, could be enhanced to get from S3
                file_size=0,    # Default size, could be enhanced to get from S3
                content_type="video/mp4",
                title=f"{video_item.get('title', 'Video')} - Part {i}",
                description=f"Processed segment {i} of {len(output_s3_urls)}",
                tags=video_item.get("tags", []),
                created_at=video_item.get("created_at", ""),
                updated_at=video_item.get("updated_at", ""),
                filename=filename,
                download_count=0,
                social_media_usage=[]
            )
            
            segments.append(segment_data)
            print(f"[DEBUG] Created segment {segment_id} from s3_key: {s3_key}")
            
        except Exception as e:
            print(f"[DEBUG] Failed to create segment {i}: {e}")
            continue
    
    print(f"[DEBUG] Successfully created {len(segments)} segments for video {video_id}")
    return segments


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


def increment_download_count(segment_id: str) -> Optional[VideoSegment]:
    """
    Increment the download count for a segment and update last_downloaded_at.
    """
    try:
        now = iso_utc_now()
        resp = table.update_item(
            Key={"segment_id": segment_id},
            UpdateExpression="SET download_count = download_count + :inc, last_downloaded_at = :now, updated_at = :now",
            ExpressionAttributeValues={
                ":inc": 1,
                ":now": now
            },
            ReturnValues="ALL_NEW"
        )
        
        updated_item = resp.get("Attributes")
        return _item_to_video_segment(updated_item) if updated_item else None
    except Exception as e:
        print(f"Error incrementing download count for segment {segment_id}: {e}")
        return None



