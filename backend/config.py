from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
import logging
from .services.security_config import security_config

logger = logging.getLogger(__name__)

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
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))  # development, staging, production

    # Admin Authentication
    admin_password: str = Field(default="admin123")

    # Debug settings
    debug_photo_circle: bool = Field(default=False)  # Show red circle instead of photo for debugging

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
    rate_limit_requests_per_minute: int = Field(default=60)  # General API requests per minute (increased for development)
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

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate secret key security"""
        if not v or v in ['your-secret-key-change-this', 'your-super-secret-key-change-this-in-production']:
            logger.warning("Using default/example SECRET_KEY. This is insecure for production!")
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("Default SECRET_KEY cannot be used in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    def get_rate_limit_requests_per_minute(self) -> int:
        """Get rate limit based on environment"""
        if self.environment == "development":
            return 120  # Very lenient for development
        elif self.environment == "staging":
            return 60   # Moderate for staging
        else:  # production
            return 10   # Strict for production

    def get_rate_limit_burst_size(self) -> int:
        """Get burst size based on environment"""
        if self.environment == "development":
            return 50   # Very lenient for development
        elif self.environment == "staging":
            return 20   # Moderate for staging
        else:  # production
            return 5    # Strict for production

    def is_rate_limit_enabled(self) -> bool:
        """Check if rate limiting should be enabled based on environment"""
        if self.environment == "development":
            return False  # Disable rate limiting in development
        else:
            return self.rate_limit_enabled

    @validator('aws_access_key_id')
    def validate_aws_access_key(cls, v):
        """Validate AWS access key"""
        if v and v in ['your_aws_access_key', 'AKIAIOSFODNN7EXAMPLE']:
            logger.warning("Using default/example AWS_ACCESS_KEY_ID")
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("Default AWS credentials cannot be used in production")
        return v

    @validator('aws_secret_access_key')
    def validate_aws_secret_key(cls, v):
        """Validate AWS secret key"""
        if v and v in ['your_aws_secret_key', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY']:
            logger.warning("Using default/example AWS_SECRET_ACCESS_KEY")
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("Default AWS credentials cannot be used in production")
        return v

    @validator('stripe_secret_key')
    def validate_stripe_secret_key(cls, v):
        """Validate Stripe secret key"""
        if v and v == 'sk_test_your_stripe_secret_key':
            logger.warning("Using default/example STRIPE_SECRET_KEY")
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("Default Stripe credentials cannot be used in production")
        return v

    @validator('sendgrid_api_key')
    def validate_sendgrid_api_key(cls, v):
        """Validate SendGrid API key"""
        if v and v == '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':
            logger.warning("Using default/example SENDGRID_API_KEY")
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("Default SendGrid credentials cannot be used in production")
        return v

    def validate_security(self) -> dict:
        """Validate overall security configuration"""
        return security_config.validate_environment()

    def get_masked_config(self) -> dict:
        """Get configuration with sensitive values masked for logging"""
        config_dict = self.dict()
        sensitive_fields = [
            'secret_key', 'aws_access_key_id', 'aws_secret_access_key',
            'stripe_secret_key', 'stripe_webhook_secret', 'sendgrid_api_key',
            'local_encryption_key', 'admin_password'
        ]

        for field in sensitive_fields:
            if field in config_dict and config_dict[field]:
                config_dict[field] = security_config.mask_sensitive_value(config_dict[field])

        return config_dict

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

# Validate security on startup
settings = Settings()
security_validation = settings.validate_security()

if not security_validation['valid']:
    logger.error("Security validation failed:")
    for error in security_validation['errors']:
        logger.error(f"  - {error}")
    for issue in security_validation['security_issues']:
        logger.error(f"  - SECURITY ISSUE: {issue}")

    if os.getenv('ENVIRONMENT') == 'production':
        raise ValueError("Security validation failed in production environment")

for warning in security_validation['warnings']:
    logger.warning(f"Security warning: {warning}")
