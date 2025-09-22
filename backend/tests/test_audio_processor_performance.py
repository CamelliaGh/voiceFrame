"""
Performance and stress tests for AudioProcessor
Tests memory usage, processing speed, and system resource utilization
"""

import asyncio
import os
import tempfile
import time
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import psutil
import pytest

from backend.services.audio_processor import AudioProcessingError, AudioProcessor


class TestAudioProcessorPerformance:
    """Performance and stress tests for AudioProcessor"""

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

    @pytest.fixture
    def large_audio_file(self):
        """Create large audio file for performance testing"""
        # Create a 10-minute audio signal
        sample_rate = 44100
        duration = 600.0  # 10 minutes
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.write(audio_data.astype(np.float32).tobytes())
        temp_file.close()

        yield temp_file.name

        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    @pytest.fixture
    def very_large_audio_file(self):
        """Create very large audio file for stress testing"""
        # Create a 30-minute audio signal
        sample_rate = 44100
        duration = 1800.0  # 30 minutes
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.2 * np.sin(2 * np.pi * 440 * t)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.write(audio_data.astype(np.float32).tobytes())
        temp_file.close()

        yield temp_file.name

        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

    # ==================== MEMORY USAGE TESTS ====================

    def test_memory_usage_small_file(self, audio_processor, mock_file_uploader):
        """Test memory usage with small audio file"""
        # Create small audio file
        sample_rate = 44100
        duration = 10.0  # 10 seconds
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.write(audio_data.astype(np.float32).tobytes())
        temp_file.close()

        try:
            # Monitor memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Process audio file
            result = audio_processor.extract_audio_metadata(temp_file.name)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Verify memory usage is reasonable (should be < 100MB for small file)
            assert (
                memory_increase < 100.0
            ), f"Memory increase too high: {memory_increase}MB"

            # Verify result is correct
            assert result["duration"] == pytest.approx(duration, rel=0.1)
            assert result["sample_rate"] == sample_rate

        finally:
            os.unlink(temp_file.name)

    def test_memory_usage_large_file(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test memory usage with large audio file"""
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process large audio file
        result = audio_processor.extract_audio_metadata(large_audio_file)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory usage is reasonable (should be < 500MB for large file)
        assert memory_increase < 500.0, f"Memory increase too high: {memory_increase}MB"

        # Verify result is correct
        assert result["duration"] == pytest.approx(600.0, rel=0.1)  # 10 minutes
        assert result["sample_rate"] == 44100

    def test_memory_usage_very_large_file(
        self, audio_processor, very_large_audio_file, mock_file_uploader
    ):
        """Test memory usage with very large audio file"""
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process very large audio file
        result = audio_processor.extract_audio_metadata(very_large_audio_file)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory usage is reasonable (should be < 1GB for very large file)
        assert (
            memory_increase < 1000.0
        ), f"Memory increase too high: {memory_increase}MB"

        # Verify result is correct
        assert result["duration"] == pytest.approx(1800.0, rel=0.1)  # 30 minutes
        assert result["sample_rate"] == 44100

    def test_memory_usage_chunk_processing(
        self, audio_processor, very_large_audio_file, mock_file_uploader
    ):
        """Test memory usage with chunk processing"""
        # Load audio data
        import librosa

        audio_data, sample_rate = librosa.load(very_large_audio_file, sr=44100)

        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process with chunk processing
        result = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, method="dynamic"
        )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory usage is reasonable with chunk processing
        assert (
            memory_increase < 200.0
        ), f"Memory increase too high with chunk processing: {memory_increase}MB"

        # Verify result is correct
        assert "trimmed_audio" in result
        assert "trim_info" in result
        assert result["trim_info"]["original_duration"] > 0
        assert result["trim_info"]["trimmed_duration"] > 0

    # ==================== PROCESSING SPEED TESTS ====================

    def test_processing_speed_metadata_extraction(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test processing speed for metadata extraction"""
        # Measure processing time
        start_time = time.time()
        result = audio_processor.extract_audio_metadata(large_audio_file)
        end_time = time.time()

        processing_time = end_time - start_time

        # Verify processing time is reasonable (should be < 5 seconds for 10-minute file)
        assert (
            processing_time < 5.0
        ), f"Metadata extraction too slow: {processing_time:.2f}s"

        # Verify result is correct
        assert result["duration"] > 0
        assert result["sample_rate"] > 0

    def test_processing_speed_quality_analysis(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test processing speed for quality analysis"""
        # Load audio data
        import librosa

        audio_data, sample_rate = librosa.load(large_audio_file, sr=44100)

        # Measure processing time
        start_time = time.time()
        result = audio_processor.analyze_audio_quality(
            large_audio_file, audio_data, sample_rate
        )
        end_time = time.time()

        processing_time = end_time - start_time

        # Verify processing time is reasonable (should be < 10 seconds for 10-minute file)
        assert (
            processing_time < 10.0
        ), f"Quality analysis too slow: {processing_time:.2f}s"

        # Verify result is correct
        assert "quality_score" in result
        assert 0.0 <= result["quality_score"] <= 1.0

    def test_processing_speed_advanced_trimming(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test processing speed for advanced trimming"""
        # Load audio data
        import librosa

        audio_data, sample_rate = librosa.load(large_audio_file, sr=44100)

        # Test different trimming methods
        trimming_methods = ["dynamic", "split", "segment", "adaptive"]

        for method in trimming_methods:
            # Measure processing time
            start_time = time.time()
            result = audio_processor.advanced_silence_trimming(
                audio_data, sample_rate, method=method
            )
            end_time = time.time()

            processing_time = end_time - start_time

            # Verify processing time is reasonable (should be < 15 seconds for 10-minute file)
            assert (
                processing_time < 15.0
            ), f"Advanced trimming ({method}) too slow: {processing_time:.2f}s"

            # Verify result is correct
            assert "trimmed_audio" in result
            assert "trim_info" in result

    def test_processing_speed_peak_detection(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test processing speed for peak detection"""
        # Load audio data
        import librosa

        audio_data, sample_rate = librosa.load(large_audio_file, sr=44100)

        # Test different peak detection methods
        peak_methods = ["onset", "spectral", "envelope", "all"]

        for method in peak_methods:
            # Measure processing time
            start_time = time.time()
            result = audio_processor.detect_peaks(
                audio_data, sample_rate, method=method
            )
            end_time = time.time()

            processing_time = end_time - start_time

            # Verify processing time is reasonable (should be < 20 seconds for 10-minute file)
            assert (
                processing_time < 20.0
            ), f"Peak detection ({method}) too slow: {processing_time:.2f}s"

            # Verify result is correct
            assert "peaks" in result
            assert "peak_statistics" in result

    def test_processing_speed_waveform_generation(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test processing speed for waveform generation"""
        # Load audio data
        import librosa

        audio_data, sample_rate = librosa.load(large_audio_file, sr=44100)

        # Measure processing time
        start_time = time.time()
        result = audio_processor._generate_waveform_image(audio_data, sample_rate)
        end_time = time.time()

        processing_time = end_time - start_time

        # Verify processing time is reasonable (should be < 3 seconds for 10-minute file)
        assert (
            processing_time < 3.0
        ), f"Waveform generation too slow: {processing_time:.2f}s"

        # Verify result is correct
        assert isinstance(result, BytesIO)
        assert len(result.getvalue()) > 0

    # ==================== STRESS TESTS ====================

    @pytest.mark.asyncio
    async def test_stress_concurrent_processing(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test stress with concurrent audio processing"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=large_audio_file)
        audio_processor._upload_waveform = AsyncMock(
            return_value="waveforms/test-session.png"
        )

        # Mock settings
        with patch("backend.services.audio_processor.settings") as mock_settings:
            mock_settings.max_audio_duration = 600.0

            # Create many concurrent processing tasks
            num_tasks = 10
            tasks = []

            for i in range(num_tasks):
                task = audio_processor.process_audio_file(
                    f"temp_audio/test{i}.mp3", f"test-session-{i}"
                )
                tasks.append(task)

            # Run all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            total_time = end_time - start_time

            # Verify all tasks completed successfully
            assert len(results) == num_tasks
            for result in results:
                assert result["status"] == "completed"
                assert result["waveform_s3_key"] is not None

            # Verify total time is reasonable (should be < 60 seconds for 10 concurrent tasks)
            assert (
                total_time < 60.0
            ), f"Concurrent processing too slow: {total_time:.2f}s"

    def test_stress_memory_under_load(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test memory usage under heavy load"""
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple files sequentially
        num_files = 5
        for i in range(num_files):
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(open(large_audio_file, "rb").read())
            temp_file.close()

            try:
                # Process file
                result = audio_processor.extract_audio_metadata(temp_file.name)
                assert result["duration"] > 0

            finally:
                os.unlink(temp_file.name)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Verify memory usage is reasonable under load
        assert (
            memory_increase < 1000.0
        ), f"Memory increase too high under load: {memory_increase}MB"

    def test_stress_large_file_processing(
        self, audio_processor, very_large_audio_file, mock_file_uploader
    ):
        """Test stress with very large file processing"""
        # Monitor memory and time
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()

        # Process very large file
        result = audio_processor.extract_audio_metadata(very_large_audio_file)

        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        processing_time = end_time - start_time
        memory_increase = final_memory - initial_memory

        # Verify processing time is reasonable (should be < 30 seconds for 30-minute file)
        assert (
            processing_time < 30.0
        ), f"Very large file processing too slow: {processing_time:.2f}s"

        # Verify memory usage is reasonable
        assert (
            memory_increase < 1000.0
        ), f"Memory increase too high for very large file: {memory_increase}MB"

        # Verify result is correct
        assert result["duration"] == pytest.approx(1800.0, rel=0.1)  # 30 minutes
        assert result["sample_rate"] == 44100

    # ==================== RESOURCE UTILIZATION TESTS ====================

    def test_cpu_usage_during_processing(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test CPU usage during audio processing"""
        # Monitor CPU usage
        process = psutil.Process()

        # Start monitoring
        cpu_percentages = []

        def monitor_cpu():
            while True:
                cpu_percentages.append(process.cpu_percent())
                time.sleep(0.1)

        # Start monitoring thread
        import threading

        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Process audio file
        result = audio_processor.extract_audio_metadata(large_audio_file)

        # Stop monitoring
        time.sleep(0.5)  # Let monitoring finish

        # Verify CPU usage is reasonable (should be < 100% average)
        if cpu_percentages:
            avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
            assert avg_cpu < 100.0, f"CPU usage too high: {avg_cpu:.1f}%"

        # Verify result is correct
        assert result["duration"] > 0

    def test_disk_io_during_processing(
        self, audio_processor, large_audio_file, mock_file_uploader
    ):
        """Test disk I/O during audio processing"""
        # Monitor disk I/O
        process = psutil.Process()

        # Get initial I/O stats
        initial_io = process.io_counters()

        # Process audio file
        result = audio_processor.extract_audio_metadata(large_audio_file)

        # Get final I/O stats
        final_io = process.io_counters()

        # Calculate I/O increase
        read_bytes = final_io.read_bytes - initial_io.read_bytes
        write_bytes = final_io.write_bytes - initial_io.write_bytes

        # Verify I/O is reasonable (should be < 1GB for 10-minute file)
        assert (
            read_bytes < 1024 * 1024 * 1024
        ), f"Read I/O too high: {read_bytes / 1024 / 1024:.1f}MB"
        assert (
            write_bytes < 1024 * 1024 * 1024
        ), f"Write I/O too high: {write_bytes / 1024 / 1024:.1f}MB"

        # Verify result is correct
        assert result["duration"] > 0

    # ==================== PERFORMANCE BENCHMARKS ====================

    def test_performance_benchmark_metadata_extraction(
        self, audio_processor, mock_file_uploader
    ):
        """Benchmark metadata extraction performance"""
        # Test with different file sizes
        file_sizes = [10, 60, 300, 600]  # seconds

        for duration in file_sizes:
            # Create test file
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(audio_data.astype(np.float32).tobytes())
            temp_file.close()

            try:
                # Measure processing time
                start_time = time.time()
                result = audio_processor.extract_audio_metadata(temp_file.name)
                end_time = time.time()

                processing_time = end_time - start_time

                # Verify processing time scales reasonably with file size
                expected_time = duration * 0.01  # 1% of duration
                assert (
                    processing_time < expected_time
                ), f"Processing time too high for {duration}s file: {processing_time:.2f}s"

                # Verify result is correct
                assert result["duration"] == pytest.approx(duration, rel=0.1)

            finally:
                os.unlink(temp_file.name)

    def test_performance_benchmark_quality_analysis(
        self, audio_processor, mock_file_uploader
    ):
        """Benchmark quality analysis performance"""
        # Test with different file sizes
        file_sizes = [10, 60, 300]  # seconds

        for duration in file_sizes:
            # Create test file
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(audio_data.astype(np.float32).tobytes())
            temp_file.close()

            try:
                # Load audio data
                import librosa

                audio_data, sample_rate = librosa.load(temp_file.name, sr=44100)

                # Measure processing time
                start_time = time.time()
                result = audio_processor.analyze_audio_quality(
                    temp_file.name, audio_data, sample_rate
                )
                end_time = time.time()

                processing_time = end_time - start_time

                # Verify processing time scales reasonably with file size
                expected_time = duration * 0.02  # 2% of duration
                assert (
                    processing_time < expected_time
                ), f"Quality analysis too slow for {duration}s file: {processing_time:.2f}s"

                # Verify result is correct
                assert "quality_score" in result
                assert 0.0 <= result["quality_score"] <= 1.0

            finally:
                os.unlink(temp_file.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
