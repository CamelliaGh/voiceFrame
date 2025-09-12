"""
Tests for file migration system
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import os

from ..services.storage_manager import StorageManager
from ..models import SessionModel, Order
from ..schemas import SessionUpdate


class TestStorageManagerMigration:
    """Test file migration functionality"""
    
    @pytest.fixture
    def storage_manager(self):
        return StorageManager()
    
    @pytest.fixture
    def mock_session(self):
        return SessionModel(
            id="test-session-id",
            session_token="test-session-token",
            photo_s3_key="temp_photos/test.jpg",
            audio_s3_key="temp_audio/test.mp3",
            waveform_s3_key="waveforms/test.png",
            custom_text="Test text",
            photo_shape="square",
            pdf_size="A4",
            template_id="framed_a4_portrait",
            background_id="none"
        )
    
    @pytest.fixture
    def mock_order(self):
        return Order(
            id="test-order-id",
            email="test@example.com",
            amount_cents=999,
            status="pending",
            session_token="test-session-token"
        )
    
    @patch('backend.services.storage_manager.os.path.exists')
    @patch('backend.services.storage_manager.os.listdir')
    @patch('backend.services.storage_manager.os.remove')
    @patch.object(StorageManager, '_upload_to_s3_permanent')
    @patch.object(StorageManager, '_copy_s3_file')
    @patch.object(StorageManager, 'file_uploader')
    async def test_migrate_all_session_files_success(
        self, mock_file_uploader, mock_copy_s3, mock_upload_s3, 
        mock_remove, mock_listdir, mock_exists, storage_manager, 
        mock_session, mock_order
    ):
        """Test successful migration of all session files"""
        # Mock file existence
        mock_exists.return_value = True
        mock_listdir.return_value = ["test-session-token.mp3"]
        mock_file_uploader.file_exists.return_value = True
        
        # Mock async methods
        mock_upload_s3.return_value = None
        mock_copy_s3.return_value = None
        
        result = await storage_manager.migrate_all_session_files(
            mock_session.session_token, 
            str(mock_order.id)
        )
        
        # Verify migration results
        assert "permanent_photo_s3_key" in result
        assert "permanent_audio_s3_key" in result
        assert "permanent_waveform_s3_key" in result
        
        # Verify file paths
        assert result["permanent_photo_s3_key"] == f"permanent/photos/{mock_order.id}.jpg"
        assert result["permanent_audio_s3_key"] == f"permanent/audio/{mock_order.id}.mp3"
        assert result["permanent_waveform_s3_key"] == f"permanent/waveforms/{mock_order.id}.png"
        
        # Verify cleanup was called
        assert mock_remove.call_count >= 2  # Photo and audio cleanup
    
    @patch('backend.services.storage_manager.os.path.exists')
    @patch('backend.services.storage_manager.os.listdir')
    @patch('backend.services.storage_manager.os.remove')
    @patch.object(StorageManager, '_upload_to_s3_permanent')
    @patch.object(StorageManager, 'file_uploader')
    async def test_migrate_all_session_files_no_files(
        self, mock_file_uploader, mock_upload_s3, 
        mock_remove, mock_listdir, mock_exists, storage_manager, 
        mock_session, mock_order
    ):
        """Test migration when no files exist"""
        # Mock no files exist
        mock_exists.return_value = False
        mock_listdir.return_value = []
        mock_file_uploader.file_exists.return_value = False
        
        result = await storage_manager.migrate_all_session_files(
            mock_session.session_token, 
            str(mock_order.id)
        )
        
        # Should return empty dict when no files to migrate
        assert result == {}
    
    @patch('backend.services.storage_manager.os.path.exists')
    @patch('backend.services.storage_manager.os.listdir')
    @patch('backend.services.storage_manager.os.remove')
    @patch.object(StorageManager, '_upload_to_s3_permanent')
    @patch.object(StorageManager, 'file_uploader')
    async def test_migrate_all_session_files_error(
        self, mock_file_uploader, mock_upload_s3, 
        mock_remove, mock_listdir, mock_exists, storage_manager, 
        mock_session, mock_order
    ):
        """Test migration error handling"""
        # Mock file existence
        mock_exists.return_value = True
        mock_listdir.return_value = ["test-session-token.mp3"]
        mock_file_uploader.file_exists.return_value = True
        
        # Mock upload error
        mock_upload_s3.side_effect = Exception("Upload failed")
        
        with pytest.raises(Exception, match="Migration to permanent storage failed"):
            await storage_manager.migrate_all_session_files(
                mock_session.session_token, 
                str(mock_order.id)
            )
    
    def test_verify_migration_success(self, storage_manager):
        """Test migration verification"""
        mock_file_uploader = MagicMock()
        storage_manager.file_uploader = mock_file_uploader
        
        # Test successful verification
        mock_file_uploader.file_exists.return_value = True
        permanent_keys = ["key1", "key2", "key3"]
        
        result = storage_manager.verify_migration_success(permanent_keys)
        assert result is True
        assert mock_file_uploader.file_exists.call_count == 3
        
        # Test failed verification
        mock_file_uploader.file_exists.return_value = False
        result = storage_manager.verify_migration_success(permanent_keys)
        assert result is False
    
    def test_verify_migration_success_with_none_keys(self, storage_manager):
        """Test migration verification with None keys"""
        mock_file_uploader = MagicMock()
        storage_manager.file_uploader = mock_file_uploader
        
        permanent_keys = ["key1", None, "key3"]
        
        result = storage_manager.verify_migration_success(permanent_keys)
        assert result is True
        # Should only check non-None keys
        assert mock_file_uploader.file_exists.call_count == 2
    
    @patch.object(StorageManager, 'file_uploader')
    async def test_rollback_migration(self, mock_file_uploader, storage_manager):
        """Test migration rollback"""
        mock_file_uploader.file_exists.return_value = True
        mock_file_uploader.delete_file.return_value = None
        
        permanent_keys = ["key1", "key2", "key3"]
        
        result = await storage_manager.rollback_migration(permanent_keys)
        assert result is True
        assert mock_file_uploader.delete_file.call_count == 3
    
    def test_get_audio_content_type(self, storage_manager):
        """Test audio content type detection"""
        assert storage_manager._get_audio_content_type("mp3") == "audio/mpeg"
        assert storage_manager._get_audio_content_type("wav") == "audio/wav"
        assert storage_manager._get_audio_content_type("m4a") == "audio/mp4"
        assert storage_manager._get_audio_content_type("aac") == "audio/aac"
        assert storage_manager._get_audio_content_type("ogg") == "audio/ogg"
        assert storage_manager._get_audio_content_type("flac") == "audio/flac"
        assert storage_manager._get_audio_content_type("unknown") == "audio/mpeg"  # default


class TestFileMigrationIntegration:
    """Test file migration integration with payment flow"""
    
    @pytest.fixture
    def client(self):
        from ..main import app
        return TestClient(app)
    
    @patch('backend.main.storage_manager.migrate_all_session_files')
    @patch('backend.main.storage_manager.verify_migration_success')
    @patch('backend.main.session_manager.get_session_by_order')
    @patch('backend.main.stripe_service.verify_payment')
    @patch('backend.main.session_manager.get_session')
    def test_complete_order_with_migration_success(
        self, mock_get_session, mock_verify_payment, 
        mock_get_session_by_order, mock_verify_migration, 
        mock_migrate_files, client
    ):
        """Test successful order completion with file migration"""
        # Mock session
        mock_session = MagicMock()
        mock_session.photo_s3_key = "temp_photos/test.jpg"
        mock_session.audio_s3_key = "temp_audio/test.mp3"
        mock_session.waveform_s3_key = "waveforms/test.png"
        mock_get_session.return_value = mock_session
        mock_get_session_by_order.return_value = mock_session
        
        # Mock payment verification
        mock_verify_payment.return_value = {"status": "succeeded"}
        
        # Mock file migration
        mock_migrate_files.return_value = {
            "permanent_photo_s3_key": "permanent/photos/test.jpg",
            "permanent_audio_s3_key": "permanent/audio/test.mp3",
            "permanent_waveform_s3_key": "permanent/waveforms/test.png"
        }
        mock_verify_migration.return_value = True
        
        # Mock PDF generation
        with patch('backend.main.pdf_generator.generate_final_pdf') as mock_generate_pdf:
            mock_generate_pdf.return_value = "https://example.com/test.pdf"
            
            response = client.post(
                "/api/orders/test-order-id/complete",
                json={"payment_intent_id": "pi_test"}
            )
            
            assert response.status_code == 200
            mock_migrate_files.assert_called_once()
            mock_verify_migration.assert_called_once()
    
    @patch('backend.main.storage_manager.migrate_all_session_files')
    @patch('backend.main.session_manager.get_session_by_order')
    @patch('backend.main.stripe_service.verify_payment')
    @patch('backend.main.session_manager.get_session')
    def test_complete_order_with_migration_failure(
        self, mock_get_session, mock_verify_payment, 
        mock_get_session_by_order, mock_migrate_files, client
    ):
        """Test order completion with file migration failure"""
        # Mock session
        mock_session = MagicMock()
        mock_session.photo_s3_key = "temp_photos/test.jpg"
        mock_session.audio_s3_key = "temp_audio/test.mp3"
        mock_session.waveform_s3_key = "waveforms/test.png"
        mock_get_session.return_value = mock_session
        mock_get_session_by_order.return_value = mock_session
        
        # Mock payment verification
        mock_verify_payment.return_value = {"status": "succeeded"}
        
        # Mock file migration failure
        mock_migrate_files.side_effect = Exception("Migration failed")
        
        response = client.post(
            "/api/orders/test-order-id/complete",
            json={"payment_intent_id": "pi_test"}
        )
        
        assert response.status_code == 500
        assert "File migration failed" in response.json()["detail"]
