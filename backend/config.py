from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # AWS Configuration
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # DynamoDB
    DYNAMODB_TABLE_NAME: str

    # Celery/Redis Configuration
    REDIS_URL: str

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()