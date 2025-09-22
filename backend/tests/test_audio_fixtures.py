"""
Audio test fixtures and utilities for comprehensive testing
Provides reusable fixtures for different audio scenarios and test data
"""

import pytest
import numpy as np
import tempfile
import os
import io
import wave
import struct
from typing import Tuple, List, Dict, Any


class AudioTestFixtures:
    """Collection of audio test fixtures and utilities"""
    
    @staticmethod
    def create_sine_wave(frequency: float, duration: float, sample_rate: int = 44100, amplitude: float = 0.5) -> np.ndarray:
        """Create a sine wave audio signal"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        return amplitude * np.sin(2 * np.pi * frequency * t)
    
    @staticmethod
    def create_complex_audio(duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Create complex audio with multiple frequencies and characteristics"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Base signal with multiple frequencies
        audio = 0.3 * np.sin(2 * np.pi * 440 * t)  # A4
        audio += 0.2 * np.sin(2 * np.pi * 880 * t)  # A5
        audio += 0.1 * np.sin(2 * np.pi * 1320 * t)  # E6
        
        # Add some harmonics
        audio += 0.05 * np.sin(2 * np.pi * 220 * t)  # A3
        audio += 0.05 * np.sin(2 * np.pi * 1760 * t)  # A6
        
        # Add some noise
        noise = np.random.normal(0, 0.01, len(t))
        audio += noise
        
        return audio
    
    @staticmethod
    def create_audio_with_silence(duration: float, sample_rate: int = 44100, 
                                 silence_start: float = 0.2, silence_end: float = 0.4) -> np.ndarray:
        """Create audio with silence periods"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.zeros_like(t)
        
        # Add content before silence
        if silence_start > 0:
            start_idx = 0
            end_idx = int(silence_start * sample_rate)
            audio[start_idx:end_idx] = 0.5 * np.sin(2 * np.pi * 440 * t[start_idx:end_idx])
        
        # Add content after silence
        if silence_end < duration:
            start_idx = int(silence_end * sample_rate)
            end_idx = len(audio)
            audio[start_idx:end_idx] = 0.5 * np.sin(2 * np.pi * 440 * t[start_idx:end_idx])
        
        return audio
    
    @staticmethod
    def create_audio_with_peaks(duration: float, sample_rate: int = 44100, 
                               num_peaks: int = 5) -> np.ndarray:
        """Create audio with distinct peaks"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.zeros_like(t)
        
        # Add base signal
        audio += 0.2 * np.sin(2 * np.pi * 440 * t)
        
        # Add distinct peaks
        peak_positions = np.linspace(0.1, duration - 0.1, num_peaks)
        for peak_pos in peak_positions:
            peak_idx = int(peak_pos * sample_rate)
            peak_width = int(0.05 * sample_rate)  # 50ms peak
            start_idx = max(0, peak_idx - peak_width // 2)
            end_idx = min(len(audio), peak_idx + peak_width // 2)
            
            # Create peak with higher frequency
            peak_t = t[start_idx:end_idx]
            audio[start_idx:end_idx] += 0.8 * np.sin(2 * np.pi * 1000 * peak_t)
        
        return audio
    
    @staticmethod
    def create_corrupted_audio(duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Create corrupted audio with NaN and infinite values"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Introduce corruption
        audio[1000:1100] = np.nan
        audio[2000:2100] = np.inf
        audio[3000:3100] = -np.inf
        
        return audio
    
    @staticmethod
    def create_low_quality_audio(duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Create low quality audio with high noise"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Weak signal
        signal = 0.1 * np.sin(2 * np.pi * 440 * t)
        
        # High noise
        noise = np.random.normal(0, 0.2, len(t))
        
        return signal + noise
    
    @staticmethod
    def create_high_quality_audio(duration: float, sample_rate: int = 44100) -> np.ndarray:
        """Create high quality audio with clean signal"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Strong, clean signal with multiple frequencies
        audio = 0.8 * np.sin(2 * np.pi * 440 * t)
        audio += 0.6 * np.sin(2 * np.pi * 880 * t)
        audio += 0.4 * np.sin(2 * np.pi * 1320 * t)
        
        # Minimal noise
        noise = np.random.normal(0, 0.001, len(t))
        audio += noise
        
        return audio
    
    @staticmethod
    def write_wav_file(audio_data: np.ndarray, sample_rate: int, filename: str) -> str:
        """Write audio data to WAV file using soundfile"""
        import soundfile as sf
        
        # Normalize audio data to prevent clipping
        audio_data = np.clip(audio_data, -1.0, 1.0)
        
        # Write using soundfile for proper WAV format
        sf.write(filename, audio_data, sample_rate, format='WAV', subtype='PCM_16')
        
        return filename
    
    @staticmethod
    def create_temp_audio_file(audio_data: np.ndarray, sample_rate: int, 
                              suffix: str = '.wav') -> str:
        """Create temporary audio file"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.close()
        
        AudioTestFixtures.write_wav_file(audio_data, sample_rate, temp_file.name)
        return temp_file.name


# Pytest fixtures for common audio test scenarios
@pytest.fixture
def audio_fixtures():
    """Provide access to AudioTestFixtures class"""
    return AudioTestFixtures


@pytest.fixture
def sample_audio_data(audio_fixtures):
    """Create sample audio data for testing"""
    return audio_fixtures.create_complex_audio(2.0, 44100), 44100


@pytest.fixture
def large_audio_data(audio_fixtures):
    """Create large audio data for chunk processing tests"""
    return audio_fixtures.create_complex_audio(300.0, 44100), 44100  # 5 minutes


@pytest.fixture
def audio_with_silence(audio_fixtures):
    """Create audio with silence periods"""
    return audio_fixtures.create_audio_with_silence(3.0, 44100, 0.5, 1.0), 44100


@pytest.fixture
def audio_with_peaks(audio_fixtures):
    """Create audio with distinct peaks"""
    return audio_fixtures.create_audio_with_peaks(2.0, 44100, 5), 44100


@pytest.fixture
def corrupted_audio_data(audio_fixtures):
    """Create corrupted audio data"""
    return audio_fixtures.create_corrupted_audio(1.0, 44100), 44100


@pytest.fixture
def low_quality_audio(audio_fixtures):
    """Create low quality audio"""
    return audio_fixtures.create_low_quality_audio(2.0, 44100), 44100


@pytest.fixture
def high_quality_audio(audio_fixtures):
    """Create high quality audio"""
    return audio_fixtures.create_high_quality_audio(2.0, 44100), 44100


@pytest.fixture
def temp_audio_file(sample_audio_data, audio_fixtures):
    """Create temporary audio file"""
    audio_data, sample_rate = sample_audio_data
    temp_file = audio_fixtures.create_temp_audio_file(audio_data, sample_rate)
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_large_audio_file(large_audio_data, audio_fixtures):
    """Create temporary large audio file"""
    audio_data, sample_rate = large_audio_data
    temp_file = audio_fixtures.create_temp_audio_file(audio_data, sample_rate)
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_corrupted_audio_file(corrupted_audio_data, audio_fixtures):
    """Create temporary corrupted audio file"""
    audio_data, sample_rate = corrupted_audio_data
    temp_file = audio_fixtures.create_temp_audio_file(audio_data, sample_rate)
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_low_quality_audio_file(low_quality_audio, audio_fixtures):
    """Create temporary low quality audio file"""
    audio_data, sample_rate = low_quality_audio
    temp_file = audio_fixtures.create_temp_audio_file(audio_data, sample_rate)
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def temp_high_quality_audio_file(high_quality_audio, audio_fixtures):
    """Create temporary high quality audio file"""
    audio_data, sample_rate = high_quality_audio
    temp_file = audio_fixtures.create_temp_audio_file(audio_data, sample_rate)
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Create data for performance testing"""
    return {
        'small_file': (1.0, 44100),  # 1 second
        'medium_file': (30.0, 44100),  # 30 seconds
        'large_file': (300.0, 44100),  # 5 minutes
        'very_large_file': (1800.0, 44100),  # 30 minutes
    }


# Error scenario fixtures
@pytest.fixture
def error_scenarios():
    """Create various error scenarios for testing"""
    return {
        'empty_file': b'',
        'corrupted_header': b'RIFF\x00\x00\x00\x00WAVE',
        'invalid_format': b'INVALID_AUDIO_DATA',
        'too_large': b'0' * (100 * 1024 * 1024 + 1),  # > 100MB
        'zero_size': b'',
    }


# Mock fixtures for external dependencies
@pytest.fixture
def mock_s3_operations():
    """Mock S3 operations for testing"""
    from unittest.mock import MagicMock
    
    mock_s3 = MagicMock()
    mock_s3.upload_fileobj.return_value = None
    mock_s3.download_fileobj.return_value = None
    mock_s3.generate_presigned_url.return_value = "https://example.com/test-url"
    mock_s3.head_object.return_value = {"ContentLength": 1024}
    mock_s3.list_objects_v2.return_value = {"Contents": []}
    mock_s3.delete_object.return_value = None
    
    return mock_s3


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing"""
    from unittest.mock import patch, MagicMock
    
    with patch('os.path.exists') as mock_exists, \
         patch('os.path.getsize') as mock_getsize, \
         patch('os.unlink') as mock_unlink:
        
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 * 1024  # 1MB
        mock_unlink.return_value = None
        
        yield {
            'exists': mock_exists,
            'getsize': mock_getsize,
            'unlink': mock_unlink
        }


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_audio_formats() -> List[Dict[str, Any]]:
        """Generate test data for different audio formats"""
        return [
            {'format': 'mp3', 'mime_type': 'audio/mpeg', 'extension': '.mp3'},
            {'format': 'wav', 'mime_type': 'audio/wav', 'extension': '.wav'},
            {'format': 'm4a', 'mime_type': 'audio/mp4', 'extension': '.m4a'},
            {'format': 'aac', 'mime_type': 'audio/aac', 'extension': '.aac'},
            {'format': 'ogg', 'mime_type': 'audio/ogg', 'extension': '.ogg'},
            {'format': 'flac', 'mime_type': 'audio/flac', 'extension': '.flac'},
        ]
    
    @staticmethod
    def generate_sample_rates() -> List[int]:
        """Generate test data for different sample rates"""
        return [8000, 16000, 22050, 44100, 48000, 96000, 192000]
    
    @staticmethod
    def generate_durations() -> List[float]:
        """Generate test data for different durations"""
        return [0.1, 1.0, 10.0, 60.0, 300.0, 600.0, 1800.0]  # 0.1s to 30min
    
    @staticmethod
    def generate_file_sizes() -> List[int]:
        """Generate test data for different file sizes"""
        return [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            10 * 1024 * 1024,  # 10MB
            50 * 1024 * 1024,  # 50MB
            100 * 1024 * 1024,  # 100MB
        ]


@pytest.fixture
def test_data_generator():
    """Provide access to TestDataGenerator class"""
    return TestDataGenerator


# Parametrized test fixtures
@pytest.fixture(params=TestDataGenerator.generate_audio_formats())
def audio_format_data(request):
    """Parametrized fixture for different audio formats"""
    return request.param


@pytest.fixture(params=TestDataGenerator.generate_sample_rates())
def sample_rate_data(request):
    """Parametrized fixture for different sample rates"""
    return request.param


@pytest.fixture(params=TestDataGenerator.generate_durations())
def duration_data(request):
    """Parametrized fixture for different durations"""
    return request.param


@pytest.fixture(params=TestDataGenerator.generate_file_sizes())
def file_size_data(request):
    """Parametrized fixture for different file sizes"""
    return request.param
