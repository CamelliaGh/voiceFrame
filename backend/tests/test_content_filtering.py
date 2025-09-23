"""
Tests for Content Filtering Service

Tests the content filtering functionality including file type detection,
virus scanning, and suspicious file pattern detection.
"""

import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from fastapi import UploadFile

from ..services.content_filter import ContentFilter


class TestContentFilter:
    """Test cases for ContentFilter service"""

    @pytest.fixture
    def content_filter(self):
        """Create a content filter instance for testing"""
        return ContentFilter()

    @pytest.fixture
    def mock_image_file(self):
        """Create a mock image file for testing"""
        file_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
        file = MagicMock(spec=UploadFile)
        file.filename = "test_image.jpg"
        file.content_type = "image/jpeg"
        file.size = len(file_content)
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock()
        return file

    @pytest.fixture
    def mock_audio_file(self):
        """Create a mock audio file for testing"""
        file_content = b'ID3\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        file = MagicMock(spec=UploadFile)
        file.filename = "test_audio.mp3"
        file.content_type = "audio/mpeg"
        file.size = len(file_content)
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock()
        return file

    @pytest.fixture
    def mock_suspicious_file(self):
        """Create a mock suspicious file for testing"""
        file_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
        file = MagicMock(spec=UploadFile)
        file.filename = "malware.exe"
        file.content_type = "application/octet-stream"
        file.size = len(file_content)
        file.read = AsyncMock(return_value=file_content)
        file.seek = AsyncMock()
        return file

    def test_get_file_extension(self, content_filter):
        """Test file extension extraction"""
        assert content_filter._get_file_extension("test.jpg") == ".jpg"
        assert content_filter._get_file_extension("test.MP3") == ".mp3"
        assert content_filter._get_file_extension("test") == ""
        assert content_filter._get_file_extension("") == ""

    def test_is_suspicious_pattern_valid(self, content_filter):
        """Test suspicious pattern detection for valid files"""
        assert content_filter._is_suspicious_pattern("test.jpg") is False
        assert content_filter._is_suspicious_pattern("test.mp3") is False
        assert content_filter._is_suspicious_pattern("test.png") is False
        assert content_filter._is_suspicious_pattern("") is True

    def test_is_suspicious_pattern_suspicious(self, content_filter):
        """Test suspicious pattern detection for suspicious files"""
        assert content_filter._is_suspicious_pattern("malware.exe") is True
        assert content_filter._is_suspicious_pattern("script.bat") is True
        assert content_filter._is_suspicious_pattern("virus.cmd") is True
        assert content_filter._is_suspicious_pattern("trojan.scr") is True

    @patch('magic.from_buffer')
    def test_detect_true_file_type(self, mock_magic, content_filter):
        """Test true file type detection"""
        mock_magic.side_effect = [
            "image/jpeg",  # mime_type
            "JPEG image data"  # file_description
        ]

        file_content = b'\xff\xd8\xff\xe0'
        mime_type, description = content_filter._detect_true_file_type(file_content)

        assert mime_type == "image/jpeg"
        assert description == "JPEG image data"
        mock_magic.assert_called()

    @patch('magic.from_buffer')
    def test_detect_true_file_type_error(self, mock_magic, content_filter):
        """Test true file type detection with error"""
        mock_magic.side_effect = Exception("Magic error")

        file_content = b'invalid'
        mime_type, description = content_filter._detect_true_file_type(file_content)

        assert mime_type == "application/octet-stream"
        assert description == "Unknown file type"

    @patch('magic.from_buffer')
    def test_validate_image_file_valid(self, mock_magic, content_filter):
        """Test image file validation for valid images"""
        mock_magic.side_effect = ["image/jpeg", "JPEG image data"]

        file_content = b'\xff\xd8\xff\xe0'
        is_valid = content_filter._validate_image_file(file_content, "image/jpeg")

        assert is_valid is True

    @patch('magic.from_buffer')
    def test_validate_image_file_invalid_mime(self, mock_magic, content_filter):
        """Test image file validation for invalid MIME type"""
        mock_magic.side_effect = ["text/plain", "ASCII text"]

        file_content = b'not an image'
        is_valid = content_filter._validate_image_file(file_content, "image/jpeg")

        assert is_valid is False

    @patch('magic.from_buffer')
    def test_validate_image_file_unsupported_type(self, mock_magic, content_filter):
        """Test image file validation for unsupported image type"""
        mock_magic.side_effect = ["image/svg+xml", "SVG image"]

        file_content = b'<svg></svg>'
        is_valid = content_filter._validate_image_file(file_content, "image/svg+xml")

        assert is_valid is False

    @patch('magic.from_buffer')
    def test_validate_audio_file_valid(self, mock_magic, content_filter):
        """Test audio file validation for valid audio"""
        mock_magic.side_effect = ["audio/mpeg", "MP3 audio"]

        file_content = b'ID3\x03\x00'
        is_valid = content_filter._validate_audio_file(file_content, "audio/mpeg")

        assert is_valid is True

    @patch('magic.from_buffer')
    def test_validate_audio_file_invalid_mime(self, mock_magic, content_filter):
        """Test audio file validation for invalid MIME type"""
        mock_magic.side_effect = ["text/plain", "ASCII text"]

        file_content = b'not audio'
        is_valid = content_filter._validate_audio_file(file_content, "audio/mpeg")

        assert is_valid is False

    @patch('magic.from_buffer')
    def test_validate_audio_file_unsupported_type(self, mock_magic, content_filter):
        """Test audio file validation for unsupported audio type"""
        mock_magic.side_effect = ["audio/midi", "MIDI audio"]

        file_content = b'MThd\x00\x00\x00\x06'
        is_valid = content_filter._validate_audio_file(file_content, "audio/midi")

        assert is_valid is False

    def test_validate_file_size_valid(self, content_filter):
        """Test file size validation for valid sizes"""
        assert content_filter._validate_file_size(1024, "image") is True
        assert content_filter._validate_file_size(1024 * 1024, "audio") is True

    def test_validate_file_size_too_large(self, content_filter):
        """Test file size validation for oversized files"""
        # Assuming max_photo_size is 50MB and max_audio_size is 100MB
        assert content_filter._validate_file_size(100 * 1024 * 1024, "image") is False
        assert content_filter._validate_file_size(200 * 1024 * 1024, "audio") is False

    def test_check_file_content_safety_safe(self, content_filter):
        """Test file content safety check for safe files"""
        safe_content = b'This is a safe text file with no dangerous content.'
        is_safe, reason = content_filter._check_file_content_safety(safe_content)

        assert is_safe is True
        assert reason == "Content appears safe"

    def test_check_file_content_safety_dangerous(self, content_filter):
        """Test file content safety check for dangerous files"""
        dangerous_content = b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'
        is_safe, reason = content_filter._check_file_content_safety(dangerous_content)

        assert is_safe is False
        assert "Dangerous content detected" in reason

    def test_check_file_content_safety_script(self, content_filter):
        """Test file content safety check for script files"""
        script_content = b'#!/bin/bash\necho "Hello World"'
        is_safe, reason = content_filter._check_file_content_safety(script_content)

        assert is_safe is False
        assert "Dangerous content detected" in reason

    @pytest.mark.asyncio
    async def test_scan_for_viruses_clean(self, content_filter):
        """Test virus scanning for clean files"""
        with patch.object(content_filter, '_clamav_client') as mock_clamav:
            mock_clamav.scan_stream.return_value = None  # No virus found

            is_clean, result = await content_filter._scan_for_viruses(b'clean file content')

            assert is_clean is True
            assert result == "Clean"

    @pytest.mark.asyncio
    async def test_scan_for_viruses_infected(self, content_filter):
        """Test virus scanning for infected files"""
        with patch.object(content_filter, '_clamav_client') as mock_clamav:
            mock_clamav.scan_stream.return_value = {
                "file": ("FOUND", "EICAR-Test-File")
            }

            is_clean, result = await content_filter._scan_for_viruses(b'infected content')

            assert is_clean is False
            assert "Virus detected" in result

    @pytest.mark.asyncio
    async def test_scan_for_viruses_error(self, content_filter):
        """Test virus scanning with scan error"""
        with patch.object(content_filter, '_clamav_client') as mock_clamav:
            mock_clamav.scan_stream.return_value = {
                "file": ("ERROR", "Scan failed")
            }

            is_clean, result = await content_filter._scan_for_viruses(b'content')

            assert is_clean is False
            assert "Scan error" in result

    @pytest.mark.asyncio
    async def test_scan_for_viruses_disabled(self, content_filter):
        """Test virus scanning when disabled"""
        content_filter._clamav_client = None

        is_clean, result = await content_filter._scan_for_viruses(b'content')

        assert is_clean is True
        assert result == "Virus scanning disabled"

    @pytest.mark.asyncio
    async def test_validate_upload_image_success(self, content_filter, mock_image_file):
        """Test successful image upload validation"""
        with patch.object(content_filter, '_detect_true_file_type') as mock_detect, \
             patch.object(content_filter, '_validate_image_file') as mock_validate, \
             patch.object(content_filter, '_check_file_content_safety') as mock_safety, \
             patch.object(content_filter, '_scan_for_viruses') as mock_scan:

            mock_detect.return_value = ("image/jpeg", "JPEG image")
            mock_validate.return_value = True
            mock_safety.return_value = (True, "Safe")
            mock_scan.return_value = (True, "Clean")

            result = await content_filter.validate_upload(mock_image_file, "image")

            assert result["is_valid"] is True
            assert len(result["errors"]) == 0
            assert "File validation completed successfully" in result["warnings"]

    @pytest.mark.asyncio
    async def test_validate_upload_audio_success(self, content_filter, mock_audio_file):
        """Test successful audio upload validation"""
        with patch.object(content_filter, '_detect_true_file_type') as mock_detect, \
             patch.object(content_filter, '_validate_audio_file') as mock_validate, \
             patch.object(content_filter, '_check_file_content_safety') as mock_safety, \
             patch.object(content_filter, '_scan_for_viruses') as mock_scan:

            mock_detect.return_value = ("audio/mpeg", "MP3 audio")
            mock_validate.return_value = True
            mock_safety.return_value = (True, "Safe")
            mock_scan.return_value = (True, "Clean")

            result = await content_filter.validate_upload(mock_audio_file, "audio")

            assert result["is_valid"] is True
            assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_upload_suspicious_filename(self, content_filter, mock_suspicious_file):
        """Test upload validation for suspicious filename"""
        result = await content_filter.validate_upload(mock_suspicious_file, "image")

        assert result["is_valid"] is False
        assert "Suspicious file pattern detected" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_upload_empty_file(self, content_filter):
        """Test upload validation for empty file"""
        empty_file = MagicMock(spec=UploadFile)
        empty_file.filename = "empty.jpg"
        empty_file.content_type = "image/jpeg"
        empty_file.size = 0
        empty_file.read = AsyncMock(return_value=b'')
        empty_file.seek = AsyncMock()

        result = await content_filter.validate_upload(empty_file, "image")

        assert result["is_valid"] is False
        assert "File is empty" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_upload_file_too_large(self, content_filter):
        """Test upload validation for oversized file"""
        large_file = MagicMock(spec=UploadFile)
        large_file.filename = "large.jpg"
        large_file.content_type = "image/jpeg"
        large_file.size = 200 * 1024 * 1024  # 200MB
        large_file.read = AsyncMock(return_value=b'x' * (200 * 1024 * 1024))
        large_file.seek = AsyncMock()

        result = await content_filter.validate_upload(large_file, "image")

        assert result["is_valid"] is False
        assert "File too large" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_validate_upload_virus_detected(self, content_filter, mock_image_file):
        """Test upload validation when virus is detected"""
        with patch.object(content_filter, '_detect_true_file_type') as mock_detect, \
             patch.object(content_filter, '_validate_image_file') as mock_validate, \
             patch.object(content_filter, '_check_file_content_safety') as mock_safety, \
             patch.object(content_filter, '_scan_for_viruses') as mock_scan:

            mock_detect.return_value = ("image/jpeg", "JPEG image")
            mock_validate.return_value = True
            mock_safety.return_value = (True, "Safe")
            mock_scan.return_value = (False, "Virus detected: EICAR-Test-File")

            result = await content_filter.validate_upload(mock_image_file, "image")

            assert result["is_valid"] is False
            assert "Virus scan failed" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_validate_upload_dangerous_content(self, content_filter, mock_image_file):
        """Test upload validation for dangerous content"""
        with patch.object(content_filter, '_detect_true_file_type') as mock_detect, \
             patch.object(content_filter, '_validate_image_file') as mock_validate, \
             patch.object(content_filter, '_check_file_content_safety') as mock_safety:

            mock_detect.return_value = ("image/jpeg", "JPEG image")
            mock_validate.return_value = True
            mock_safety.return_value = (False, "Dangerous content detected: MZ")

            result = await content_filter.validate_upload(mock_image_file, "image")

            assert result["is_valid"] is False
            assert "Dangerous content detected" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_validate_upload_validation_error(self, content_filter, mock_image_file):
        """Test upload validation with validation error"""
        with patch.object(content_filter, '_detect_true_file_type') as mock_detect:
            mock_detect.side_effect = Exception("Validation error")

            result = await content_filter.validate_upload(mock_image_file, "image")

            assert result["is_valid"] is False
            assert "Validation error" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_get_filter_status(self, content_filter):
        """Test getting content filter status"""
        status = await content_filter.get_filter_status()

        assert "content_filter_enabled" in status
        assert "virus_scan_enabled" in status
        assert "clamav_available" in status
        assert "clamav_connected" in status
        assert "max_scan_size" in status
        assert "suspicious_patterns" in status
