"""
Tests for QR code URL generation

Tests verify that QR codes use permanent /listen/ endpoint URLs
instead of expiring presigned S3 URLs. This ensures QR codes work
for years as long as the backend is running.
"""
from unittest.mock import MagicMock, patch

import pytest

from ..models import Order, SessionModel
from ..services.pdf_generator import PDFGenerator
from ..services.visual_pdf_generator import VisualPDFGenerator
from ..config import settings


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
        import uuid

        return SessionModel(
            id=str(uuid.uuid4()),
            session_token="test-session-token",
            audio_s3_key="temp_audio/test.mp3",
            custom_text="Test text",
        )

    @pytest.fixture
    def mock_paid_order(self):
        import uuid

        return Order(
            id=str(uuid.uuid4()),
            email="test@example.com",
            amount_cents=999,
            status="completed",
            permanent_audio_s3_key="permanent/audio/test.mp3",
        )

    @patch("backend.services.pdf_generator.FileUploader")
    def test_qr_url_paid_version_uses_listen_endpoint(
        self, mock_file_uploader_class, pdf_generator, mock_paid_order
    ):
        """Test QR URL for paid version uses permanent /listen/ endpoint"""
        # Mock the FileUploader class and its instance
        mock_file_uploader_instance = mock_file_uploader_class.return_value
        mock_file_uploader_instance.file_exists.return_value = True

        # Replace the pdf_generator's file_uploader with our mock
        pdf_generator.file_uploader = mock_file_uploader_instance

        qr_url = pdf_generator._generate_qr_url(None, mock_paid_order)

        # Verify it uses /listen/ endpoint with order ID
        assert qr_url == f"{settings.base_url}/listen/{mock_paid_order.id}"

        # Verify file existence was checked
        mock_file_uploader_instance.file_exists.assert_called_once_with("permanent/audio/test.mp3")

        # Verify no presigned URL was generated (we use /listen/ endpoint now)
        mock_file_uploader_instance.generate_presigned_url.assert_not_called()

    @patch("backend.services.pdf_generator.FileUploader")
    def test_qr_url_preview_version_uses_listen_endpoint(
        self, mock_file_uploader_class, pdf_generator, mock_session
    ):
        """Test QR URL for preview version uses /listen/ endpoint with session token"""
        # Mock the FileUploader class and its instance
        mock_file_uploader_instance = mock_file_uploader_class.return_value
        mock_file_uploader_instance.file_exists.return_value = True

        # Replace the pdf_generator's file_uploader with our mock
        pdf_generator.file_uploader = mock_file_uploader_instance

        qr_url = pdf_generator._generate_qr_url(mock_session, None)

        # Verify it uses /listen/ endpoint with session token
        assert qr_url == f"{settings.base_url}/listen/{mock_session.session_token}"

        # Verify file existence was checked
        mock_file_uploader_instance.file_exists.assert_called_once_with("temp_audio/test.mp3")

        # Verify no presigned URL was generated (we use /listen/ endpoint now)
        mock_file_uploader_instance.generate_presigned_url.assert_not_called()

    @patch("backend.services.pdf_generator.FileUploader")
    def test_qr_url_missing_file_error(
        self, mock_file_uploader_class, pdf_generator, mock_paid_order
    ):
        """Test QR URL generation raises error when file is missing"""
        # Mock the FileUploader class and its instance
        mock_file_uploader_instance = mock_file_uploader_class.return_value
        mock_file_uploader_instance.file_exists.return_value = False

        # Replace the pdf_generator's file_uploader with our mock
        pdf_generator.file_uploader = mock_file_uploader_instance

        with pytest.raises(Exception, match="Permanent audio file missing"):
            pdf_generator._generate_qr_url(None, mock_paid_order)

    def test_qr_url_no_audio_error(self, pdf_generator):
        """Test QR URL generation raises error when no audio is available"""
        with pytest.raises(Exception, match="No audio file available"):
            pdf_generator._generate_qr_url(None, None)

    @patch("backend.services.visual_pdf_generator.FileUploader")
    def test_visual_qr_url_paid_version_uses_listen_endpoint(
        self, mock_file_uploader_class, visual_generator, mock_paid_order
    ):
        """Test visual QR URL for paid version uses permanent /listen/ endpoint"""
        # Mock the FileUploader class and its instance
        mock_file_uploader_instance = mock_file_uploader_class.return_value
        mock_file_uploader_instance.file_exists.return_value = True

        # Replace the visual_generator's file_uploader with our mock
        visual_generator.file_uploader = mock_file_uploader_instance

        qr_url = visual_generator._generate_qr_url(None, mock_paid_order)

        # Verify it uses /listen/ endpoint with order ID
        assert qr_url == f"{settings.base_url}/listen/{mock_paid_order.id}"

        # Verify file existence was checked
        mock_file_uploader_instance.file_exists.assert_called_once_with("permanent/audio/test.mp3")

        # Verify no presigned URL was generated (we use /listen/ endpoint now)
        mock_file_uploader_instance.generate_presigned_url.assert_not_called()

    @patch("backend.services.visual_pdf_generator.FileUploader")
    def test_visual_qr_url_preview_version_uses_listen_endpoint(
        self, mock_file_uploader_class, visual_generator, mock_session
    ):
        """Test visual QR URL for preview version uses /listen/ endpoint with session token"""
        # Mock the FileUploader class and its instance
        mock_file_uploader_instance = mock_file_uploader_class.return_value
        mock_file_uploader_instance.file_exists.return_value = True

        # Replace the visual_generator's file_uploader with our mock
        visual_generator.file_uploader = mock_file_uploader_instance

        qr_url = visual_generator._generate_qr_url(mock_session, None)

        # Verify it uses /listen/ endpoint with session token
        assert qr_url == f"{settings.base_url}/listen/{mock_session.session_token}"

        # Verify file existence was checked
        mock_file_uploader_instance.file_exists.assert_called_once_with("temp_audio/test.mp3")

        # Verify no presigned URL was generated (we use /listen/ endpoint now)
        mock_file_uploader_instance.generate_presigned_url.assert_not_called()
