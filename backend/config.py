from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: str
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # DynamoDB
    DYNAMODB_TABLE_NAME: str = "easy-video-share-video-metadata"

    # Celery/Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Railway-specific Redis configuration
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_PASSWORD: Optional[str] = None

    # Google Cloud Vertex AI Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: Optional[str] = None

    # FastAPI Configuration
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Video Processing Configuration
    MAX_VIDEO_SIZE_MB: int = 5000
    SEGMENT_DURATION_SECONDS: int = 30

    # Railway-specific settings
    RAILWAY_ENVIRONMENT: Optional[str] = None
    RAILWAY_STATIC_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Railway-specific Redis URL construction
        if self.REDIS_HOST:
            redis_url_parts = [f"redis://"]
            if self.REDIS_PASSWORD:
                redis_url_parts.append(f":{self.REDIS_PASSWORD}@")
            redis_url_parts.append(f"{self.REDIS_HOST}")
            if self.REDIS_PORT:
                redis_url_parts.append(f":{self.REDIS_PORT}")
            redis_url_parts.append("/0")
            self.REDIS_URL = "".join(redis_url_parts)
        
        # Detect Railway environment
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_STATIC_URL"):
            self.RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "false")

    @property
    def is_railway_environment(self) -> bool:
        """Check if running in Railway environment"""
        return self.RAILWAY_ENVIRONMENT is not None and self.RAILWAY_ENVIRONMENT.lower() in ['true', 'production', 'staging']

# Create global settings instance
settings = Settings()