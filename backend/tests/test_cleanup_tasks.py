"""
Tests for cleanup task modifications
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from ..tasks import cleanup_expired_sessions, cleanup_orphaned_audio_files
from ..models import SessionModel, Order


class TestCleanupTasks:
    """Test cleanup task modifications"""
    
    @patch('backend.tasks.get_db')
    def test_cleanup_expired_sessions_database_only(self, mock_get_db):
        """Test that session cleanup only removes database records, not files"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock expired session
        expired_session = SessionModel(
            id="expired-session-id",
            session_token="expired-token",
            photo_s3_key="temp_photos/expired.jpg",
            audio_s3_key="temp_audio/expired.mp3",
            waveform_s3_key="waveforms/expired.png",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        # Mock query result
        mock_db.query.return_value.filter.return_value.all.return_value = [expired_session]
        
        # Mock order check (no paid order)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = cleanup_expired_sessions()
        
        # Verify session was deleted from database
        mock_db.delete.assert_called_once_with(expired_session)
        mock_db.commit.assert_called_once()
        
        # Verify result
        assert result["status"] == "completed"
        assert result["sessions_cleaned"] == 1
        assert "Only database records cleaned" in result["note"]
    
    @patch('backend.tasks.get_db')
    def test_cleanup_expired_sessions_keep_paid_orders(self, mock_get_db):
        """Test that sessions with paid orders are kept"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock expired session
        expired_session = SessionModel(
            id="expired-session-id",
            session_token="expired-token",
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        # Mock paid order exists
        paid_order = Order(
            id="paid-order-id",
            session_token="expired-token",
            status="completed"
        )
        
        # Mock query results
        mock_db.query.return_value.filter.return_value.all.return_value = [expired_session]
        mock_db.query.return_value.filter.return_value.first.return_value = paid_order
        
        result = cleanup_expired_sessions()
        
        # Verify session was NOT deleted
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_called_once()
        
        # Verify result
        assert result["status"] == "completed"
        assert result["sessions_cleaned"] == 0
    
    @patch('backend.tasks.get_db')
    @patch('backend.tasks.FileUploader')
    def test_cleanup_orphaned_audio_files_7_days_old(self, mock_file_uploader_class, mock_get_db):
        """Test that orphaned files older than 7 days are deleted"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock file uploader
        mock_file_uploader = MagicMock()
        mock_file_uploader_class.return_value = mock_file_uploader
        
        # Mock file listing
        mock_file_uploader.list_files_with_prefix.return_value = ["temp_audio/old_file.mp3"]
        
        # Mock file age (8 days old)
        old_date = datetime.utcnow() - timedelta(days=8)
        mock_file_uploader.get_file_creation_time.return_value = old_date
        
        # Mock no session or order references
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = cleanup_orphaned_audio_files()
        
        # Verify file was deleted
        mock_file_uploader.delete_file.assert_called_once_with("temp_audio/old_file.mp3")
        
        # Verify result
        assert result["status"] == "completed"
        assert result["orphaned_files_deleted"] == 1
        assert "Only temporary files older than 7 days are deleted" in result["note"]
    
    @patch('backend.tasks.get_db')
    @patch('backend.tasks.FileUploader')
    def test_cleanup_orphaned_audio_files_too_recent(self, mock_file_uploader_class, mock_get_db):
        """Test that files newer than 7 days are kept"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock file uploader
        mock_file_uploader = MagicMock()
        mock_file_uploader_class.return_value = mock_file_uploader
        
        # Mock file listing
        mock_file_uploader.list_files_with_prefix.return_value = ["temp_audio/recent_file.mp3"]
        
        # Mock file age (3 days old)
        recent_date = datetime.utcnow() - timedelta(days=3)
        mock_file_uploader.get_file_creation_time.return_value = recent_date
        
        # Mock no session or order references
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = cleanup_orphaned_audio_files()
        
        # Verify file was NOT deleted
        mock_file_uploader.delete_file.assert_not_called()
        
        # Verify result
        assert result["status"] == "completed"
        assert result["orphaned_files_deleted"] == 0
    
    @patch('backend.tasks.get_db')
    @patch('backend.tasks.FileUploader')
    def test_cleanup_orphaned_audio_files_has_session(self, mock_file_uploader_class, mock_get_db):
        """Test that files referenced by sessions are not deleted"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock file uploader
        mock_file_uploader = MagicMock()
        mock_file_uploader_class.return_value = mock_file_uploader
        
        # Mock file listing
        mock_file_uploader.list_files_with_prefix.return_value = ["temp_audio/active_file.mp3"]
        
        # Mock session exists
        active_session = SessionModel(
            id="active-session-id",
            audio_s3_key="temp_audio/active_file.mp3"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = active_session
        
        result = cleanup_orphaned_audio_files()
        
        # Verify file was NOT deleted
        mock_file_uploader.delete_file.assert_not_called()
        
        # Verify result
        assert result["status"] == "completed"
        assert result["orphaned_files_deleted"] == 0
    
    @patch('backend.tasks.get_db')
    @patch('backend.tasks.FileUploader')
    def test_cleanup_orphaned_audio_files_moved_to_permanent(self, mock_file_uploader_class, mock_get_db):
        """Test that files moved to permanent storage are not deleted"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock file uploader
        mock_file_uploader = MagicMock()
        mock_file_uploader_class.return_value = mock_file_uploader
        
        # Mock file listing
        mock_file_uploader.list_files_with_prefix.return_value = ["temp_audio/migrated_file.mp3"]
        
        # Mock no session but permanent order exists
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No session
            Order(id="order-id", permanent_audio_s3_key="permanent/audio/migrated_file.mp3")  # Has permanent order
        ]
        
        result = cleanup_orphaned_audio_files()
        
        # Verify file was NOT deleted
        mock_file_uploader.delete_file.assert_not_called()
        
        # Verify result
        assert result["status"] == "completed"
        assert result["orphaned_files_deleted"] == 0
