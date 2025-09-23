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

    # Privacy Compliance
    company_name: str = Field(default="AudioPoster")  # Company name for CAN-SPAM compliance
    company_address: str = Field(default="123 Business St, City, State 12345")  # Physical address for CAN-SPAM
    privacy_policy_url: str = Field(default="https://audioposter.com/privacy")  # Privacy policy URL
    unsubscribe_url: str = Field(default="https://audioposter.com/unsubscribe")  # Unsubscribe page URL
    data_retention_days: int = Field(default=90)  # Days to retain session data

    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(default=True)  # Enable/disable rate limiting
    rate_limit_requests_per_minute: int = Field(default=10)  # General API requests per minute
    rate_limit_upload_per_hour: int = Field(default=20)  # File uploads per hour per user
    rate_limit_upload_per_day: int = Field(default=100)  # File uploads per day per user
    rate_limit_burst_size: int = Field(default=5)  # Burst allowance for rate limiting
    rate_limit_ban_duration: int = Field(default=3600)  # Ban duration in seconds (1 hour)

    # Content Filtering Configuration
    content_filter_enabled: bool = Field(default=True)  # Enable/disable content filtering
    virus_scan_enabled: bool = Field(default=True)  # Enable/disable virus scanning
    clamav_host: str = Field(default="localhost")  # ClamAV daemon host
    clamav_port: int = Field(default=3310)  # ClamAV daemon port
    max_file_scan_size: int = Field(default=100 * 1024 * 1024)  # Max file size for virus scanning (100MB)
    suspicious_file_patterns: list = Field(default=[
        "*.exe", "*.bat", "*.cmd", "*.scr", "*.pif", "*.com", "*.vbs", "*.js", "*.jar"
    ])  # File patterns to block

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
