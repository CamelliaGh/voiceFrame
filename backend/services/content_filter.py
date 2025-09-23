"""
Content Filtering Service for AudioPoster

Provides advanced content filtering for uploaded files including:
- True file type detection using python-magic
- Virus scanning with ClamAV
- Suspicious file pattern detection
- File content validation
"""

import fnmatch
import logging
import magic
import os
import tempfile
from typing import Dict, List, Optional, Tuple
from fastapi import UploadFile, HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..config import settings

logger = logging.getLogger(__name__)

# Try to import ClamAV scanner
try:
    import pyclamd
    CLAMAV_AVAILABLE = True
except ImportError:
    CLAMAV_AVAILABLE = False
    logger.warning("pyclamd not available - virus scanning will be disabled")


class ContentFilter:
    """Advanced content filtering service for uploaded files"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._clamav_client = None
        self._initialize_clamav()

    def _initialize_clamav(self):
        """Initialize ClamAV client if available and enabled"""
        if not CLAMAV_AVAILABLE or not settings.virus_scan_enabled:
            logger.info("Virus scanning disabled or ClamAV not available")
            return

        try:
            self._clamav_client = pyclamd.ClamdUnixSocket()
            if self._clamav_client.ping():
                logger.info("ClamAV connection established successfully")
            else:
                logger.warning("ClamAV daemon not responding")
                self._clamav_client = None
        except Exception as e:
            logger.warning(f"Failed to connect to ClamAV: {e}")
            self._clamav_client = None

    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        return os.path.splitext(filename.lower())[1] if filename else ""

    def _is_suspicious_pattern(self, filename: str) -> bool:
        """Check if filename matches suspicious patterns"""
        if not filename:
            return True

        filename_lower = filename.lower()

        for pattern in settings.suspicious_file_patterns:
            if fnmatch.fnmatch(filename_lower, pattern):
                logger.warning(f"Suspicious file pattern detected: {filename} matches {pattern}")
                return True

        return False

    def _detect_true_file_type(self, file_content: bytes) -> Tuple[str, str]:
        """
        Detect true file type using python-magic

        Returns:
            Tuple[str, str]: (mime_type, file_type_description)
        """
        try:
            # Get MIME type
            mime_type = magic.from_buffer(file_content, mime=True)

            # Get human-readable description
            file_description = magic.from_buffer(file_content)

            return mime_type, file_description
        except Exception as e:
            logger.error(f"File type detection failed: {e}")
            return "application/octet-stream", "Unknown file type"

    def _validate_image_file(self, file_content: bytes, declared_mime: str) -> bool:
        """Validate that the file is actually an image"""
        true_mime, description = self._detect_true_file_type(file_content)

        # Check if true MIME type matches declared type
        if not true_mime.startswith("image/"):
            logger.warning(f"File declared as {declared_mime} but detected as {true_mime}")
            return False

        # Additional validation for common image formats
        valid_image_types = {
            "image/jpeg", "image/jpg", "image/png", "image/gif",
            "image/bmp", "image/webp", "image/tiff"
        }

        if true_mime not in valid_image_types:
            logger.warning(f"Unsupported image type: {true_mime}")
            return False

        return True

    def _validate_audio_file(self, file_content: bytes, declared_mime: str) -> bool:
        """Validate that the file is actually an audio file"""
        true_mime, description = self._detect_true_file_type(file_content)

        # Check if true MIME type matches declared type
        if not true_mime.startswith("audio/"):
            logger.warning(f"File declared as {declared_mime} but detected as {true_mime}")
            return False

        # Additional validation for common audio formats
        valid_audio_types = {
            "audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4",
            "audio/aac", "audio/ogg", "audio/flac", "audio/x-flac"
        }

        if true_mime not in valid_audio_types:
            logger.warning(f"Unsupported audio type: {true_mime}")
            return False

        return True

    async def _scan_for_viruses(self, file_content: bytes) -> Tuple[bool, str]:
        """
        Scan file for viruses using ClamAV

        Returns:
            Tuple[bool, str]: (is_clean, scan_result)
        """
        if not self._clamav_client or not settings.virus_scan_enabled:
            return True, "Virus scanning disabled"

        try:
            # Run virus scan in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._clamav_client.scan_stream,
                file_content
            )

            if result is None:
                return True, "Clean"
            else:
                # result is a dict with file path as key and scan result as value
                for file_path, scan_result in result.items():
                    if scan_result[0] == "FOUND":
                        logger.warning(f"Virus detected: {scan_result[1]}")
                        return False, f"Virus detected: {scan_result[1]}"
                    elif scan_result[0] == "ERROR":
                        logger.error(f"Virus scan error: {scan_result[1]}")
                        return False, f"Scan error: {scan_result[1]}"

            return True, "Clean"

        except Exception as e:
            logger.error(f"Virus scan failed: {e}")
            # Fail open - allow file if virus scanning fails
            return True, f"Scan failed: {str(e)}"

    def _validate_file_size(self, file_size: int, file_type: str) -> bool:
        """Validate file size against configured limits"""
        if file_type == "image":
            max_size = settings.max_photo_size
        elif file_type == "audio":
            max_size = settings.max_audio_size
        else:
            max_size = settings.max_file_scan_size

        if file_size > max_size:
            logger.warning(f"File too large: {file_size} bytes (max: {max_size})")
            return False

        return True

    def _check_file_content_safety(self, file_content: bytes) -> Tuple[bool, str]:
        """
        Check file content for safety issues

        Returns:
            Tuple[bool, str]: (is_safe, reason)
        """
        # Check for embedded executables or scripts
        dangerous_signatures = [
            b"MZ",  # PE executable
            b"\x7fELF",  # ELF executable
            b"#!/bin/",  # Shell script
            b"<script",  # JavaScript
            b"javascript:",  # JavaScript URL
            b"vbscript:",  # VBScript URL
        ]

        # Only check first 1KB for performance
        header = file_content[:1024]

        for signature in dangerous_signatures:
            if signature in header:
                logger.warning(f"Dangerous content signature detected: {signature}")
                return False, f"Dangerous content detected: {signature.decode('utf-8', errors='ignore')}"

        return True, "Content appears safe"

    async def validate_upload(self, file: UploadFile, expected_type: str) -> Dict:
        """
        Comprehensive file validation

        Args:
            file: UploadFile object
            expected_type: Expected file type ("image" or "audio")

        Returns:
            Dict: Validation results
        """
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "file_info": {},
            "scan_results": {}
        }

        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            # Reset file pointer
            await file.seek(0)

            # Basic validation
            if file_size == 0:
                validation_result["errors"].append("File is empty")
                return validation_result

            # Check file size
            if not self._validate_file_size(file_size, expected_type):
                validation_result["errors"].append(f"File too large (max: {settings.max_photo_size if expected_type == 'image' else settings.max_audio_size} bytes)")
                return validation_result

            # Check suspicious filename patterns
            if self._is_suspicious_pattern(file.filename):
                validation_result["errors"].append("Suspicious file pattern detected")
                return validation_result

            # Detect true file type
            true_mime, file_description = self._detect_true_file_type(file_content)
            validation_result["file_info"] = {
                "true_mime_type": true_mime,
                "declared_mime_type": file.content_type,
                "file_description": file_description,
                "file_size": file_size,
                "filename": file.filename
            }

            # Validate file type matches expected type
            if expected_type == "image":
                if not self._validate_image_file(file_content, file.content_type):
                    validation_result["errors"].append("File is not a valid image")
                    return validation_result
            elif expected_type == "audio":
                if not self._validate_audio_file(file_content, file.content_type):
                    validation_result["errors"].append("File is not a valid audio file")
                    return validation_result

            # Check content safety
            is_safe, safety_reason = self._check_file_content_safety(file_content)
            if not is_safe:
                validation_result["errors"].append(safety_reason)
                return validation_result

            # Virus scanning (if enabled and file size allows)
            if file_size <= settings.max_file_scan_size:
                is_clean, scan_result = await self._scan_for_viruses(file_content)
                validation_result["scan_results"]["virus_scan"] = {
                    "is_clean": is_clean,
                    "result": scan_result
                }

                if not is_clean:
                    validation_result["errors"].append(f"Virus scan failed: {scan_result}")
                    return validation_result
            else:
                validation_result["warnings"].append("File too large for virus scanning")
                validation_result["scan_results"]["virus_scan"] = {
                    "is_clean": True,
                    "result": "Skipped - file too large"
                }

            # All validations passed
            validation_result["is_valid"] = True
            validation_result["warnings"].append("File validation completed successfully")

            logger.info(f"File validation successful: {file.filename} ({true_mime})")

        except Exception as e:
            logger.error(f"File validation failed: {e}")
            validation_result["errors"].append(f"Validation error: {str(e)}")

        return validation_result

    async def get_filter_status(self) -> Dict:
        """Get current content filter status for monitoring"""
        return {
            "content_filter_enabled": settings.content_filter_enabled,
            "virus_scan_enabled": settings.virus_scan_enabled,
            "clamav_available": CLAMAV_AVAILABLE,
            "clamav_connected": self._clamav_client is not None,
            "max_scan_size": settings.max_file_scan_size,
            "suspicious_patterns": settings.suspicious_file_patterns
        }


# Global content filter instance
content_filter = ContentFilter()
