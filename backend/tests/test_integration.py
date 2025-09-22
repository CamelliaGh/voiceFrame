"""
Integration tests for the complete file migration system
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from ..main import app
from ..models import SessionModel
from .conftest import TestOrder as Order, TestSessionModel


class TestFileMigrationIntegration:
    """Integration tests for file migration system"""
    
    def test_complete_payment_flow_with_migration(self, client, sample_session, mock_s3_client, mock_stripe_service, mock_storage_manager):
        """Test complete payment flow with file migration"""
        # Create payment intent (this creates the order)
        payment_data = {
            "email": "test@example.com"
        }
        
        response = client.post(f"/api/session/{sample_session.session_token}/payment", json=payment_data)
        assert response.status_code == 200
        order_id = response.json()["order_id"]
        
        # Complete order with payment
        complete_data = {
            "payment_intent_id": "pi_test"
        }
        
        with patch('backend.main.pdf_generator.generate_final_pdf') as mock_generate_pdf:
            mock_generate_pdf.return_value = "https://example.com/test.pdf"
            
            response = client.post(f"/api/orders/{order_id}/complete", json=complete_data)
            
            # Should succeed
            assert response.status_code == 200
            
            # Verify file migration was called
            mock_storage_manager.migrate_all_session_files.assert_called_once()
            mock_storage_manager.verify_migration_success.assert_called_once()
    
    def test_migration_failure_handling(self, client, sample_session, mock_s3_client, mock_stripe_service):
        """Test handling of migration failures"""
        # Mock storage manager to fail
        with patch('backend.main.storage_manager') as mock_storage:
            mock_storage.migrate_all_session_files.side_effect = Exception("Migration failed")
            
            # Create payment intent (this creates the order)
            payment_data = {
                "email": "test@example.com"
            }
            
            response = client.post(f"/api/session/{sample_session.session_token}/payment", json=payment_data)
            order_id = response.json()["order_id"]
            
            # Complete order with payment
            complete_data = {
                "payment_intent_id": "pi_test"
            }
            
            response = client.post(f"/api/orders/{order_id}/complete", json=complete_data)
            
            # Should fail with migration error
            assert response.status_code == 500
            assert "File migration failed" in response.json()["detail"]
    
    def test_session_update_validation(self, client, sample_session):
        """Test session update validation with various data combinations"""
        # Test valid update
        valid_data = {
            "custom_text": "Updated text",
            "photo_shape": "circle",
            "pdf_size": "A4_Landscape",
            "template_id": "framed_a4_landscape",
            "background_id": "abstract-blurred"
        }
        
        response = client.put(f"/api/session/{sample_session.session_token}", json=valid_data)
        assert response.status_code == 200
        
        # Test with None values
        none_data = {
            "custom_text": "Test text",
            "photo_shape": None,
            "pdf_size": "A4",
            "template_id": "framed_a4_portrait",
            "background_id": None
        }
        
        response = client.put(f"/api/session/{sample_session.session_token}", json=none_data)
        assert response.status_code == 200
        
        # Test invalid data
        invalid_data = {
            "photo_shape": "invalid",
            "pdf_size": "invalid",
            "template_id": "invalid",
            "background_id": "invalid"
        }
        
        response = client.put(f"/api/session/{sample_session.session_token}", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_qr_code_expiration_differences(self, client, sample_session, sample_order, mock_s3_client):
        """Test that QR codes have different expiration times for paid vs unpaid"""
        with patch('backend.services.pdf_generator.FileUploader') as mock_file_uploader_class:
            mock_file_uploader_instance = mock_file_uploader_class.return_value
            mock_file_uploader_instance.file_exists.return_value = True
            mock_file_uploader_instance.generate_presigned_url.return_value = "https://example.com/audio.mp3"
            
            from ..services.pdf_generator import PDFGenerator
            pdf_generator = PDFGenerator()
            # Replace the file_uploader with our mock
            pdf_generator.file_uploader = mock_file_uploader_instance
            
            # Test preview version (7 days)
            qr_url = pdf_generator._generate_qr_url(sample_session, None)
            call_args = mock_file_uploader_instance.generate_presigned_url.call_args
            assert call_args[1]['expiration'] == 86400 * 7  # 7 days
            
            # Test paid version (5 years)
            qr_url = pdf_generator._generate_qr_url(None, sample_order)
            call_args = mock_file_uploader_instance.generate_presigned_url.call_args
            assert call_args[1]['expiration'] == 86400 * 365 * 5  # 5 years
    
    def test_cleanup_tasks_manual_only(self, client, sample_session):
        """Test that cleanup tasks are manual only and don't run automatically"""
        # This test verifies that the cleanup tasks are commented out in the beat schedule
        # and can only be run manually
        
        # Check that the beat schedule is disabled
        from ..tasks import celery_app
        assert not hasattr(celery_app.conf, 'beat_schedule') or not celery_app.conf.beat_schedule
        
        # Test manual cleanup task execution
        with patch('backend.tasks.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.all.return_value = []
            
            from ..tasks import cleanup_expired_sessions
            result = cleanup_expired_sessions()
            
            assert result["status"] == "completed"
            assert "Only database records cleaned" in result["note"]


class TestDatabaseSchemaUpdates:
    """Test database schema updates for file migration"""
    
    def test_order_model_has_migration_fields(self, db_session):
        """Test that Order model has all required migration fields"""
        import uuid
        order = Order(
            id=str(uuid.uuid4()),
            email="test@example.com",
            amount_cents=999,
            permanent_photo_s3_key="permanent/photos/test.jpg",
            permanent_audio_s3_key="permanent/audio/test.mp3",
            permanent_waveform_s3_key="permanent/waveforms/test.png",
            permanent_pdf_s3_key="permanent/pdfs/test.pdf",
            migration_status="completed",
            migration_completed_at=datetime.utcnow(),
            migration_error=None
        )
        
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        # Verify all fields exist and can be set
        assert order.permanent_photo_s3_key == "permanent/photos/test.jpg"
        assert order.permanent_audio_s3_key == "permanent/audio/test.mp3"
        assert order.permanent_waveform_s3_key == "permanent/waveforms/test.png"
        assert order.permanent_pdf_s3_key == "permanent/pdfs/test.pdf"
        assert order.migration_status == "completed"
        assert order.migration_completed_at is not None
        assert order.migration_error is None
    
    def test_session_model_unchanged(self, db_session):
        """Test that SessionModel remains unchanged"""
        import uuid
        session = TestSessionModel(
            id=str(uuid.uuid4()),
            session_token="test-token",
            photo_s3_key="temp_photos/test.jpg",
            audio_s3_key="temp_audio/test.mp3",
            waveform_s3_key="waveforms/test.png",
            custom_text="Test text",
            photo_shape="square",
            pdf_size="A4",
            template_id="framed_a4_portrait",
            background_id="none"
        )
        
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Verify all original fields still work
        assert session.photo_s3_key == "temp_photos/test.jpg"
        assert session.audio_s3_key == "temp_audio/test.mp3"
        assert session.waveform_s3_key == "waveforms/test.png"
        assert session.custom_text == "Test text"
        assert session.photo_shape == "square"
        assert session.pdf_size == "A4"
        assert session.template_id == "framed_a4_portrait"
        assert session.background_id == "none"
