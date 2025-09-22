"""
Test suite for advanced audio processing features
Tests the new advanced silence trimming and peak detection functionality
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import patch, MagicMock

from backend.services.audio_processor import AudioProcessor, AudioProcessingError
from backend.services.file_uploader import FileUploader


class TestAdvancedAudioFeatures:
    """Test class for advanced audio processing features"""
    
    @pytest.fixture
    def audio_processor(self):
        """Create AudioProcessor instance for testing"""
        processor = AudioProcessor()
        return processor
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing"""
        # Create a 2-second audio signal with some silence and peaks
        sample_rate = 44100
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create audio with silence at beginning and end, and peaks in the middle
        audio_data = np.zeros_like(t)
        
        # Add silence at beginning (0.2s)
        # Add peaks in middle (0.2s - 1.8s)
        middle_start = int(0.2 * sample_rate)
        middle_end = int(1.8 * sample_rate)
        
        # Add sinusoidal peaks
        audio_data[middle_start:middle_end] = 0.5 * np.sin(2 * np.pi * 440 * t[middle_start:middle_end])
        audio_data[middle_start:middle_end] += 0.3 * np.sin(2 * np.pi * 880 * t[middle_start:middle_end])
        
        # Add some random peaks
        peak_indices = np.random.choice(
            np.arange(middle_start, middle_end, 1000), 
            size=5, 
            replace=False
        )
        for idx in peak_indices:
            audio_data[idx:idx+100] = 0.8 * np.sin(2 * np.pi * 1000 * t[idx:idx+100])
        
        # Add silence at end (1.8s - 2.0s)
        
        return audio_data, sample_rate
    
    def test_advanced_silence_trimming_dynamic(self, audio_processor, sample_audio_data):
        """Test dynamic silence trimming method"""
        audio_data, sample_rate = sample_audio_data
        
        # Test dynamic trimming
        trimmed_audio, trimming_info = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, trim_method='dynamic'
        )
        
        # Verify trimming results
        assert isinstance(trimmed_audio, np.ndarray)
        assert len(trimmed_audio) < len(audio_data)  # Should be shorter due to silence removal
        assert trimming_info['method'] == 'dynamic'
        assert 'threshold_db' in trimming_info
        assert 'original_duration' in trimming_info
        assert 'trimmed_duration' in trimming_info
        assert 'silence_removed' in trimming_info
        assert 'silence_percentage' in trimming_info
        assert trimming_info['silence_percentage'] > 0  # Should have removed some silence
    
    def test_advanced_silence_trimming_split(self, audio_processor, sample_audio_data):
        """Test split-based silence trimming method"""
        audio_data, sample_rate = sample_audio_data
        
        # Test split-based trimming
        trimmed_audio, trimming_info = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, trim_method='split'
        )
        
        # Verify trimming results
        assert isinstance(trimmed_audio, np.ndarray)
        assert trimming_info['method'] == 'split'
        assert 'intervals_found' in trimming_info
        assert 'interval_details' in trimming_info
        assert len(trimming_info['interval_details']) > 0
    
    def test_advanced_silence_trimming_segment(self, audio_processor, sample_audio_data):
        """Test segment-based silence trimming method"""
        audio_data, sample_rate = sample_audio_data
        
        # Test segment-based trimming
        trimmed_audio, trimming_info = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, trim_method='segment'
        )
        
        # Verify trimming results
        assert isinstance(trimmed_audio, np.ndarray)
        assert trimming_info['method'] == 'segment'
        assert 'segments_processed' in trimming_info
        assert 'segments_kept' in trimming_info
        assert 'segment_details' in trimming_info
        assert trimming_info['segments_kept'] <= trimming_info['segments_processed']
    
    def test_advanced_silence_trimming_adaptive(self, audio_processor, sample_audio_data):
        """Test adaptive silence trimming method"""
        audio_data, sample_rate = sample_audio_data
        
        # Test adaptive trimming
        trimmed_audio, trimming_info = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, trim_method='adaptive'
        )
        
        # Verify trimming results
        assert isinstance(trimmed_audio, np.ndarray)
        assert trimming_info['method'].startswith('adaptive')
        assert 'original_duration' in trimming_info
        assert 'trimmed_duration' in trimming_info
    
    def test_detect_peaks_onset(self, audio_processor, sample_audio_data):
        """Test onset peak detection"""
        audio_data, sample_rate = sample_audio_data
        
        # Test onset peak detection
        peak_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['onset']
        )
        
        # Verify peak detection results
        assert 'onset_peaks' in peak_results
        assert 'peak_statistics' in peak_results
        assert peak_results['peak_detection_methods'] == ['onset']
        assert 'onset_count' in peak_results['onset_peaks']
        assert peak_results['peak_statistics']['total_peaks_detected'] >= 0
    
    def test_detect_peaks_spectral(self, audio_processor, sample_audio_data):
        """Test spectral peak detection"""
        audio_data, sample_rate = sample_audio_data
        
        # Test spectral peak detection
        peak_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['spectral']
        )
        
        # Verify peak detection results
        assert 'spectral_peaks' in peak_results
        assert 'peak_statistics' in peak_results
        assert peak_results['peak_detection_methods'] == ['spectral']
        assert 'mel_peak_count' in peak_results['spectral_peaks']
        assert 'chroma_peak_count' in peak_results['spectral_peaks']
    
    def test_detect_peaks_envelope(self, audio_processor, sample_audio_data):
        """Test envelope peak detection"""
        audio_data, sample_rate = sample_audio_data
        
        # Test envelope peak detection
        peak_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['envelope']
        )
        
        # Verify peak detection results
        assert 'envelope_peaks' in peak_results
        assert 'peak_statistics' in peak_results
        assert peak_results['peak_detection_methods'] == ['envelope']
        assert 'peak_count' in peak_results['envelope_peaks']
        assert 'peak_times' in peak_results['envelope_peaks']
        assert 'peak_amplitudes' in peak_results['envelope_peaks']
    
    def test_detect_peaks_all_types(self, audio_processor, sample_audio_data):
        """Test comprehensive peak detection with all types"""
        audio_data, sample_rate = sample_audio_data
        
        # Test all peak detection types
        peak_results = audio_processor.detect_peaks(
            audio_data, sample_rate, peak_types=['onset', 'spectral', 'envelope']
        )
        
        # Verify comprehensive peak detection results
        assert 'onset_peaks' in peak_results
        assert 'spectral_peaks' in peak_results
        assert 'envelope_peaks' in peak_results
        assert 'peak_statistics' in peak_results
        assert len(peak_results['peak_detection_methods']) == 3
        
        # Verify peak statistics
        stats = peak_results['peak_statistics']
        assert 'total_peaks_detected' in stats
        assert 'peak_types' in stats
        assert 'peak_density' in stats
        assert 'dominant_peak_type' in stats
        assert len(stats['peak_types']) >= 0
    
    def test_advanced_silence_trimming_error_handling(self, audio_processor):
        """Test error handling in advanced silence trimming"""
        # Test with empty audio data
        empty_audio = np.array([])
        
        with pytest.raises(AudioProcessingError):
            audio_processor.advanced_silence_trimming(empty_audio, 44100)
    
    def test_detect_peaks_error_handling(self, audio_processor):
        """Test error handling in peak detection"""
        # Test with empty audio data
        empty_audio = np.array([])
        
        with pytest.raises(AudioProcessingError):
            audio_processor.detect_peaks(empty_audio, 44100)
    
    def test_integration_with_main_pipeline(self, audio_processor, sample_audio_data):
        """Test integration of new features with main processing pipeline"""
        audio_data, sample_rate = sample_audio_data
        
        # Test that the new features can be called without errors
        # This simulates the integration in the main process_audio_file method
        
        # Apply advanced silence trimming
        y_trimmed, trimming_info = audio_processor.advanced_silence_trimming(
            audio_data, sample_rate, trim_method='adaptive'
        )
        
        # Detect peaks
        peak_results = audio_processor.detect_peaks(
            y_trimmed, sample_rate, peak_types=['onset', 'spectral', 'envelope']
        )
        
        # Verify integration works
        assert isinstance(y_trimmed, np.ndarray)
        assert isinstance(trimming_info, dict)
        assert isinstance(peak_results, dict)
        assert 'advanced_trimming' not in peak_results  # Should be separate
        assert 'peak_detection' not in trimming_info  # Should be separate
        
        # Verify the results can be used together
        assert len(y_trimmed) > 0
        assert peak_results['duration'] > 0
        assert trimming_info['trimmed_duration'] > 0


if __name__ == "__main__":
    pytest.main([__file__])
