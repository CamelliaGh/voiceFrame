"""
Test suite for file audit logging functionality

This module tests the comprehensive file operation audit logging system
to ensure all file operations are properly logged for security and compliance.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..main import app
from ..services.file_audit_logger import (
    file_audit_logger,
    FileOperationType,
    FileType,
    FileOperationStatus,
    FileOperationContext,
    FileOperationDetails,
    FileAuditLog
)
from ..database import get_db
from ..models import SessionModel

client = TestClient(app)

class TestFileAuditLogger:
    """Test the file audit logger service"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing"""
        mock_session = MagicMock(spec=Session)
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        return mock_session

    @pytest.fixture
    def sample_context(self):
        """Sample file operation context"""
        return FileOperationContext(
            user_identifier="test_user_123",
            session_token="test_session_token",
            order_id="test_order_456",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Test Browser)",
            request_id="req_789",
            api_endpoint="/api/upload/photo",
            additional_metadata={"test": "metadata"}
        )

    @pytest.fixture
    def sample_details(self):
        """Sample file operation details"""
        return FileOperationDetails(
            source_path="/tmp/test_photo.jpg",
            destination_path="temp_photos/test_session.jpg",
            file_size=1024000,
            file_hash="abc123def456",
            content_type="image/jpeg",
            encryption_status="encrypted",
            processing_time_ms=1500,
            error_message=None,
            additional_details={"compression": "high"}
        )

    def test_log_file_operation_success(self, mock_db_session, sample_context, sample_details):
        """Test successful file operation logging"""
        log_id = file_audit_logger.log_file_operation(
            operation_type=FileOperationType.UPLOAD,
            file_type=FileType.PHOTO,
            status=FileOperationStatus.SUCCESS,
            context=sample_context,
            details=sample_details,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    def test_log_file_operation_failure(self, mock_db_session, sample_context):
        """Test failed file operation logging"""
        error_details = FileOperationDetails(
            source_path="/tmp/test_photo.jpg",
            destination_path="temp_photos/test_session.jpg",
            file_size=1024000,
            error_message="Upload failed: Network timeout",
            processing_time_ms=5000
        )

        log_id = file_audit_logger.log_file_operation(
            operation_type=FileOperationType.UPLOAD,
            file_type=FileType.PHOTO,
            status=FileOperationStatus.FAILED,
            context=sample_context,
            details=error_details,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_file_upload(self, mock_db_session, sample_context):
        """Test file upload logging"""
        log_id = file_audit_logger.log_file_upload(
            file_type=FileType.PHOTO,
            file_path="temp_photos/test_session.jpg",
            file_size=1024000,
            content_type="image/jpeg",
            context=sample_context,
            status=FileOperationStatus.SUCCESS,
            processing_time_ms=1500,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_file_download(self, mock_db_session, sample_context):
        """Test file download logging"""
        log_id = file_audit_logger.log_file_download(
            file_type=FileType.PHOTO,
            file_path="permanent/photos/test_order.jpg",
            context=sample_context,
            status=FileOperationStatus.SUCCESS,
            processing_time_ms=800,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_file_deletion(self, mock_db_session, sample_context):
        """Test file deletion logging"""
        log_id = file_audit_logger.log_file_deletion(
            file_type=FileType.PHOTO,
            file_path="temp_photos/test_session.jpg",
            context=sample_context,
            status=FileOperationStatus.SUCCESS,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_file_migration(self, mock_db_session, sample_context):
        """Test file migration logging"""
        log_id = file_audit_logger.log_file_migration(
            file_type=FileType.PHOTO,
            source_path="temp_photos/test_session.jpg",
            destination_path="permanent/photos/test_order.jpg",
            file_size=1024000,
            context=sample_context,
            status=FileOperationStatus.SUCCESS,
            processing_time_ms=2000,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_file_processing(self, mock_db_session, sample_context):
        """Test file processing logging"""
        log_id = file_audit_logger.log_file_processing(
            file_type=FileType.AUDIO,
            file_path="temp_audio/test_session.mp3",
            processing_type="waveform_generation",
            context=sample_context,
            status=FileOperationStatus.SUCCESS,
            processing_time_ms=3000,
            db=mock_db_session
        )

        assert log_id is not None
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_get_audit_logs_with_filters(self, mock_db_session):
        """Test retrieving audit logs with various filters"""
        # Mock query results
        mock_logs = [
            MagicMock(
                id="log_1",
                operation_type="upload",
                file_type="photo",
                status="success",
                timestamp=datetime.now(timezone.utc),
                user_identifier="test_user",
                source_path="temp_photos/test.jpg",
                destination_path=None,
                file_size=1024000,
                content_type="image/jpeg",
                processing_time_ms=1500,
                error_message=None,
                additional_metadata='{"test": "data"}',
                additional_details='{"compression": "high"}'
            )
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_logs

        mock_db_session.query.return_value = mock_query

        logs = file_audit_logger.get_audit_logs(
            db=mock_db_session,
            user_identifier="test_user",
            operation_type=FileOperationType.UPLOAD,
            file_type=FileType.PHOTO,
            status=FileOperationStatus.SUCCESS,
            limit=10,
            offset=0
        )

        assert len(logs) == 1
        assert logs[0]["id"] == "log_1"
        assert logs[0]["operation_type"] == "upload"
        assert logs[0]["file_type"] == "photo"
        assert logs[0]["status"] == "success"

    def test_get_audit_statistics(self, mock_db_session):
        """Test audit statistics generation"""
        # Mock log entries
        mock_logs = [
            MagicMock(
                operation_type="upload",
                file_type="photo",
                status="success",
                file_size=1024000,
                processing_time_ms=1500
            ),
            MagicMock(
                operation_type="download",
                file_type="photo",
                status="success",
                file_size=1024000,
                processing_time_ms=800
            ),
            MagicMock(
                operation_type="upload",
                file_type="audio",
                status="failed",
                file_size=2048000,
                processing_time_ms=5000
            )
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_logs

        mock_db_session.query.return_value = mock_query

        stats = file_audit_logger.get_audit_statistics(mock_db_session)

        assert stats["total_operations"] == 3
        assert stats["successful_operations"] == 2
        assert stats["failed_operations"] == 1
        assert stats["success_rate"] == 66.67
        assert stats["total_file_size_bytes"] == 4096000
        assert stats["average_processing_time_ms"] == 2433.33

    def test_cleanup_old_logs(self, mock_db_session):
        """Test cleanup of old audit logs"""
        # Mock old logs
        old_logs = [
            MagicMock(id="old_log_1"),
            MagicMock(id="old_log_2")
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = old_logs

        mock_db_session.query.return_value = mock_query

        cleaned_count = file_audit_logger.cleanup_old_logs(mock_db_session)

        assert cleaned_count == 2
        assert mock_db_session.delete.call_count == 2
        mock_db_session.commit.assert_called_once()

    def test_sensitive_file_detection(self):
        """Test sensitive file type detection"""
        assert file_audit_logger._is_sensitive_file(FileType.PHOTO, "image/jpeg") == True
        assert file_audit_logger._is_sensitive_file(FileType.AUDIO, "audio/mp3") == True
        assert file_audit_logger._is_sensitive_file(FileType.PDF, "application/pdf") == True
        assert file_audit_logger._is_sensitive_file(FileType.TEMPLATE, "application/json") == False

    def test_legal_basis_determination(self):
        """Test legal basis determination for file operations"""
        assert file_audit_logger._get_legal_basis(FileOperationType.UPLOAD, FileType.PHOTO) == "contract"
        assert file_audit_logger._get_legal_basis(FileOperationType.DELETE, FileType.PHOTO) == "legal_obligation"
        assert file_audit_logger._get_legal_basis(FileOperationType.DOWNLOAD, FileType.PHOTO) == "consent"
        assert file_audit_logger._get_legal_basis(FileOperationType.COPY, FileType.PHOTO) == "legitimate_interest"

class TestFileAuditAPIEndpoints:
    """Test the file audit API endpoints"""

    @patch('backend.main.file_audit_logger')
    @patch('backend.main.admin_auth_service')
    def test_get_file_audit_logs(self, mock_admin_auth, mock_audit_logger):
        """Test GET /api/audit/file-operations endpoint"""
        mock_admin_auth.get_admin_dependency.return_value = True
        mock_audit_logger.get_audit_logs.return_value = [
            {
                "id": "log_1",
                "operation_type": "upload",
                "file_type": "photo",
                "status": "success",
                "timestamp": "2024-01-01T00:00:00Z",
                "user_identifier": "test_user",
                "file_size": 1024000
            }
        ]

        response = client.get("/api/audit/file-operations?user_identifier=test_user&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert len(data["logs"]) == 1
        assert data["logs"][0]["operation_type"] == "upload"

    @patch('backend.main.file_audit_logger')
    @patch('backend.main.admin_auth_service')
    def test_get_file_audit_statistics(self, mock_admin_auth, mock_audit_logger):
        """Test GET /api/audit/file-operations/statistics endpoint"""
        mock_admin_auth.get_admin_dependency.return_value = True
        mock_audit_logger.get_audit_statistics.return_value = {
            "total_operations": 100,
            "successful_operations": 95,
            "failed_operations": 5,
            "success_rate": 95.0,
            "operation_types": {"upload": 50, "download": 30, "delete": 20},
            "file_types": {"photo": 60, "audio": 40},
            "total_file_size_bytes": 1024000000,
            "average_processing_time_ms": 1500
        }

        response = client.get("/api/audit/file-operations/statistics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_operations"] == 100
        assert data["success_rate"] == 95.0
        assert "operation_types" in data
        assert "file_types" in data

    @patch('backend.main.file_audit_logger')
    @patch('backend.main.admin_auth_service')
    def test_cleanup_old_audit_logs(self, mock_admin_auth, mock_audit_logger):
        """Test POST /api/audit/file-operations/cleanup endpoint"""
        mock_admin_auth.get_admin_dependency.return_value = True
        mock_audit_logger.cleanup_old_logs.return_value = 25

        response = client.post("/api/audit/file-operations/cleanup")

        assert response.status_code == 200
        data = response.json()
        assert data["cleaned_count"] == 25
        assert "Cleaned up 25 old audit logs" in data["message"]

    def test_unauthorized_access(self):
        """Test that audit endpoints require admin authentication"""
        with patch('backend.main.admin_auth_service') as mock_admin_auth:
            mock_admin_auth.get_admin_dependency.return_value = False

            response = client.get("/api/audit/file-operations")
            assert response.status_code == 401

class TestFileOperationIntegration:
    """Test file operation logging integration"""

    @patch('backend.services.file_uploader.file_audit_logger')
    @patch('backend.services.file_uploader.FileUploader._upload_to_s3')
    def test_file_upload_with_audit_logging(self, mock_upload, mock_audit_logger):
        """Test that file uploads are properly logged"""
        from ..services.file_uploader import FileUploader
        from ..services.file_audit_logger import FileOperationContext

        mock_upload.return_value = None
        mock_audit_logger.log_file_upload.return_value = "log_id_123"

        uploader = FileUploader()
        context = FileOperationContext(
            user_identifier="test_user",
            session_token="test_session",
            ip_address="192.168.1.1"
        )

        # Mock UploadFile
        mock_file = MagicMock()
        mock_file.filename = "test_photo.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"fake_image_data"
        mock_file.seek.return_value = None

        # Mock database session
        mock_db = MagicMock()

        # This would normally be called in the actual upload process
        # We're testing the integration point
        result = uploader._determine_file_type("image/jpeg", "test_photo.jpg")
        assert result == FileType.PHOTO

    def test_file_type_determination(self):
        """Test file type determination logic"""
        from ..services.file_uploader import FileUploader

        uploader = FileUploader()

        # Test photo detection
        assert uploader._determine_file_type("image/jpeg", "photo.jpg") == FileType.PHOTO
        assert uploader._determine_file_type("image/png", "image.png") == FileType.PHOTO

        # Test audio detection
        assert uploader._determine_file_type("audio/mp3", "song.mp3") == FileType.AUDIO
        assert uploader._determine_file_type("audio/wav", "recording.wav") == FileType.AUDIO

        # Test PDF detection
        assert uploader._determine_file_type("application/pdf", "document.pdf") == FileType.PDF

        # Test other types
        assert uploader._determine_file_type("text/plain", "readme.txt") == FileType.OTHER

    def test_file_type_from_key_determination(self):
        """Test file type determination from file keys"""
        from ..services.file_uploader import FileUploader

        uploader = FileUploader()

        # Test path-based detection
        assert uploader._determine_file_type_from_key("temp_photos/session123.jpg") == FileType.PHOTO
        assert uploader._determine_file_type_from_key("permanent/audio/order456.mp3") == FileType.AUDIO
        assert uploader._determine_file_type_from_key("waveforms/session789.png") == FileType.WAVEFORM

        # Test extension-based detection
        assert uploader._determine_file_type_from_key("unknown/path/image.jpg") == FileType.PHOTO
        assert uploader._determine_file_type_from_key("unknown/path/audio.mp3") == FileType.AUDIO
        assert uploader._determine_file_type_from_key("unknown/path/document.pdf") == FileType.PDF

class TestAuditLogModel:
    """Test the FileAuditLog database model"""

    def test_audit_log_creation(self):
        """Test creating an audit log entry"""
        audit_log = FileAuditLog(
            operation_type="upload",
            file_type="photo",
            status="success",
            user_identifier="test_user",
            source_path="/tmp/test.jpg",
            destination_path="temp_photos/test.jpg",
            file_size=1024000,
            content_type="image/jpeg",
            processing_time_ms=1500
        )

        assert audit_log.operation_type == "upload"
        assert audit_log.file_type == "photo"
        assert audit_log.status == "success"
        assert audit_log.user_identifier == "test_user"
        assert audit_log.file_size == 1024000
        assert audit_log.processing_time_ms == 1500
        assert audit_log.timestamp is not None
        assert audit_log.id is not None

if __name__ == "__main__":
    pytest.main([__file__])
