from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal
from enum import Enum


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


class CompleteUploadRequest(BaseModel):
    """Request model for completing upload and starting processing"""
    s3_key: str = Field(..., description="S3 object key of the uploaded file")
    job_id: str = Field(..., description="Job identifier from initiate upload")


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


class AnalyzeDurationRequest(BaseModel):
    """Request model for analyzing video duration"""
    s3_key: str = Field(..., description="S3 object key of the video to analyze")
    cutting_options: CuttingOptions = Field(..., description="Cutting parameters")


class AnalyzeDurationResponse(BaseModel):
    """Response model for video duration analysis"""
    total_duration: float = Field(..., description="Total video duration in seconds")
    num_segments: int = Field(..., description="Estimated number of segments")
    segment_durations: List[float] = Field(..., description="Duration of each segment")
