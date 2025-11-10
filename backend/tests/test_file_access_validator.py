import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend.config import settings
from backend.services.file_access_validator import FileAccessValidator
from .conftest import TestSessionModel


class TestFileAccessValidatorPreviewAccess:
    """Tests for preview audio access validation logic"""

    def test_preview_session_within_extension_window(self, db_session):
        """Expired sessions inside preview window should still be accessible"""
        validator = FileAccessValidator()
        now = datetime.utcnow()
        session = TestSessionModel(
            id=str(uuid.uuid4()),
            session_token="preview-session-accessible",
            audio_s3_key="temp_audio/preview-session-accessible.mp3",
            created_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=5),
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        result = validator.validate_audio_playback_access(
            db_session, session.session_token
        )

        assert result["type"] == "session"
        assert result["audio_key"] == "temp_audio/preview-session-accessible.mp3"

        refreshed = (
            db_session.query(TestSessionModel)
            .filter(TestSessionModel.session_token == session.session_token)
            .first()
        )
        expected_expiration = session.created_at + timedelta(
            seconds=settings.qr_code_preview_expiration
        )
        assert refreshed.expires_at >= expected_expiration

    def test_preview_session_beyond_extension_window(self, db_session):
        """Sessions older than preview window should raise expiration errors"""
        validator = FileAccessValidator()
        now = datetime.utcnow()
        session = TestSessionModel(
            id=str(uuid.uuid4()),
            session_token="preview-session-expired",
            audio_s3_key="temp_audio/preview-session-expired.mp3",
            created_at=now
            - timedelta(seconds=settings.qr_code_preview_expiration + 60),
            expires_at=now - timedelta(days=1),
        )
        db_session.add(session)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            validator.validate_audio_playback_access(
                db_session, session.session_token
            )

        assert exc_info.value.status_code == 410
        assert "expired" in exc_info.value.detail.lower()
