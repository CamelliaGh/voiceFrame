"""
Comprehensive test suite for AudioProcessor class
Tests all functionality including validation, processing, quality analysis, and error handling
"""

import pytest
import numpy as np
import tempfile
import os
import io
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from backend.services.audio_processor import (
    AudioProcessor, 
    AudioProcessingError, 
    AudioFormatError, 
    AudioValidationError
)
from backend.services.file_uploader import FileUploader


class TestAudioProcessorComprehensive:
    """Comprehensive test suite for AudioProcessor class"""
    
    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance for testing"""
        processor = AudioProcessor()
        return processor
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing"""
        # Create a 2-second audio signal with various characteristics
        sample_rate = 44100
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create audio with silence at beginning and end, and content in the middle
        audio_data = np.zeros_like(t)
        
        # Add silence at beginning (0.2s)
        # Add content in middle (0.2s - 1.8s)
        middle_start = int(0.2 * sample_rate)
        middle_end = int(1.8 * sample_rate)
        
        # Add sinusoidal content with multiple frequencies
        audio_data[middle_start:middle_end] = 0.5 * np.sin(2 * np.pi * 440 * t[middle_start:middle_end])
        audio_data[middle_start:middle_end] += 0.3 * np.sin(2 * np.pi * 880 * t[middle_start:middle_end])
        
        # Add some random peaks for peak detection testing
        peak_indices = np.random.choice(
            np.arange(middle_start, middle_end, 1000), 
            size=5, 
            replace=False
        )
        for idx in peak_indices:
            audio_data[idx:idx+100] = 0.8 * np.sin(2 * np.pi * 1000 * t[idx:idx+100])
        
        # Add silence at end (1.8s - 2.0s)
        
        return audio_data, sample_rate
    
    @pytest.fixture
    def large_audio_data(self):
        """Create large audio data for chunk processing tests"""
        # Create a 5-minute audio signal for chunk processing
        sample_rate = 44100
        duration = 300.0  # 5 minutes
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create audio with varying content
        audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
        audio_data += 0.2 * np.sin(2 * np.pi * 880 * t)
        
        # Add some silence periods
        silence_start = int(60 * sample_rate)  # 1 minute
        silence_end = int(90 * sample_rate)    # 1.5 minutes
        audio_data[silence_start:silence_end] = 0.0
        
        return audio_data, sample_rate
    
    @pytest.fixture
    def corrupted_audio_data(self):
        """Create corrupted audio data for error testing"""
        # Create audio data with NaN or infinite values
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        audio_data = np.sin(2 * np.pi * 440 * t)
        # Introduce corruption
        audio_data[1000:1100] = np.nan
        audio_data[2000:2100] = np.inf
        
        return audio_data, sample_rate
    
    @pytest.fixture
    def temp_audio_file(self, sample_audio_data):
        """Create temporary audio file for testing"""
        audio_data, sample_rate = sample_audio_data
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        
        # Write audio data as WAV file (simplified)
        # In real implementation, this would use proper WAV writing
        temp_file.write(b'RIFF')  # WAV header start
        temp_file.write(b'\x00' * 36)  # Placeholder header
        temp_file.write(audio_data.astype(np.float32).tobytes())
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    @pytest.fixture
    def mock_file_uploader(self):
        """Mock FileUploader for testing"""
        with patch('backend.services.audio_processor.FileUploader') as mock_uploader:
            mock_instance = MagicMock()
            mock_instance.s3_client = MagicMock()
            mock_instance.local_storage_path = "/tmp/test"
            mock_uploader.return_value = mock_instance
            yield mock_instance
    
    # ==================== VALIDATION TESTS ====================
    
    def test_validate_audio_file_success(self, audio_processor, temp_audio_file):
        """Test successful audio file validation"""
        result = audio_processor.validate_audio_file(temp_audio_file)
        
        assert result['valid'] is True
        assert 'file_size' in result
        assert 'mime_type' in result
        assert 'sample_rate' in result
        assert 'duration' in result
        assert 'channels' in result
        assert result['file_size'] > 0
        assert result['duration'] > 0
    
    def test_validate_audio_file_nonexistent(self, audio_processor):
        """Test validation of non-existent file"""
        with pytest.raises(AudioValidationError, match="File does not exist"):
            audio_processor.validate_audio_file("nonexistent_file.wav")
    
    def test_validate_audio_file_empty(self, audio_processor):
        """Test validation of empty file"""
        # Create empty file
        empty_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        empty_file.close()
        
        try:
            with pytest.raises(AudioValidationError, match="File is empty"):
                audio_processor.validate_audio_file(empty_file.name)
        finally:
            os.unlink(empty_file.name)
    
    def test_validate_audio_file_too_large(self, audio_processor):
        """Test validation of oversized file"""
        # Create a file larger than MAX_FILE_SIZE
        large_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        large_file.write(b'0' * (audio_processor.max_file_size + 1))
        large_file.close()
        
        try:
            with pytest.raises(AudioValidationError, match="File too large"):
                audio_processor.validate_audio_file(large_file.name)
        finally:
            os.unlink(large_file.name)
    
    def test_validate_audio_file_unsupported_format(self, audio_processor):
        """Test validation of unsupported format"""
        # Create file with unsupported extension
        unsupported_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xyz')
        unsupported_file.write(b'fake audio data')
        unsupported_file.close()
        
        try:
            with pytest.raises(AudioFormatError, match="Unsupported file format"):
                audio_processor.validate_audio_file(unsupported_file.name)
        finally:
            os.unlink(unsupported_file.name)
    
    # ==================== METADATA EXTRACTION TESTS ====================
    
    def test_extract_audio_metadata_success(self, audio_processor, temp_audio_file):
        """Test successful metadata extraction"""
        metadata = audio_processor.extract_audio_metadata(temp_audio_file)
        
        # Verify all expected metadata fields
        expected_fields = [
            'duration', 'sample_rate', 'channels', 'rms_energy',
            'peak_amplitude', 'dynamic_range', 'avg_spectral_centroid',
            'tempo', 'zero_crossing_rate', 'file_size'
        ]
        
        for field in expected_fields:
            assert field in metadata
            assert metadata[field] is not None
        
        # Verify data types and ranges
        assert isinstance(metadata['duration'], float)
        assert metadata['duration'] > 0
        assert isinstance(metadata['sample_rate'], int)
        assert metadata['sample_rate'] > 0
        assert isinstance(metadata['channels'], int)
        assert metadata['channels'] > 0
        assert isinstance(metadata['rms_energy'], float)
        assert metadata['rms_energy'] >= 0
        assert isinstance(metadata['peak_amplitude'], float)
        assert metadata['peak_amplitude'] >= 0
    
    def test_extract_audio_metadata_corrupted_file(self, audio_processor):
        """Test metadata extraction from corrupted file"""
        # Create corrupted file
        corrupted_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        corrupted_file.write(b'corrupted audio data')
        corrupted_file.close()
        
        try:
            with pytest.raises(AudioProcessingError, match="Metadata extraction failed"):
                audio_processor.extract_audio_metadata(corrupted_file.name)
        finally:
            os.unlink(corrupted_file.name)
    
    # ==================== QUALITY ANALYSIS TESTS ====================
    
    def test_analyze_audio_quality_comprehensive(self, audio_processor, sample_audio_data):
        """Test comprehensive audio quality analysis"""
        audio_data, sample_rate = sample_audio_data
        
        # Mock file path for bitrate analysis
        with patch('os.path.getsize', return_value=1024*1024):  # 1MB
            quality_metrics = audio_processor.analyze_audio_quality(
                "test.mp3", audio_data, sample_rate
            )
        
        # Verify all quality metrics are present
        expected_metrics = [
            'snr_db', 'spectral_centroid', 'spectral_bandwidth',
            'spectral_rolloff', 'spectral_contrast', 'mfcc_means',
            'zero_crossing_rate', 'rms_energy_mean', 'rms_energy_std',
            'energy_variation', 'is_speech_like', 'voice_activity_score',
            'noise_floor', 'noise_ratio', 'noise_level', 'noise_score',
            'quality_score'
        ]
        
        for metric in expected_metrics:
            assert metric in quality_metrics
        
        # Verify quality score is in valid range
        assert 0.0 <= quality_metrics['quality_score'] <= 1.0
        
        # Verify SNR is reasonable
        assert isinstance(quality_metrics['snr_db'], float)
        
        # Verify noise level classification
        assert quality_metrics['noise_level'] in ['very_low', 'low', 'moderate', 'high']
    
    def test_analyze_bitrate_with_pydub(self, audio_processor):
        """Test bitrate analysis with pydub available"""
        with patch('backend.services.audio_processor.PYDUB_AVAILABLE', True):
            with patch('backend.services.audio_processor.AudioSegment') as mock_audio_segment:
                # Mock AudioSegment
                mock_segment = MagicMock()
                mock_segment.frame_rate = 44100
                mock_segment.frame_width = 2
                mock_segment.channels = 2
                mock_audio_segment.from_file.return_value = mock_segment
                
                result = audio_processor._analyze_bitrate("test.mp3")
                
                assert 'bitrate' in result
                assert 'encoding_quality' in result
                assert 'frame_rate' in result
                assert 'frame_width' in result
                assert 'channels' in result
                assert result['encoding_quality'] in ['high', 'medium', 'standard', 'low']
    
    def test_analyze_bitrate_without_pydub(self, audio_processor):
        """Test bitrate analysis without pydub"""
        with patch('backend.services.audio_processor.PYDUB_AVAILABLE', False):
            result = audio_processor._analyze_bitrate("test.mp3")
            
            assert result['bitrate'] is None
            assert result['encoding_quality'] == 'unknown'
    
    def test_calculate_snr(self, audio_processor, sample_audio_data):
        """Test SNR calculation"""
        audio_data, sample_rate = sample_audio_data
        
        snr = audio_processor._calculate_snr(audio_data, sample_rate)
        
        assert isinstance(snr, float)
        # SNR should be reasonable for our test signal
        assert -20 <= snr <= 100  # Reasonable range
    
    def test_analyze_spectral_features(self, audio_processor, sample_audio_data):
        """Test spectral feature analysis"""
        audio_data, sample_rate = sample_audio_data
        
        spectral_features = audio_processor._analyze_spectral_features(audio_data, sample_rate)
        
        expected_features = [
            'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff',
            'spectral_contrast', 'mfcc_means'
        ]
        
        for feature in expected_features:
            assert feature in spectral_features
        
        # Verify MFCC means are provided
        assert isinstance(spectral_features['mfcc_means'], list)
        assert len(spectral_features['mfcc_means']) == 5
    
    def test_analyze_voice_activity(self, audio_processor, sample_audio_data):
        """Test voice activity analysis"""
        audio_data, sample_rate = sample_audio_data
        
        voice_activity = audio_processor._analyze_voice_activity(audio_data, sample_rate)
        
        expected_features = [
            'zero_crossing_rate', 'rms_energy_mean', 'rms_energy_std',
            'energy_variation', 'is_speech_like', 'voice_activity_score'
        ]
        
        for feature in expected_features:
            assert feature in voice_activity
        
        # Verify boolean classification
        assert isinstance(voice_activity['is_speech_like'], bool)
        
        # Verify score is in valid range
        assert 0.0 <= voice_activity['voice_activity_score'] <= 1.0
    
    def test_analyze_noise_level(self, audio_processor, sample_audio_data):
        """Test noise level analysis"""
        audio_data, sample_rate = sample_audio_data
        
        noise_analysis = audio_processor._analyze_noise_level(audio_data, sample_rate)
        
        expected_features = [
            'noise_floor', 'noise_ratio', 'noise_level', 'noise_score'
        ]
        
        for feature in expected_features:
            assert feature in noise_analysis
        
        # Verify noise level classification
        assert noise_analysis['noise_level'] in ['very_low', 'low', 'moderate', 'high']
        
        # Verify score is in valid range
        assert 0.0 <= noise_analysis['noise_score'] <= 1.0
    
    def test_calculate_quality_score(self, audio_processor):
        """Test quality score calculation"""
        # Test with various quality metrics
        quality_metrics = {
            'snr_db': 25.0,
            'encoding_quality': 'high',
            'noise_score': 0.1,
            'dynamic_range': 45.0,
            'spectral_bandwidth': 3000.0
        }
        
        score = audio_processor._calculate_quality_score(quality_metrics)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        
        # Test with minimal metrics
        minimal_metrics = {'snr_db': 5.0}
        score_minimal = audio_processor._calculate_quality_score(minimal_metrics)
        assert 0.0 <= score_minimal <= 1.0
    
    # ==================== SILENCE TRIMMING TESTS ====================
    
    def test_advanced_silence_trimming_all_methods(self, audio_processor, sample_audio_data):
        """Test all silence trimming methods"""
        audio_data, sample_rate = sample_audio_data
        
        methods = ['dynamic', 'split', 'segment', 'adaptive']
        
        for method in methods:
            trimmed_audio, trimming_info = audio_processor.advanced_silence_trimming(
                audio_data, sample_rate, trim_method=method
            )
            
            # Verify results
            assert isinstance(trimmed_audio, np.ndarray)
            assert isinstance(trimming_info, dict)
            assert 'method' in trimming_info
            assert trimming_info['method'].startswith(method)
            assert 'original_duration' in trimming_info
            assert 'trimmed_duration' in trimming_info
            assert trimming_info['trimmed_duration'] <= trimming_info['original_duration']
    
    def test_advanced_silence_trimming_invalid_method(self, audio_processor, sample_audio_data):
        """Test silence trimming with invalid method"""
        audio_data, sample_rate = sample_audio_data
        
        # Should fallback to dynamic method
        trimmed_audio, trimming_info = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, trim_method='invalid'
        )
        
        assert isinstance(trimmed_audio, np.ndarray)
        assert trimming_info['method'] == 'dynamic'
    
    def test_advanced_silence_trimming_empty_audio(self, audio_processor):
        """Test silence trimming with empty audio"""
        empty_audio = np.array([])
        
        with pytest.raises(AudioProcessingError):
            audio_processor.advanced_silence_trimming(empty_audio, 44100)
    
    # ==================== PEAK DETECTION TESTS ====================
    
    def test_detect_peaks_all_types(self, audio_processor, sample_audio_data):
        """Test peak detection with all types"""
        audio_data, sample_rate = sample_audio_data
        
        peak_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['onset', 'spectral', 'envelope']
        )
        
        # Verify all peak types are present
        assert 'onset_peaks' in peak_results
        assert 'spectral_peaks' in peak_results
        assert 'envelope_peaks' in peak_results
        assert 'peak_statistics' in peak_results
        
        # Verify peak statistics
        stats = peak_results['peak_statistics']
        assert 'total_peaks_detected' in stats
        assert 'peak_types' in stats
        assert 'peak_density' in stats
        assert 'dominant_peak_type' in stats
        
        # Verify individual peak detection results
        assert 'onset_count' in peak_results['onset_peaks']
        assert 'mel_peak_count' in peak_results['spectral_peaks']
        assert 'peak_count' in peak_results['envelope_peaks']
    
    def test_detect_peaks_individual_types(self, audio_processor, sample_audio_data):
        """Test individual peak detection types"""
        audio_data, sample_rate = sample_audio_data
        
        # Test onset detection
        onset_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['onset']
        )
        assert 'onset_peaks' in onset_results
        assert 'onset_times' in onset_results['onset_peaks']
        assert 'onset_samples' in onset_results['onset_peaks']
        
        # Test spectral detection
        spectral_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['spectral']
        )
        assert 'spectral_peaks' in spectral_results
        assert 'mel_peaks' in spectral_results['spectral_peaks']
        assert 'chroma_peaks' in spectral_results['spectral_peaks']
        
        # Test envelope detection
        envelope_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['envelope']
        )
        assert 'envelope_peaks' in envelope_results
        assert 'peak_times' in envelope_results['envelope_peaks']
        assert 'peak_amplitudes' in envelope_results['envelope_peaks']
    
    def test_detect_peaks_empty_audio(self, audio_processor):
        """Test peak detection with empty audio"""
        empty_audio = np.array([])
        
        with pytest.raises(AudioProcessingError):
            audio_processor.detect_peaks(empty_audio, 44100)
    
    # ==================== CHUNK PROCESSING TESTS ====================
    
    def test_chunk_processing_large_file(self, audio_processor, temp_large_audio_file, large_audio_data):
        """Test chunk processing for large files"""
        audio_data, sample_rate = large_audio_data
        
        # Test chunk processing decision
        should_chunk = audio_processor._should_use_chunk_processing(
            len(audio_data) / sample_rate, len(audio_data) * 4  # 4 bytes per float32
        )
        assert should_chunk is True
        
        # Test chunk processing
        chunk_metrics = audio_processor._process_audio_in_chunks(temp_large_audio_file, sample_rate)
        
        assert 'chunks_processed' in chunk_metrics
        assert 'processing_method' in chunk_metrics
        assert chunk_metrics['processing_method'] == 'chunked'
        assert chunk_metrics['chunks_processed'] > 0
    
    def test_chunk_processing_decision(self, audio_processor):
        """Test chunk processing decision logic"""
        # Test with small file (should not use chunks)
        should_chunk_small = audio_processor._should_use_chunk_processing(60.0, 10*1024*1024)  # 1 min, 10MB
        assert should_chunk_small is False
        
        # Test with long file (should use chunks)
        should_chunk_long = audio_processor._should_use_chunk_processing(180.0, 10*1024*1024)  # 3 min, 10MB
        assert should_chunk_long is True
        
        # Test with large file (should use chunks)
        should_chunk_large = audio_processor._should_use_chunk_processing(60.0, 60*1024*1024)  # 1 min, 60MB
        assert should_chunk_large is True
    
    # ==================== MEMORY MANAGEMENT TESTS ====================
    
    def test_memory_monitoring(self, audio_processor):
        """Test memory monitoring functionality"""
        memory_usage = audio_processor._monitor_memory_usage()
        
        assert isinstance(memory_usage, float)
        assert memory_usage >= 0.0
    
    def test_memory_threshold_check(self, audio_processor):
        """Test memory threshold checking"""
        # Mock high memory usage
        with patch.object(audio_processor, '_monitor_memory_usage', return_value=600.0):
            exceeds_threshold = audio_processor._check_memory_threshold()
            assert exceeds_threshold is True
        
        # Mock low memory usage
        with patch.object(audio_processor, '_monitor_memory_usage', return_value=100.0):
            exceeds_threshold = audio_processor._check_memory_threshold()
            assert exceeds_threshold is False
    
    def test_garbage_collection(self, audio_processor):
        """Test garbage collection functionality"""
        # Should not raise any exceptions
        audio_processor._force_garbage_collection()
    
    def test_optimize_audio_data_type(self, audio_processor):
        """Test audio data type optimization"""
        # Test with float64 data
        float64_data = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        optimized_data = audio_processor._optimize_audio_data_type(float64_data)
        
        assert optimized_data.dtype == np.float32
        assert np.array_equal(optimized_data, float64_data.astype(np.float32))
        
        # Test with already float32 data
        float32_data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        optimized_data = audio_processor._optimize_audio_data_type(float32_data)
        
        assert optimized_data.dtype == np.float32
        assert optimized_data is float32_data  # Should return same array
    
    # ==================== WAVEFORM GENERATION TESTS ====================
    
    def test_generate_waveform_image(self, audio_processor, sample_audio_data):
        """Test waveform image generation"""
        audio_data, sample_rate = sample_audio_data
        
        waveform_buffer = audio_processor._generate_waveform_image(audio_data, sample_rate)
        
        assert isinstance(waveform_buffer, io.BytesIO)
        assert len(waveform_buffer.getvalue()) > 0
        
        # Verify it's a valid PNG (starts with PNG signature)
        buffer_content = waveform_buffer.getvalue()
        assert buffer_content.startswith(b'\x89PNG')
    
    def test_generate_waveform_image_large_data(self, audio_processor, large_audio_data):
        """Test waveform generation with large audio data"""
        audio_data, sample_rate = large_audio_data
        
        waveform_buffer = audio_processor._generate_waveform_image(audio_data, sample_rate)
        
        assert isinstance(waveform_buffer, io.BytesIO)
        assert len(waveform_buffer.getvalue()) > 0
        
        # Should be downsampled for performance
        buffer_content = waveform_buffer.getvalue()
        assert buffer_content.startswith(b'\x89PNG')
    
    def test_generate_waveform_image_empty_data(self, audio_processor):
        """Test waveform generation with empty data"""
        empty_audio = np.array([])
        
        with pytest.raises(AudioProcessingError, match="Waveform generation failed"):
            audio_processor._generate_waveform_image(empty_audio, 44100)
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_audio_processing_error_creation(self):
        """Test custom exception creation"""
        error = AudioProcessingError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_audio_format_error_creation(self):
        """Test format error creation"""
        error = AudioFormatError("Unsupported format")
        assert str(error) == "Unsupported format"
        assert isinstance(error, AudioProcessingError)
    
    def test_audio_validation_error_creation(self):
        """Test validation error creation"""
        error = AudioValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, AudioProcessingError)
    
    def test_quality_analysis_error_handling(self, audio_processor):
        """Test error handling in quality analysis"""
        # Test with corrupted audio data
        corrupted_audio = np.array([np.nan, np.inf, -np.inf])
        
        # Quality analysis should handle corrupted data gracefully with warnings
        result = audio_processor.analyze_audio_quality("test.mp3", corrupted_audio, 44100)
        
        # Should return a result with default values for corrupted data
        assert 'quality_score' in result
        assert 0.0 <= result['quality_score'] <= 1.0
    
    def test_peak_detection_error_handling(self, audio_processor):
        """Test error handling in peak detection"""
        # Test with corrupted audio data
        corrupted_audio = np.array([np.nan, np.inf, -np.inf])
        
        # Peak detection should handle corrupted data gracefully with warnings
        result = audio_processor.detect_peaks(corrupted_audio, 44100)
        
        # Should return a result with default values for corrupted data
        assert 'peaks' in result
        assert 'peak_statistics' in result
    
    # ==================== INTEGRATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_process_audio_file_integration(self, audio_processor, temp_audio_file, mock_file_uploader):
        """Test complete audio processing pipeline"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=temp_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0  # 10 minutes
            
            result = await audio_processor.process_audio_file("test.mp3", "test-session")
            
            # Verify result structure
            expected_fields = [
                'duration', 'original_duration', 'waveform_s3_key', 'sample_rate',
                'channels', 'rms_energy', 'peak_amplitude', 'dynamic_range',
                'tempo', 'zero_crossing_rate', 'file_size', 'mime_type', 'status',
                'quality_score', 'snr_db', 'advanced_trimming', 'peak_detection',
                'performance_stats'
            ]
            
            for field in expected_fields:
                assert field in result
            
            # Verify processing completed successfully
            assert result['status'] == 'completed'
            assert result['waveform_s3_key'] == "waveforms/test.png"
            assert result['duration'] > 0
            assert result['original_duration'] > 0
            
            # Verify advanced features are included
            assert 'method' in result['advanced_trimming']
            assert 'peak_statistics' in result['peak_detection']
            
            # Verify performance stats
            assert 'total_processing_time' in result['performance_stats']
            assert 'memory_used_mb' in result['performance_stats']
    
    @pytest.mark.asyncio
    async def test_process_audio_file_chunk_processing(self, audio_processor, temp_large_audio_file, mock_file_uploader):
        """Test audio processing with chunk processing"""
        # Mock the download and upload methods
        audio_processor._download_audio_file = AsyncMock(return_value=temp_large_audio_file)
        audio_processor._upload_waveform = AsyncMock(return_value="waveforms/test.png")
        
        # Mock settings
        with patch('backend.services.audio_processor.settings') as mock_settings:
            mock_settings.max_audio_duration = 600.0  # 10 minutes
            
            result = await audio_processor.process_audio_file("test.mp3", "test-session")
            
            # Verify chunk processing was used
            assert result['performance_stats']['chunk_processing_used'] is True
            assert result['processing_method'] == 'chunked'
            assert result['chunks_processed'] > 0
    
    @pytest.mark.asyncio
    async def test_process_audio_file_validation_error(self, audio_processor, temp_corrupted_audio_file, mock_file_uploader):
        """Test audio processing with validation error"""
        # Mock the download method
        audio_processor._download_audio_file = AsyncMock(return_value=temp_corrupted_audio_file)
        
        with pytest.raises(Exception):  # Should raise HTTPException from FastAPI
            await audio_processor.process_audio_file("test.mp3", "test-session")
    
    # ==================== PERFORMANCE TESTS ====================
    
    def test_performance_stats_tracking(self, audio_processor, sample_audio_data):
        """Test performance statistics tracking"""
        audio_data, sample_rate = sample_audio_data
        
        # Generate waveform to trigger performance tracking
        waveform_buffer = audio_processor._generate_waveform_image(audio_data, sample_rate)
        
        # Verify performance stats are tracked
        assert 'processing_times' in audio_processor.performance_stats
        assert 'waveform_generation' in audio_processor.performance_stats['processing_times']
        
        processing_time = audio_processor.performance_stats['processing_times']['waveform_generation']
        assert isinstance(processing_time, float)
        assert processing_time > 0.0
    
    def test_memory_usage_tracking(self, audio_processor):
        """Test memory usage tracking"""
        initial_memory = audio_processor._monitor_memory_usage()
        
        # Perform some operations
        audio_processor._force_garbage_collection()
        
        final_memory = audio_processor._monitor_memory_usage()
        
        # Memory usage should be tracked (may vary due to garbage collection)
        assert isinstance(initial_memory, float)
        assert isinstance(final_memory, float)
        assert initial_memory >= 0.0
        assert final_memory >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
