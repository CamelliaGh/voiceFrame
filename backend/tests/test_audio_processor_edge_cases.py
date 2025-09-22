"""
Edge case and error scenario tests for AudioProcessor
Tests boundary conditions, invalid inputs, and error handling
"""

import asyncio
import os
import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from backend.services.audio_processor import (
    AudioFormatError,
    AudioProcessingError,
    AudioProcessor,
    AudioValidationError,
)


class TestAudioProcessorEdgeCases:
    """Edge case and error scenario tests for AudioProcessor"""

    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance for testing"""
        processor = AudioProcessor()
        return processor

    @pytest.fixture
    def mock_file_uploader(self):
        """Mock FileUploader for testing"""
        with patch("backend.services.audio_processor.FileUploader") as mock_uploader:
            mock_instance = MagicMock()
            mock_instance.s3_client = MagicMock()
            mock_instance.local_storage_path = "/tmp/test"
            mock_uploader.return_value = mock_instance
            yield mock_instance

    # ==================== BOUNDARY CONDITION TESTS ====================

    def test_empty_audio_file(self, audio_processor, mock_file_uploader):
        """Test handling of empty audio file"""
        # Create empty file
        empty_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        empty_file.close()

        try:
            # Test validation
            with pytest.raises(AudioValidationError, match="File is empty"):
                audio_processor.validate_audio_file(empty_file.name)

        finally:
            os.unlink(empty_file.name)

    def test_minimal_audio_file(self, audio_processor, mock_file_uploader):
        """Test handling of minimal audio file (1 sample)"""
        # Create minimal audio file
        minimal_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        minimal_file.write(b"\x00\x00\x00\x00")  # 4 bytes
        minimal_file.close()

        try:
            # Test validation
            with pytest.raises(AudioValidationError, match="Audio file too short"):
                audio_processor.validate_audio_file(minimal_file.name)

        finally:
            os.unlink(minimal_file.name)

    def test_maximum_file_size(self, audio_processor, mock_file_uploader):
        """Test handling of maximum file size"""
        # Create file at maximum size
        max_size = 100 * 1024 * 1024  # 100MB
        max_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        max_file.write(b"0" * max_size)
        max_file.close()

        try:
            # Test validation
            result = audio_processor.validate_audio_file(max_file.name)
            assert result["valid"] is True
            assert result["file_size"] == max_size

        finally:
            os.unlink(max_file.name)

    def test_oversized_file(self, audio_processor, mock_file_uploader):
        """Test handling of oversized file"""
        # Create oversized file
        oversized_size = 101 * 1024 * 1024  # 101MB
        oversized_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        oversized_file.write(b"0" * oversized_size)
        oversized_file.close()

        try:
            # Test validation
            with pytest.raises(AudioValidationError, match="File size exceeds maximum"):
                audio_processor.validate_audio_file(oversized_file.name)

        finally:
            os.unlink(oversized_file.name)

    def test_zero_duration_audio(self, audio_processor, mock_file_uploader):
        """Test handling of zero duration audio"""
        # Create audio with zero duration
        sample_rate = 44100
        duration = 0.0
        audio_data = np.array([])

        # Test metadata extraction
        with pytest.raises(AudioProcessingError, match="Audio duration is zero"):
            audio_processor.extract_audio_metadata_from_data(audio_data, sample_rate)

    def test_single_sample_audio(self, audio_processor, mock_file_uploader):
        """Test handling of single sample audio"""
        # Create audio with single sample
        sample_rate = 44100
        audio_data = np.array([0.5])

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(1.0 / sample_rate, rel=0.01)
        assert result["sample_rate"] == sample_rate
        assert result["channels"] == 1

    def test_maximum_duration_audio(self, audio_processor, mock_file_uploader):
        """Test handling of maximum duration audio"""
        # Create audio at maximum duration
        sample_rate = 44100
        duration = 600.0  # 10 minutes
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["sample_rate"] == sample_rate
        assert result["channels"] == 1

    def test_oversized_duration_audio(self, audio_processor, mock_file_uploader):
        """Test handling of oversized duration audio"""
        # Create audio with oversized duration
        sample_rate = 44100
        duration = 601.0  # 10 minutes 1 second
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Test validation
        with pytest.raises(
            AudioValidationError, match="Audio duration exceeds maximum"
        ):
            audio_processor.validate_audio_duration(duration)

    # ==================== INVALID INPUT TESTS ====================

    def test_nonexistent_file(self, audio_processor, mock_file_uploader):
        """Test handling of nonexistent file"""
        # Test validation
        with pytest.raises(AudioValidationError, match="File does not exist"):
            audio_processor.validate_audio_file("/nonexistent/file.wav")

    def test_invalid_file_extension(self, audio_processor, mock_file_uploader):
        """Test handling of invalid file extension"""
        # Create file with invalid extension
        invalid_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xyz")
        invalid_file.write(b"fake audio data")
        invalid_file.close()

        try:
            # Test validation
            with pytest.raises(AudioFormatError, match="Unsupported audio format"):
                audio_processor.validate_audio_file(invalid_file.name)

        finally:
            os.unlink(invalid_file.name)

    def test_corrupted_audio_file(self, audio_processor, mock_file_uploader):
        """Test handling of corrupted audio file"""
        # Create corrupted audio file
        corrupted_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        corrupted_file.write(b"corrupted audio data")
        corrupted_file.close()

        try:
            # Test validation
            with pytest.raises(AudioProcessingError, match="Failed to load audio file"):
                audio_processor.extract_audio_metadata(corrupted_file.name)

        finally:
            os.unlink(corrupted_file.name)

    def test_invalid_audio_data(self, audio_processor, mock_file_uploader):
        """Test handling of invalid audio data"""
        # Test with invalid audio data
        invalid_data = np.array([np.inf, np.nan, -np.inf])

        with pytest.raises(AudioProcessingError, match="Invalid audio data"):
            audio_processor.extract_audio_metadata_from_data(invalid_data, 44100)

    def test_negative_sample_rate(self, audio_processor, mock_file_uploader):
        """Test handling of negative sample rate"""
        # Test with negative sample rate
        audio_data = np.array([0.5, 0.3, 0.1])

        with pytest.raises(AudioProcessingError, match="Invalid sample rate"):
            audio_processor.extract_audio_metadata_from_data(audio_data, -44100)

    def test_zero_sample_rate(self, audio_processor, mock_file_uploader):
        """Test handling of zero sample rate"""
        # Test with zero sample rate
        audio_data = np.array([0.5, 0.3, 0.1])

        with pytest.raises(AudioProcessingError, match="Invalid sample rate"):
            audio_processor.extract_audio_metadata_from_data(audio_data, 0)

    def test_invalid_trimming_method(self, audio_processor, mock_file_uploader):
        """Test handling of invalid trimming method"""
        # Create test audio data
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Test with invalid method
        with pytest.raises(AudioProcessingError, match="Invalid trimming method"):
            audio_processor.advanced_silence_trimming(
                audio_data, sample_rate, method="invalid"
            )

    def test_invalid_peak_detection_method(self, audio_processor, mock_file_uploader):
        """Test handling of invalid peak detection method"""
        # Create test audio data
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Test with invalid method
        with pytest.raises(AudioProcessingError, match="Invalid peak detection method"):
            audio_processor.detect_peaks(audio_data, sample_rate, method="invalid")

    # ==================== EDGE CASE AUDIO CONTENT TESTS ====================

    def test_silent_audio(self, audio_processor, mock_file_uploader):
        """Test handling of completely silent audio"""
        # Create silent audio
        sample_rate = 44100
        duration = 10.0
        audio_data = np.zeros(int(sample_rate * duration))

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["rms_energy"] == 0.0
        assert result["peak_amplitude"] == 0.0
        assert result["dynamic_range"] == 0.0

    def test_constant_amplitude_audio(self, audio_processor, mock_file_uploader):
        """Test handling of constant amplitude audio"""
        # Create constant amplitude audio
        sample_rate = 44100
        duration = 10.0
        audio_data = np.full(int(sample_rate * duration), 0.5)

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["rms_energy"] == pytest.approx(0.5, rel=0.01)
        assert result["peak_amplitude"] == pytest.approx(0.5, rel=0.01)
        assert result["dynamic_range"] == 0.0

    def test_clipped_audio(self, audio_processor, mock_file_uploader):
        """Test handling of clipped audio"""
        # Create clipped audio
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 2.0 * np.sin(2 * np.pi * 440 * t)  # Will clip at ±1.0

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["peak_amplitude"] == pytest.approx(1.0, rel=0.01)  # Clipped
        assert result["dynamic_range"] > 0.0

    def test_very_low_amplitude_audio(self, audio_processor, mock_file_uploader):
        """Test handling of very low amplitude audio"""
        # Create very low amplitude audio
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.001 * np.sin(2 * np.pi * 440 * t)  # Very low amplitude

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["rms_energy"] < 0.01
        assert result["peak_amplitude"] < 0.01
        assert result["dynamic_range"] > 0.0

    def test_very_high_frequency_audio(self, audio_processor, mock_file_uploader):
        """Test handling of very high frequency audio"""
        # Create very high frequency audio
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 20000 * t)  # 20kHz

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["sample_rate"] == sample_rate
        assert result["channels"] == 1

    def test_very_low_frequency_audio(self, audio_processor, mock_file_uploader):
        """Test handling of very low frequency audio"""
        # Create very low frequency audio
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 20 * t)  # 20Hz

        # Test metadata extraction
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )

        assert result["duration"] == pytest.approx(duration, rel=0.01)
        assert result["sample_rate"] == sample_rate
        assert result["channels"] == 1

    # ==================== ERROR RECOVERY TESTS ====================

    def test_recovery_from_validation_error(self, audio_processor, mock_file_uploader):
        """Test recovery from validation error"""
        # Create invalid file
        invalid_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        invalid_file.write(b"invalid data")
        invalid_file.close()

        try:
            # Test validation error
            with pytest.raises(AudioProcessingError):
                audio_processor.extract_audio_metadata(invalid_file.name)

            # Test that processor is still functional
            # Create valid file
            valid_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sample_rate = 44100
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
            valid_file.write(audio_data.astype(np.float32).tobytes())
            valid_file.close()

            try:
                # Test that processor works with valid file
                result = audio_processor.extract_audio_metadata(valid_file.name)
                assert result["duration"] > 0

            finally:
                os.unlink(valid_file.name)

        finally:
            os.unlink(invalid_file.name)

    def test_recovery_from_processing_error(self, audio_processor, mock_file_uploader):
        """Test recovery from processing error"""
        # Create audio data that will cause processing error
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Mock processing error
        with patch.object(
            audio_processor,
            "analyze_audio_quality",
            side_effect=AudioProcessingError("Processing error"),
        ):
            # Test that error is properly handled
            with pytest.raises(AudioProcessingError, match="Processing error"):
                audio_processor.analyze_audio_quality(
                    "test.wav", audio_data, sample_rate
                )

        # Test that processor is still functional
        # Test with valid data
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )
        assert result["duration"] > 0

    # ==================== MEMORY EDGE CASES ====================

    def test_memory_cleanup_after_error(self, audio_processor, mock_file_uploader):
        """Test memory cleanup after processing error"""
        # Monitor memory usage
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create audio data that will cause error
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Mock processing error
        with patch.object(
            audio_processor,
            "analyze_audio_quality",
            side_effect=AudioProcessingError("Processing error"),
        ):
            # Test that error is properly handled
            with pytest.raises(AudioProcessingError):
                audio_processor.analyze_audio_quality(
                    "test.wav", audio_data, sample_rate
                )

        # Check memory usage after error
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory increase is reasonable (should be < 50MB)
        assert (
            memory_increase < 50.0
        ), f"Memory increase too high after error: {memory_increase}MB"

    def test_memory_cleanup_after_success(self, audio_processor, mock_file_uploader):
        """Test memory cleanup after successful processing"""
        # Monitor memory usage
        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create audio data
        sample_rate = 44100
        duration = 10.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Process audio data
        result = audio_processor.extract_audio_metadata_from_data(
            audio_data, sample_rate
        )
        assert result["duration"] > 0

        # Check memory usage after success
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory increase is reasonable (should be < 50MB)
        assert (
            memory_increase < 50.0
        ), f"Memory increase too high after success: {memory_increase}MB"

    # ==================== CONCURRENT ERROR TESTS ====================

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, audio_processor, mock_file_uploader):
        """Test error handling with concurrent processing"""
        # Create tasks that will cause errors
        tasks = []

        for i in range(3):
            # Create invalid file
            invalid_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            invalid_file.write(b"invalid data")
            invalid_file.close()

            # Create task that will fail
            task = audio_processor.process_audio_file(
                f"temp_audio/invalid{i}.mp3", f"test-session-{i}"
            )
            tasks.append(task)

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all tasks failed with appropriate errors
        assert len(results) == 3
        for result in results:
            assert isinstance(result, Exception)
            assert "Failed to load audio file" in str(result)

    @pytest.mark.asyncio
    async def test_mixed_success_failure_concurrent(
        self, audio_processor, mock_file_uploader
    ):
        """Test mixed success/failure with concurrent processing"""
        # Create valid audio file
        valid_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
        valid_file.write(audio_data.astype(np.float32).tobytes())
        valid_file.close()

        try:
            # Create tasks with mixed success/failure
            tasks = []

            # Valid task
            audio_processor._download_audio_file = AsyncMock(
                return_value=valid_file.name
            )
            audio_processor._upload_waveform = AsyncMock(
                return_value="waveforms/test-session.png"
            )

            with patch("backend.services.audio_processor.settings") as mock_settings:
                mock_settings.max_audio_duration = 600.0

                # Valid task
                task1 = audio_processor.process_audio_file(
                    "temp_audio/valid.mp3", "test-session-1"
                )
                tasks.append(task1)

                # Invalid task
                invalid_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                invalid_file.write(b"invalid data")
                invalid_file.close()

                audio_processor._download_audio_file = AsyncMock(
                    return_value=invalid_file.name
                )
                task2 = audio_processor.process_audio_file(
                    "temp_audio/invalid.mp3", "test-session-2"
                )
                tasks.append(task2)

            # Run all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify mixed results
            assert len(results) == 2
            assert results[0]["status"] == "completed"  # Valid task
            assert isinstance(results[1], Exception)  # Invalid task

        finally:
            os.unlink(valid_file.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
