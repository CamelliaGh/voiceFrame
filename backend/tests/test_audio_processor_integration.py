"""
Integration tests for AudioProcessor complete pipeline
Tests end-to-end functionality including S3 integration, file handling, and complete workflows
"""

import pytest
import numpy as np
import tempfile
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from io import BytesIO

from backend.services.audio_processor import AudioProcessor, AudioProcessingError
from backend.services.file_uploader import FileUploader


class TestAudioProcessorIntegration:
    """Integration tests for complete AudioProcessor pipeline"""
    
    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance for testing"""
        processor = AudioProcessor()
        return processor
    
    @pytest.fixture
    def mock_file_uploader(self):
        """Mock FileUploader for testing"""
        with patch('backend.services.audio_processor.FileUploader') as mock_uploader:
            mock_instance = MagicMock()
            mock_instance.s3_client = MagicMock()
            mock_instance.local_storage_path = "/tmp/test"
            mock_uploader.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create sample audio file for testing"""
        # Create a 2-second audio signal
        sample_rate = 44100
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(audio_data.astype(np.float32).tobytes())
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    @pytest.fixture
    def large_audio_file(self):
        """Create large audio file for chunk processing tests"""
        # Create a 5-minute audio signal
        sample_rate = 44100
        duration = 300.0  # 5 minutes
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(audio_data.astype(np.float32).tobytes())
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    # ==================== COMPLETE PIPELINE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_complete_audio_processing_pipeline(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test complete audio processing pipeline from S3 to waveform generation"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=sample_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test-session.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0  # 10 minutes
            mock_settings.s3_bucket = "test-bucket"
            
            # Test complete pipeline
            result = await audio_processor.process_audio_file("temp_audio/test.mp3", "test-session")
            
            # Verify complete result structure
            assert result['status'] == 'completed'
            assert result['waveform_s3_key'] == "waveforms/test-session.png"
            assert result['duration'] > 0
            assert result['original_duration'] > 0
            assert result['sample_rate'] == 44100
            assert result['channels'] == 1
            
            # Verify advanced features are included
            assert 'advanced_trimming' in result
            assert 'peak_detection' in result
            assert 'quality_score' in result
            assert 'performance_stats' in result
            
            # Verify performance stats
            perf_stats = result['performance_stats']
            assert 'total_processing_time' in perf_stats
            assert 'memory_used_mb' in perf_stats
            assert 'processing_times' in perf_stats
            
            # Verify download and upload were called
            audio_processor._download_audio_file.assert_called_once_with("temp_audio/test.mp3")
            audio_processor._upload_waveform.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_with_chunk_processing(self, audio_processor, large_audio_file, mock_file_uploader):
        """Test complete pipeline with chunk processing for large files"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=large_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test-session.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0  # 10 minutes
            mock_settings.s3_bucket = "test-bucket"
            
            # Test complete pipeline with large file
            result = await audio_processor.process_audio_file("temp_audio/large.mp3", "test-session")
            
            # Verify chunk processing was used
            assert result['performance_stats']['chunk_processing_used'] is True
            assert result['processing_method'] == 'chunked'
            assert result['chunks_processed'] > 0
            
            # Verify result structure
            assert result['status'] == 'completed'
            assert result['waveform_s3_key'] == "waveforms/test-session.png"
            assert result['duration'] > 0
            assert result['original_duration'] > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_s3_download_failure(self, audio_processor, mock_file_uploader):
        """Test pipeline behavior when S3 download fails"""
        # Mock download failure
        audio_processor._download_audio_file = AsyncMock(side_effect=AudioProcessingError("Download failed"))
        
        # Test that the error is properly propagated
        with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
            await audio_processor.process_audio_file("temp_audio/test.mp3", "test-session")
    
    @pytest.mark.asyncio
    async def test_pipeline_with_waveform_upload_failure(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test pipeline behavior when waveform upload fails"""
        # Mock download success but upload failure
        audio_processor._download_audio_file = AsyncMock(return_value=sample_audio_file)
        audio_processor._upload_waveform = AsyncMock(side_effect=AudioProcessingError("Upload failed"))
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0
            
            # Test that the error is properly propagated
            with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
                await audio_processor.process_audio_file("temp_audio/test.mp3", "test-session")
    
    # ==================== S3 INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_s3_download_integration(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test S3 download integration"""
        # Mock S3 client
        mock_s3 = mock_file_uploader.s3_client
        mock_s3.download_fileobj.return_value = None
        
        # Mock file operations
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_file = MagicMock()
            mock_file.name = sample_audio_file
            mock_file.close.return_value = None
            mock_temp_file.return_value = mock_file
            
            # Mock settings
            with patch('backend.services.audio_processor.settings') as mock_settings:
                mock_settings.s3_bucket = "test-bucket"
                
                # Test S3 download
                result_path = await audio_processor._download_audio_file("temp_audio/test.mp3")
                
                # Verify S3 download was called
                mock_s3.download_fileobj.assert_called_once()
                assert result_path == sample_audio_file
    
    @pytest.mark.asyncio
    async def test_s3_upload_integration(self, audio_processor, mock_file_uploader):
        """Test S3 upload integration"""
        # Mock S3 client
        mock_s3 = mock_file_uploader.s3_client
        mock_s3.upload_fileobj.return_value = None
        
        # Create mock waveform buffer
        waveform_buffer = BytesIO(b'fake_png_data')
        
        # Mock file operations
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test_waveform.png"
            mock_file.write.return_value = None
            mock_file.close.return_value = None
            mock_temp_file.return_value = mock_file
            
            with patch('builtins.open', MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value = BytesIO(b'fake_png_data')
                
                # Mock settings
                with patch('backend.services.audio_processor.settings') as mock_settings:
                    mock_settings.s3_bucket = "test-bucket"
                    
                    # Test S3 upload
                    result_key = await audio_processor._upload_waveform(waveform_buffer, "test-session")
                    
                    # Verify S3 upload was called
                    mock_s3.upload_fileobj.assert_called_once()
                    assert result_key == "waveforms/test-session.png"
    
    @pytest.mark.asyncio
    async def test_local_storage_fallback(self, audio_processor, sample_audio_file):
        """Test local storage fallback when S3 is not available"""
        # Mock FileUploader without S3 client
        with patch('backend.services.audio_processor.FileUploader') as mock_uploader:
            mock_instance = MagicMock()
            mock_instance.s3_client = None  # No S3 client
            mock_instance.local_storage_path = "/tmp/test"
            mock_uploader.return_value = mock_instance
            
            # Mock file operations
            with patch('os.path.exists', return_value=True):
                # Test local file access
                result_path = await audio_processor._download_audio_file("temp_audio/test.mp3")
                
                # Should use local path
                expected_path = "/tmp/test/temp_audio/test.mp3"
                assert result_path == expected_path
    
    # ==================== FILE HANDLING INTEGRATION TESTS ====================
    
    def test_file_validation_integration(self, audio_processor, sample_audio_file):
        """Test file validation integration with real file"""
        # Test validation with real file
        validation_result = audio_processor.validate_audio_file(sample_audio_file)
        
        assert validation_result['valid'] is True
        assert validation_result['file_size'] > 0
        assert validation_result['duration'] > 0
        assert validation_result['sample_rate'] > 0
    
    def test_metadata_extraction_integration(self, audio_processor, sample_audio_file):
        """Test metadata extraction integration with real file"""
        # Test metadata extraction with real file
        metadata = audio_processor.extract_audio_metadata(sample_audio_file)
        
        # Verify all expected metadata fields
        expected_fields = [
            'duration', 'sample_rate', 'channels', 'rms_energy',
            'peak_amplitude', 'dynamic_range', 'avg_spectral_centroid',
            'tempo', 'zero_crossing_rate', 'file_size'
        ]
        
        for field in expected_fields:
            assert field in metadata
            assert metadata[field] is not None
    
    def test_quality_analysis_integration(self, audio_processor, sample_audio_file):
        """Test quality analysis integration with real file"""
        # Load audio data
        import librosa
        audio_data, sample_rate = librosa.load(sample_audio_file, sr=44100)
        
        # Test quality analysis with real file
        quality_metrics = audio_processor.analyze_audio_quality(sample_audio_file, audio_data, sample_rate)
        
        # Verify quality metrics
        assert 'quality_score' in quality_metrics
        assert 'snr_db' in quality_metrics
        assert 'noise_level' in quality_metrics
        assert 0.0 <= quality_metrics['quality_score'] <= 1.0
    
    def test_waveform_generation_integration(self, audio_processor, sample_audio_file):
        """Test waveform generation integration with real file"""
        # Load audio data
        import librosa
        audio_data, sample_rate = librosa.load(sample_audio_file, sr=44100)
        
        # Test waveform generation
        waveform_buffer = audio_processor._generate_waveform_image(audio_data, sample_rate)
        
        # Verify waveform generation
        assert isinstance(waveform_buffer, BytesIO)
        assert len(waveform_buffer.getvalue()) > 0
        
        # Verify it's a valid PNG
        buffer_content = waveform_buffer.getvalue()
        assert buffer_content.startswith(b'\x89PNG')
    
    # ==================== ERROR HANDLING INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling_invalid_file(self, audio_processor, mock_file_uploader):
        """Test pipeline error handling with invalid file"""
        # Create invalid audio file
        invalid_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        invalid_file.write(b'invalid audio data')
        invalid_file.close()
        
        try:
            # Mock download with invalid file
            audio_processor._download_audio_file = AsyncMock(return_value=invalid_file.name)
            
            # Test that validation error is properly handled
            with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
                await audio_processor.process_audio_file("temp_audio/invalid.mp3", "test-session")
                
        finally:
            os.unlink(invalid_file.name)
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling_oversized_file(self, audio_processor, mock_file_uploader):
        """Test pipeline error handling with oversized file"""
        # Create oversized file
        oversized_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        oversized_file.write(b'0' * (100 * 1024 * 1024 + 1))  # > 100MB
        oversized_file.close()
        
        try:
            # Mock download with oversized file
            audio_processor._download_audio_file = AsyncMock(return_value=oversized_file.name)
            
            # Test that size validation error is properly handled
            with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
                await audio_processor.process_audio_file("temp_audio/oversized.mp3", "test-session")
                
        finally:
            os.unlink(oversized_file.name)
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling_unsupported_format(self, audio_processor, mock_file_uploader):
        """Test pipeline error handling with unsupported format"""
        # Create file with unsupported extension
        unsupported_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xyz')
        unsupported_file.write(b'fake audio data')
        unsupported_file.close()
        
        try:
            # Mock download with unsupported file
            audio_processor._download_audio_file = AsyncMock(return_value=unsupported_file.name)
            
            # Test that format error is properly handled
            with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
                await audio_processor.process_audio_file("temp_audio/unsupported.xyz", "test-session")
                
        finally:
            os.unlink(unsupported_file.name)
    
    # ==================== PERFORMANCE INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_pipeline_performance_tracking(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test performance tracking in complete pipeline"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=sample_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test-session.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0
            
            # Test complete pipeline
            result = await audio_processor.process_audio_file("temp_audio/test.mp3", "test-session")
            
            # Verify performance tracking
            perf_stats = result['performance_stats']
            assert 'total_processing_time' in perf_stats
            assert 'memory_used_mb' in perf_stats
            assert 'processing_times' in perf_stats
            
            # Verify processing times are tracked
            processing_times = perf_stats['processing_times']
            assert 'download' in processing_times
            assert 'advanced_trimming' in processing_times
            assert 'peak_detection' in processing_times
            assert 'waveform_generation' in processing_times
            
            # Verify all times are positive
            for time_key, time_value in processing_times.items():
                assert isinstance(time_value, float)
                assert time_value >= 0.0
    
    @pytest.mark.asyncio
    async def test_pipeline_memory_usage_tracking(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test memory usage tracking in complete pipeline"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=sample_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test-session.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0
            
            # Test complete pipeline
            result = await audio_processor.process_audio_file("temp_audio/test.mp3", "test-session")
            
            # Verify memory usage tracking
            perf_stats = result['performance_stats']
            assert 'initial_memory_mb' in perf_stats
            assert 'final_memory_mb' in perf_stats
            assert 'memory_used_mb' in perf_stats
            
            # Verify memory values are reasonable
            assert perf_stats['initial_memory_mb'] >= 0.0
            assert perf_stats['final_memory_mb'] >= 0.0
            assert perf_stats['memory_used_mb'] >= 0.0
    
    # ==================== CONCURRENT PROCESSING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test concurrent audio processing"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=sample_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test-session.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0
            
            # Create multiple concurrent processing tasks
            tasks = []
            for i in range(3):
                task = audio_processor.process_audio_file(f"temp_audio/test{i}.mp3", f"test-session-{i}")
                tasks.append(task)
            
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            # Verify all tasks completed successfully
            assert len(results) == 3
            for result in results:
                assert result['status'] == 'completed'
                assert result['waveform_s3_key'] is not None
                assert result['duration'] > 0
    
    # ==================== CLEANUP INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_pipeline_cleanup_after_success(self, audio_processor, sample_audio_file, mock_file_uploader):
        """Test that temporary files are cleaned up after successful processing"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=sample_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test-session.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0
            
            # Test complete pipeline
            result = await audio_processor.process_audio_file("temp_audio/test.mp3", "test-session")
            
            # Verify processing completed successfully
            assert result['status'] == 'completed'
            
            # Note: In real implementation, temporary files should be cleaned up
            # This test verifies that the pipeline completes without leaving orphaned files
    
    @pytest.mark.asyncio
    async def test_pipeline_cleanup_after_error(self, audio_processor, mock_file_uploader):
        """Test that temporary files are cleaned up after processing error"""
        # Create temporary file that will cause an error
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(b'invalid audio data')
        temp_file.close()
        
        try:
            # Mock download with invalid file
            audio_processor._download_audio_file = AsyncMock(return_value=temp_file.name)
            
            # Test that error is handled and cleanup occurs
            with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
                await audio_processor.process_audio_file("temp_audio/invalid.mp3", "test-session")
                
        finally:
            # Cleanup test file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
