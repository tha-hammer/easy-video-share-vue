from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal
from enum import Enum


class TextStrategy(str, Enum):
    """Text overlay strategy options"""
    ONE_FOR_ALL = "one_for_all"
    BASE_VARY = "base_vary"
    UNIQUE_FOR_ALL = "unique_for_all"


class FixedCuttingParams(BaseModel):
    """Fixed duration cutting parameters"""
    type: Literal["fixed"] = "fixed"
    duration_seconds: int = Field(..., description="Fixed segment duration in seconds")


class RandomCuttingParams(BaseModel):
    """Random duration cutting parameters"""
    type: Literal["random"] = "random"
    min_duration: int = Field(..., description="Minimum segment duration in seconds")
    max_duration: int = Field(..., description="Maximum segment duration in seconds")


CuttingOptions = Union[FixedCuttingParams, RandomCuttingParams]


class TextInput(BaseModel):
    """Text input for different text strategies"""
    strategy: TextStrategy = Field(..., description="Text overlay strategy")
    base_text: Optional[str] = Field(None, description="Base text for ONE_FOR_ALL and BASE_VARY strategies")
    context: Optional[str] = Field(None, description="Context for LLM prompt (e.g., 'sales', 'engagement', 'educational')")
    unique_texts: Optional[List[str]] = Field(None, description="Individual text for each segment (UNIQUE_FOR_ALL)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy": "base_vary",
                "base_text": "Check out our amazing product!",
                "context": "sales, urgency, call-to-action",
                "unique_texts": None
            }
        }


class InitiateUploadRequest(BaseModel):
    """Request model for initiating video upload to S3"""
    filename: str = Field(..., description="Original filename of the video")
    content_type: str = Field(..., description="MIME type of the video file")
    file_size: int = Field(..., description="Size of the file in bytes")


class InitiateUploadResponse(BaseModel):
    """Response model for S3 presigned URL and upload details"""
    presigned_url: str = Field(..., description="S3 presigned URL for direct upload")
    s3_key: str = Field(..., description="S3 object key for the uploaded file")
    job_id: str = Field(..., description="Unique job identifier")


# === MULTI-PART UPLOAD MODELS ===

class InitiateMultipartUploadRequest(BaseModel):
    """Request model for initiating multi-part upload to S3"""
    filename: str = Field(..., description="Original filename of the video")
    content_type: str = Field(..., description="MIME type of the video file")
    file_size: int = Field(..., description="Size of the file in bytes")


class InitiateMultipartUploadResponse(BaseModel):
    """Response model for multi-part upload initiation"""
    upload_id: str = Field(..., description="S3 multi-part upload ID")
    s3_key: str = Field(..., description="S3 object key for the uploaded file")
    job_id: str = Field(..., description="Unique job identifier")
    chunk_size: int = Field(..., description="Recommended chunk size in bytes")
    max_concurrent_uploads: int = Field(..., description="Maximum concurrent uploads")


class UploadPartRequest(BaseModel):
    """Request model for uploading a single part"""
    upload_id: str = Field(..., description="S3 multi-part upload ID")
    s3_key: str = Field(..., description="S3 object key")
    part_number: int = Field(..., description="Part number (1-based)")
    content_type: str = Field(..., description="MIME type of the part")


class UploadPartResponse(BaseModel):
    """Response model for part upload"""
    presigned_url: str = Field(..., description="Presigned URL for uploading this part")
    part_number: int = Field(..., description="Part number")


class CompleteMultipartUploadRequest(BaseModel):
    """Request model for completing multi-part upload"""
    upload_id: str = Field(..., description="S3 multi-part upload ID")
    s3_key: str = Field(..., description="S3 object key")
    job_id: str = Field(..., description="Job identifier")
    parts: List[dict] = Field(..., description="List of uploaded parts with ETags")
    # Additional metadata for job creation
    cutting_options: Optional[CuttingOptions] = Field(None, description="Video cutting parameters")
    text_strategy: Optional[TextStrategy] = Field(None, description="Text overlay strategy")
    text_input: Optional[TextInput] = Field(None, description="Text content and context for overlay")
    user_id: Optional[str] = Field(..., description="User identifier for tracking job ownership")
    filename: Optional[str] = Field(None, description="Original filename of the video")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")
    title: Optional[str] = Field(None, description="Video title")
    user_email: Optional[str] = Field(None, description="User email address")
    content_type: Optional[str] = Field(None, description="MIME type of the video file")


class AbortMultipartUploadRequest(BaseModel):
    """Request model for aborting multi-part upload"""
    upload_id: str = Field(..., description="S3 multi-part upload ID")
    s3_key: str = Field(..., description="S3 object key")


class CompleteUploadRequest(BaseModel):
    """Request model for completing upload and starting processing"""
    s3_key: str = Field(..., description="S3 object key of the uploaded file")
    job_id: str = Field(..., description="Job identifier from initiate upload")
    cutting_options: Optional[CuttingOptions] = Field(None, description="Video cutting parameters")
    text_strategy: Optional[TextStrategy] = Field(None, description="Text overlay strategy")
    text_input: Optional[TextInput] = Field(None, description="Text content and context for overlay")
    user_id: Optional[str] = Field(..., description="User identifier for tracking job ownership")
    filename: Optional[str] = Field(None, description="Original filename of the video")
    file_size: Optional[int] = Field(None, description="Size of the file in bytes")
    title: Optional[str] = Field(None, description="Video title")
    user_email: Optional[str] = Field(None, description="User email address")
    content_type: Optional[str] = Field(None, description="MIME type of the video file")


class JobCreatedResponse(BaseModel):
    """Response model after job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response model for job status queries"""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current job status")
    progress: Optional[int] = Field(None, description="Processing progress percentage")
    output_urls: Optional[List[str]] = Field(None, description="S3 URLs of processed video segments")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    created_at: Optional[str] = Field(None, description="Job creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    video_duration: Optional[float] = Field(None, description="Video duration in seconds (if available)")


class AnalyzeDurationRequest(BaseModel):
    """Request model for analyzing video duration"""
    s3_key: str = Field(..., description="S3 object key of the video to analyze")
    cutting_options: CuttingOptions = Field(..., description="Cutting parameters")


class AnalyzeDurationResponse(BaseModel):
    """Response model for video duration analysis"""
    total_duration: float = Field(..., description="Total video duration in seconds")
    num_segments: int = Field(..., description="Estimated number of segments")
    segment_durations: List[float] = Field(..., description="Duration of each segment")


class ProgressUpdate(BaseModel):
    """Model for streaming job progress updates via SSE"""
    job_id: str
    stage: str
    message: str
    current_segment: Optional[int] = None
    total_segments: Optional[int] = None
    progress_percentage: float
    timestamp: str
    output_urls: Optional[List[str]] = None
    error_message: Optional[str] = None


class DynamoDBJobEntry(BaseModel):
    """Model representing a job entry in DynamoDB"""
    video_id: str = Field(..., description="Job identifier (same as job_id)")
    user_id: str = Field(..., description="User identifier")
    upload_date: str = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Current job status")
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    video_duration: Optional[float] = Field(None, description="Video duration in seconds")
    output_s3_urls: Optional[List[str]] = Field(None, description="S3 URLs of processed video segments")
    error_message: Optional[str] = Field(None, description="Error message if job failed")


# === SEGMENT MODELS ===

class SegmentType(str, Enum):
    """Segment type options"""
    PROCESSED = "processed"
    ORIGINAL = "original"
    THUMBNAIL = "thumbnail"
    AUDIO = "audio"


class SocialMediaPlatform(str, Enum):
    """Social media platform options"""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class SocialMediaUsage(BaseModel):
    """Model for tracking social media usage of segments"""
    platform: SocialMediaPlatform = Field(..., description="Social media platform")
    post_id: Optional[str] = Field(None, description="Platform-specific post ID")
    post_url: Optional[str] = Field(None, description="URL to the social media post")
    posted_at: Optional[str] = Field(None, description="When the segment was posted")
    views: int = Field(default=0, description="Number of views")
    likes: int = Field(default=0, description="Number of likes")
    shares: int = Field(default=0, description="Number of shares")
    comments: int = Field(default=0, description="Number of comments")
    engagement_rate: Optional[float] = Field(None, description="Engagement rate percentage")
    last_synced: Optional[str] = Field(None, description="Last time metrics were synced")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "instagram",
                "post_id": "123456789",
                "post_url": "https://instagram.com/p/123456789",
                "posted_at": "2024-01-15T10:30:00Z",
                "views": 1500,
                "likes": 120,
                "shares": 25,
                "comments": 15,
                "engagement_rate": 8.5,
                "last_synced": "2024-01-16T09:00:00Z"
            }
        }


class VideoSegment(BaseModel):
    """Model representing a video segment"""
    segment_id: str = Field(..., description="Unique segment identifier")
    video_id: str = Field(..., description="Parent video identifier")
    user_id: str = Field(..., description="User identifier")
    segment_type: SegmentType = Field(..., description="Type of segment")
    segment_number: int = Field(..., description="Segment number within the video")
    s3_key: str = Field(..., description="S3 object key for the segment")
    s3_url: Optional[str] = Field(None, description="Presigned S3 URL for the segment")
    duration: float = Field(..., description="Segment duration in seconds")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(default="video/mp4", description="MIME type")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for the segment")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    title: Optional[str] = Field(None, description="Segment title")
    description: Optional[str] = Field(None, description="Segment description")
    tags: Optional[List[str]] = Field(default=[], description="Tags for the segment")
    social_media_usage: Optional[List[SocialMediaUsage]] = Field(default=[], description="Social media usage tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "seg_123456789",
                "video_id": "vid_123456789",
                "user_id": "user_123",
                "segment_type": "processed",
                "segment_number": 1,
                "s3_key": "processed/vid_123456789/segment_001.mp4",
                "duration": 15.5,
                "file_size": 2048576,
                "content_type": "video/mp4",
                "thumbnail_url": "https://s3.amazonaws.com/bucket/thumbnails/seg_123456789.jpg",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "title": "Amazing Product Demo - Part 1",
                "description": "First segment showcasing product features",
                "tags": ["demo", "product", "feature"],
                "social_media_usage": []
            }
        }


class SegmentCreateRequest(BaseModel):
    """Request model for creating a new segment"""
    video_id: str = Field(..., description="Parent video identifier")
    segment_type: SegmentType = Field(..., description="Type of segment")
    segment_number: int = Field(..., description="Segment number within the video")
    s3_key: str = Field(..., description="S3 object key for the segment")
    duration: float = Field(..., description="Segment duration in seconds")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(default="video/mp4", description="MIME type")
    title: Optional[str] = Field(None, description="Segment title")
    description: Optional[str] = Field(None, description="Segment description")
    tags: Optional[List[str]] = Field(default=[], description="Tags for the segment")


class SegmentUpdateRequest(BaseModel):
    """Request model for updating a segment"""
    title: Optional[str] = Field(None, description="Segment title")
    description: Optional[str] = Field(None, description="Segment description")
    tags: Optional[List[str]] = Field(None, description="Tags for the segment")


class SegmentListResponse(BaseModel):
    """Response model for listing segments"""
    segments: List[VideoSegment] = Field(..., description="List of segments")
    total_count: int = Field(..., description="Total number of segments")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class SegmentFilters(BaseModel):
    """Model for segment filtering options"""
    segment_type: Optional[SegmentType] = Field(None, description="Filter by segment type")
    min_duration: Optional[float] = Field(None, description="Minimum duration in seconds")
    max_duration: Optional[float] = Field(None, description="Maximum duration in seconds")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    has_social_media: Optional[bool] = Field(None, description="Filter segments with social media usage")
    platform: Optional[SocialMediaPlatform] = Field(None, description="Filter by social media platform")
    sort_by: Optional[str] = Field(default="created_at", description="Sort field")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")


class SocialMediaSyncRequest(BaseModel):
    """Request model for syncing social media metrics"""
    segment_id: str = Field(..., description="Segment identifier")
    platform: SocialMediaPlatform = Field(..., description="Social media platform")
    post_id: Optional[str] = Field(None, description="Platform-specific post ID")
    post_url: Optional[str] = Field(None, description="URL to the social media post")


class SocialMediaAnalyticsResponse(BaseModel):
    """Response model for social media analytics"""
    segment_id: str = Field(..., description="Segment identifier")
    total_views: int = Field(..., description="Total views across all platforms")
    total_likes: int = Field(..., description="Total likes across all platforms")
    total_shares: int = Field(..., description="Total shares across all platforms")
    total_comments: int = Field(..., description="Total comments across all platforms")
    total_engagement: int = Field(..., description="Total engagement (likes + shares + comments)")
    average_engagement_rate: float = Field(..., description="Average engagement rate percentage")
    platform_breakdown: List[SocialMediaUsage] = Field(..., description="Breakdown by platform")
    top_performing_platform: Optional[SocialMediaPlatform] = Field(None, description="Best performing platform")
    last_updated: str = Field(..., description="Last update timestamp")
