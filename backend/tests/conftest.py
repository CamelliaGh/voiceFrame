"""
Pytest configuration and fixtures
"""
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Set test environment before importing main
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["TESTING"] = "true"

# Create test-specific models for SQLite compatibility
TestBase = declarative_base()


class TestSessionModel(TestBase):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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


class TestOrder(TestBase):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    stripe_payment_intent_id = Column(String(255), nullable=True)
    session_token = Column(String(255), nullable=True)
    permanent_photo_s3_key = Column(String(500), nullable=True)
    permanent_audio_s3_key = Column(String(500), nullable=True)
    permanent_waveform_s3_key = Column(String(500), nullable=True)
    permanent_pdf_s3_key = Column(String(500), nullable=True)
    migration_status = Column(String(20), default="pending")
    migration_completed_at = Column(DateTime, nullable=True)
    migration_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestEmailSubscriber(TestBase):
    __tablename__ = "email_subscribers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Test database URL (in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from ..database import get_db

# Import main app after setting up test models
from ..main import app


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create tables using test models
    TestBase.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_session(db_session):
    """Create a sample session for testing"""
    session = TestSessionModel(
        id=str(uuid.uuid4()),
        session_token="test-session-token",
        photo_s3_key="temp_photos/test.jpg",
        audio_s3_key="temp_audio/test.mp3",
        waveform_s3_key="waveforms/test.png",
        custom_text="Test text",
        photo_shape="square",
        pdf_size="A4",
        template_id="framed_a4_portrait",
        background_id="none",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def sample_order(db_session):
    """Create a sample order for testing"""
    order = TestOrder(
        id=str(uuid.uuid4()),
        email="test@example.com",
        amount_cents=999,
        status="completed",
        session_token="test-session-token",
        permanent_audio_s3_key="permanent/audio/test.mp3",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing"""
    with patch("backend.services.file_uploader.boto3.client") as mock_client:
        mock_s3 = mock_client.return_value
        mock_s3.upload_fileobj.return_value = None
        mock_s3.generate_presigned_url.return_value = "https://example.com/test-url"
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        mock_s3.list_objects_v2.return_value = {"Contents": []}
        mock_s3.delete_object.return_value = None
        yield mock_s3


@pytest.fixture
def mock_stripe_service():
    """Mock Stripe service for testing"""
    with patch("backend.main.stripe_service") as mock_stripe:
        mock_stripe.verify_payment.return_value = {"status": "succeeded"}
        mock_stripe.create_payment_intent.return_value = {
            "id": "pi_test",
            "client_secret": "pi_test_secret",
        }
        yield mock_stripe


@pytest.fixture
def mock_email_service():
    """Mock email service for testing"""
    with patch("backend.main.email_service") as mock_email:
        mock_email.send_download_email.return_value = True
        yield mock_email


@pytest.fixture
def mock_storage_manager():
    """Mock storage manager for testing"""
    with patch("backend.main.storage_manager") as mock_storage:
        mock_storage.migrate_all_session_files.return_value = {
            "permanent_photo_s3_key": "permanent/photos/test.jpg",
            "permanent_audio_s3_key": "permanent/audio/test.mp3",
            "permanent_waveform_s3_key": "permanent/waveforms/test.png",
        }
        mock_storage.verify_migration_success.return_value = True
        yield mock_storage
