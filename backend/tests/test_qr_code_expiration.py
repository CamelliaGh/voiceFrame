"""
Tests for QR code expiration updates
"""
import pytest
from unittest.mock import patch, MagicMock

from ..services.pdf_generator import PDFGenerator
from ..services.visual_pdf_generator import VisualPDFGenerator
from ..models import SessionModel, Order


class TestQRCodeExpiration:
    """Test QR code expiration for paid vs unpaid versions"""
    
    @pytest.fixture
    def pdf_generator(self):
        return PDFGenerator()
    
    @pytest.fixture
    def visual_generator(self):
        return VisualPDFGenerator()
    
    @pytest.fixture
    def mock_session(self):
        return SessionModel(
            id="test-session-id",
            session_token="test-session-token",
            audio_s3_key="temp_audio/test.mp3",
            custom_text="Test text"
        )
    
    @pytest.fixture
    def mock_paid_order(self):
        return Order(
            id="test-order-id",
            email="test@example.com",
            amount_cents=999,
            status="completed",
            permanent_audio_s3_key="permanent/audio/test.mp3"
        )
    
    @patch.object(PDFGenerator, 'file_uploader')
    def test_qr_url_paid_version_5_years(self, mock_file_uploader, pdf_generator, mock_paid_order):
        """Test QR URL for paid version has 5-year expiration"""
        mock_file_uploader.file_exists.return_value = True
        mock_file_uploader.generate_presigned_url.return_value = "https://example.com/audio.mp3"
        
        qr_url = pdf_generator._generate_qr_url(None, mock_paid_order)
        
        # Verify presigned URL was generated
        mock_file_uploader.generate_presigned_url.assert_called_once()
        call_args = mock_file_uploader.generate_presigned_url.call_args
        
        # Check expiration is 5 years (86400 * 365 * 5 seconds)
        assert call_args[1]['expiration'] == 86400 * 365 * 5
        assert call_args[0][0] == "permanent/audio/test.mp3"
    
    @patch.object(PDFGenerator, 'file_uploader')
    def test_qr_url_preview_version_7_days(self, mock_file_uploader, pdf_generator, mock_session):
        """Test QR URL for preview version has 7-day expiration"""
        mock_file_uploader.file_exists.return_value = True
        mock_file_uploader.generate_presigned_url.return_value = "https://example.com/audio.mp3"
        
        qr_url = pdf_generator._generate_qr_url(mock_session, None)
        
        # Verify presigned URL was generated
        mock_file_uploader.generate_presigned_url.assert_called_once()
        call_args = mock_file_uploader.generate_presigned_url.call_args
        
        # Check expiration is 7 days (86400 * 7 seconds)
        assert call_args[1]['expiration'] == 86400 * 7
        assert call_args[0][0] == "temp_audio/test.mp3"
    
    @patch.object(PDFGenerator, 'file_uploader')
    def test_qr_url_missing_file_error(self, mock_file_uploader, pdf_generator, mock_paid_order):
        """Test QR URL generation raises error when file is missing"""
        mock_file_uploader.file_exists.return_value = False
        
        with pytest.raises(Exception, match="Permanent audio file missing"):
            pdf_generator._generate_qr_url(None, mock_paid_order)
    
    @patch.object(PDFGenerator, 'file_uploader')
    def test_qr_url_no_audio_error(self, mock_file_uploader, pdf_generator):
        """Test QR URL generation raises error when no audio is available"""
        with pytest.raises(Exception, match="No audio file available"):
            pdf_generator._generate_qr_url(None, None)
    
    @patch.object(VisualPDFGenerator, 'file_uploader')
    def test_visual_qr_url_paid_version_5_years(self, mock_file_uploader, visual_generator, mock_paid_order):
        """Test visual QR URL for paid version has 5-year expiration"""
        mock_file_uploader.file_exists.return_value = True
        mock_file_uploader.generate_presigned_url.return_value = "https://example.com/audio.mp3"
        
        qr_url = visual_generator._generate_qr_url(None, mock_paid_order)
        
        # Verify presigned URL was generated
        mock_file_uploader.generate_presigned_url.assert_called_once()
        call_args = mock_file_uploader.generate_presigned_url.call_args
        
        # Check expiration is 5 years (86400 * 365 * 5 seconds)
        assert call_args[1]['expiration'] == 86400 * 365 * 5
        assert call_args[0][0] == "permanent/audio/test.mp3"
    
    @patch.object(VisualPDFGenerator, 'file_uploader')
    def test_visual_qr_url_preview_version_7_days(self, mock_file_uploader, visual_generator, mock_session):
        """Test visual QR URL for preview version has 7-day expiration"""
        mock_file_uploader.file_exists.return_value = True
        mock_file_uploader.generate_presigned_url.return_value = "https://example.com/audio.mp3"
        
        qr_url = visual_generator._generate_qr_url(mock_session, None)
        
        # Verify presigned URL was generated
        mock_file_uploader.generate_presigned_url.assert_called_once()
        call_args = mock_file_uploader.generate_presigned_url.call_args
        
        # Check expiration is 7 days (86400 * 7 seconds)
        assert call_args[1]['expiration'] == 86400 * 7
        assert call_args[0][0] == "temp_audio/test.mp3"
