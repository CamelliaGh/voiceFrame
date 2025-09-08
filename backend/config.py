from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="postgresql://user:password@localhost/audioposter")
    redis_url: str = Field(default="redis://localhost:6379")
    
    # AWS S3
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    s3_bucket: str = Field(default="audioposter-files")
    s3_region: str = Field(default="us-east-2")
    
    # Stripe
    stripe_public_key: str = Field(default="")
    stripe_secret_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    
    # SendGrid
    sendgrid_api_key: str = Field(default="")
    from_email: str = Field(default="noreply@audioposter.com")
    
    # Application
    secret_key: str = Field(default="your-secret-key-change-this")
    base_url: str = Field(default="http://localhost:3000")
    debug: bool = Field(default=True)
    
    # File Processing
    max_photo_size: int = Field(default=50 * 1024 * 1024)  # 50MB
    max_audio_size: int = Field(default=100 * 1024 * 1024)  # 100MB
    max_audio_duration: int = Field(default=600)  # 10 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
