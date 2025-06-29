from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"  # Match the S3 bucket region
    AWS_BUCKET_NAME: str = "easy-video-share-silmari-dev"
    AWS_PROFILE: str = "AdministratorAccess-571960159088"  # SSO Profile name
    AWS_ACCESS_KEY_ID: Optional[str] = None  # Optional - will use AWS CLI if not set
    AWS_SECRET_ACCESS_KEY: Optional[str] = None  # Optional - will use AWS CLI if not set
    
    # DynamoDB
    DYNAMODB_TABLE_NAME: str = "easy-video-share-video-metadata"
    
    # Celery/Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Google Cloud Vertex AI Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "us-central1"  # Default region for Vertex AI
    
    # FastAPI Configuration
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Video Processing Configuration
    MAX_VIDEO_SIZE_MB: int = 500
    SEGMENT_DURATION_SECONDS: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global settings instance
settings = Settings()
