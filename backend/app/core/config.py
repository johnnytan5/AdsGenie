"""
Application configuration settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = "AdsGenie API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AdsGenie Backend API"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # AWS Configuration
    AWS_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # DynamoDB
    DYNAMODB_TABLE_NAME: str = "Projects"
    DYNAMODB_ENDPOINT_URL: Optional[str] = None  # For local development

    # S3
    S3_BUCKET_NAME: str = "adsgenie-assets"
    S3_ENDPOINT_URL: Optional[str] = None  # For local development

    # AI Services - Google GenAI (used for both NanoBanana and VEO3)
    GOOGLE_API_KEY: Optional[str] = None

    # AI Services - OpenAI (used for music type determination)
    OPENAI_API_KEY: Optional[str] = None

    # Audio Services - ElevenLabs
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = "yj4ZLC16WtrBEwPzIXzI"

    # Frontend URL for webhooks
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
