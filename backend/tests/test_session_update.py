"""
Tests for session update functionality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from ..main import app
from ..models import SessionModel
from ..schemas import SessionUpdate
from ..database import get_db


class TestSessionUpdate:
    """Test session update validation and processing"""
    
    def test_session_update_schema_validation(self):
        """Test that SessionUpdate schema properly validates all fields"""
        # Valid data
        valid_data = {
            "custom_text": "Test text",
            "photo_shape": "square",
            "pdf_size": "A4",
            "template_id": "framed_a4_portrait",
            "background_id": "none"
        }
        
        session_update = SessionUpdate(**valid_data)
        assert session_update.custom_text == "Test text"
        assert session_update.photo_shape == "square"
        assert session_update.pdf_size == "A4"
        assert session_update.template_id == "framed_a4_portrait"
        assert session_update.background_id == "none"
    
    def test_session_update_with_none_values(self):
        """Test that SessionUpdate handles None values correctly"""
        # Data with None values (as sent by frontend)
        data_with_none = {
            "custom_text": "Test text",
            "photo_shape": None,
            "pdf_size": "A4",
            "template_id": "framed_a4_portrait",
            "background_id": None
        }
        
        session_update = SessionUpdate(**data_with_none)
        assert session_update.custom_text == "Test text"
        assert session_update.photo_shape is None
        assert session_update.pdf_size == "A4"
        assert session_update.template_id == "framed_a4_portrait"
        assert session_update.background_id is None
    
    def test_session_update_validation_errors(self):
        """Test that validation errors are raised for invalid data"""
        # Invalid photo_shape
        with pytest.raises(ValueError, match="Photo shape must be either"):
            SessionUpdate(photo_shape="invalid")
        
        # Invalid pdf_size
        with pytest.raises(ValueError, match="Invalid PDF size"):
            SessionUpdate(pdf_size="invalid")
        
        # Invalid template_id
        with pytest.raises(ValueError, match="Invalid template"):
            SessionUpdate(template_id="invalid")
        
        # Invalid background_id
        with pytest.raises(ValueError, match="Invalid background"):
            SessionUpdate(background_id="invalid")
        
        # Text too long
        with pytest.raises(ValueError, match="Custom text too long"):
            SessionUpdate(custom_text="x" * 201)
        
        # Text only whitespace
        with pytest.raises(ValueError, match="Custom text cannot be only whitespace"):
            SessionUpdate(custom_text="   ")
    
    def test_session_update_text_validation(self):
        """Test custom text validation and trimming"""
        # Test trimming
        session_update = SessionUpdate(custom_text="  Test text  ")
        assert session_update.custom_text == "Test text"
        
        # Test empty string (should be allowed)
        session_update = SessionUpdate(custom_text="")
        assert session_update.custom_text == ""
        
        # Test None (should be allowed)
        session_update = SessionUpdate(custom_text=None)
        assert session_update.custom_text is None


class TestSessionUpdateAPI:
    """Test session update API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing"""
        session = SessionModel(
            id="test-session-id",
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
        return session
    
    @patch('backend.main.session_manager.get_session')
    @patch('backend.main.session_manager.update_session')
    def test_update_session_success(self, mock_update, mock_get_session, client, mock_session):
        """Test successful session update"""
        mock_get_session.return_value = mock_session
        mock_update.return_value = mock_session
        
        response = client.put(
            "/api/session/test-token",
            json={
                "custom_text": "Updated text",
                "photo_shape": "circle",
                "pdf_size": "A4_Landscape",
                "template_id": "framed_a4_landscape",
                "background_id": "abstract-blurred"
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"status": "updated"}
        mock_update.assert_called_once()
    
    @patch('backend.main.session_manager.get_session')
    def test_update_session_not_found(self, mock_get_session, client):
        """Test session update when session not found"""
        mock_get_session.return_value = None
        
        response = client.put(
            "/api/session/invalid-token",
            json={"custom_text": "Test text"}
        )
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('backend.main.session_manager.get_session')
    def test_update_session_missing_photo(self, mock_get_session, client, mock_session):
        """Test session update when photo is missing"""
        mock_session.photo_s3_key = None
        mock_get_session.return_value = mock_session
        
        response = client.put(
            "/api/session/test-token",
            json={"custom_text": "Test text"}
        )
        
        assert response.status_code == 400
        assert "Photo must be uploaded" in response.json()["detail"]
    
    @patch('backend.main.session_manager.get_session')
    def test_update_session_missing_audio(self, mock_get_session, client, mock_session):
        """Test session update when audio is missing"""
        mock_session.audio_s3_key = None
        mock_get_session.return_value = mock_session
        
        response = client.put(
            "/api/session/test-token",
            json={"custom_text": "Test text"}
        )
        
        assert response.status_code == 400
        assert "Audio file must be uploaded" in response.json()["detail"]
    
    @patch('backend.main.session_manager.get_session')
    def test_update_session_waveform_processing(self, mock_get_session, client, mock_session):
        """Test session update when waveform is still processing"""
        mock_session.waveform_s3_key = None
        mock_get_session.return_value = mock_session
        
        response = client.put(
            "/api/session/test-token",
            json={"custom_text": "Test text"}
        )
        
        assert response.status_code == 400
        assert "Audio processing not complete" in response.json()["detail"]
    
    def test_update_session_invalid_data(self, client):
        """Test session update with invalid data"""
        response = client.put(
            "/api/session/test-token",
            json={
                "photo_shape": "invalid",
                "pdf_size": "invalid",
                "template_id": "invalid",
                "background_id": "invalid"
            }
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422
