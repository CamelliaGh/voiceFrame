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
    s3_kms_key_id: str = Field(default="")  # AWS KMS key ID for encryption

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
    project_root: str = Field(default="/app")

    # File Processing
    max_photo_size: int = Field(default=50 * 1024 * 1024)  # 50MB
    max_audio_size: int = Field(default=100 * 1024 * 1024)  # 100MB
    max_audio_duration: int = Field(default=600)  # 10 minutes

    # Encryption
    local_encryption_key: str = Field(default="")  # Base64 encoded key for local file encryption
    use_kms_encryption: bool = Field(default=False)  # Use AWS KMS instead of S3 managed keys

    # QR Code Expiration Times (in seconds)
    qr_code_preview_expiration: int = Field(default=604800)  # 7 days for preview QR codes
    qr_code_permanent_expiration: int = Field(default=157788000)  # 5 years for paid user QR codes

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
