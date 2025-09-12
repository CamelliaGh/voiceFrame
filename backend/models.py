from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import uuid

from .database import Base

class SessionModel(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    photo_s3_key = Column(String(500), nullable=True)
    audio_s3_key = Column(String(500), nullable=True)
    waveform_s3_key = Column(String(500), nullable=True)
    custom_text = Column(Text, nullable=True)
    photo_shape = Column(String(20), default='square')
    pdf_size = Column(String(20), default='A4')
    template_id = Column(String(50), default='classic')
    background_id = Column(String(50), default='none')
    audio_duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True)
    status = Column(String(50), default='pending')  # pending, completed, failed
    download_token = Column(String(255), unique=True, nullable=True)
    download_expires_at = Column(DateTime, nullable=True)
    pdf_s3_key = Column(String(500), nullable=True)
    
    # Permanent file storage for migration system
    permanent_photo_s3_key = Column(String(500), nullable=True)
    permanent_audio_s3_key = Column(String(500), nullable=True)
    permanent_waveform_s3_key = Column(String(500), nullable=True)
    permanent_pdf_s3_key = Column(String(500), nullable=True)
    
    # Migration tracking
    migration_status = Column(String(50), default='pending')  # pending, completed, failed
    migration_completed_at = Column(DateTime, nullable=True)
    migration_error = Column(Text, nullable=True)
    
    # Session reference
    session_token = Column(String(255), nullable=True)  # Link to original session
    audio_secure_hash = Column(String(64), nullable=True)  # SHA-256 for integrity
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailSubscriber(Base):
    __tablename__ = "email_subscribers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    subscribed = Column(Boolean, default=True)
    source = Column(String(50), default='purchase')  # purchase, referral, etc
    first_purchase_date = Column(DateTime, nullable=True)
    total_purchases = Column(Integer, default=1)
    total_spent_cents = Column(Integer, default=0)
    last_campaign_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    is_premium = Column(Boolean, default=False)
    layout_config = Column(Text, nullable=True)  # JSON string
    preview_image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
