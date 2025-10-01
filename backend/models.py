import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    photo_s3_key = Column(String(500), nullable=True)
    audio_s3_key = Column(String(500), nullable=True)
    waveform_s3_key = Column(String(500), nullable=True)
    custom_text = Column(Text, nullable=True)
    photo_shape = Column(String(20), default="square")
    pdf_size = Column(String(20), default="A4")
    template_id = Column(String(50), default="framed_a4_portrait")
    background_id = Column(String(50), default="none")
    font_id = Column(String(50), default="script")
    audio_duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24)
    )

    # Privacy compliance fields
    email = Column(String(255), nullable=True, index=True)
    unsubscribed = Column(Boolean, default=False)
    unsubscribed_at = Column(DateTime, nullable=True)

    # GDPR consent management fields
    consent_data = Column(Text, nullable=True)  # JSON string storing consent records
    consent_updated_at = Column(DateTime, nullable=True)
    data_processing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=False)
    cookie_consent = Column(Boolean, default=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True)
    status = Column(String(50), default="pending")  # pending, completed, failed
    download_token = Column(String(255), unique=True, nullable=True)
    download_expires_at = Column(DateTime, nullable=True)
    pdf_s3_key = Column(String(500), nullable=True)

    # Permanent file storage for migration system
    permanent_photo_s3_key = Column(String(500), nullable=True)
    permanent_audio_s3_key = Column(String(500), nullable=True)
    permanent_waveform_s3_key = Column(String(500), nullable=True)
    permanent_pdf_s3_key = Column(String(500), nullable=True)

    # Migration tracking
    migration_status = Column(
        String(50), default="pending"
    )  # pending, completed, failed
    migration_completed_at = Column(DateTime, nullable=True)
    migration_error = Column(Text, nullable=True)

    # Session association
    session_token = Column(String(255), nullable=True, index=True)

    # Order metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailSubscriber(Base):
    __tablename__ = "email_subscribers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    unsubscribed_at = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True)  # e.g., "checkout", "newsletter", "manual"

    # GDPR compliance
    consent_data = Column(Text, nullable=True)  # JSON string storing consent records
    consent_updated_at = Column(DateTime, nullable=True)
    data_processing_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=False)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminFont(Base):
    __tablename__ = "admin_fonts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to font file
    file_size = Column(Integer, nullable=True)  # File size in bytes
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminSuggestedText(Base):
    __tablename__ = "admin_suggested_texts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # e.g., "romantic", "birthday", "anniversary"
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)  # Track how often it's used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminBackground(Base):
    __tablename__ = "admin_backgrounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to background image
    file_size = Column(Integer, nullable=True)  # File size in bytes
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # e.g., "nature", "abstract", "patterns"
    usage_count = Column(Integer, default=0)  # Track how often it's used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
