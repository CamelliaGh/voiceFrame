import librosa
import matplotlib
import numpy as np

matplotlib.use("Agg")  # Non-interactive backend
import gc
import logging
import mimetypes
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import psutil
from fastapi import HTTPException

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available - bitrate detection will be limited")

try:
    from scipy.ndimage import gaussian_filter1d

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning(
        "scipy not available - envelope peak detection will use alternative method"
    )

from ..config import settings
from .file_uploader import FileUploader

# Configure logging
logger = logging.getLogger(__name__)

# Supported audio formats and their MIME types
SUPPORTED_AUDIO_FORMATS = {
    "audio/mpeg": [".mp3"],
    "audio/wav": [".wav"],
    "audio/x-wav": [".wav"],
    "audio/mp4": [".m4a", ".mp4"],
    "audio/aac": [".aac"],
    "audio/ogg": [".ogg"],
    "audio/flac": [".flac"],
    "audio/x-flac": [".flac"],
    "audio/webm": [".webm"],
}

# Maximum file size in bytes (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# Performance optimization constants
CHUNK_SIZE_SECONDS = 30  # Process audio in 30-second chunks
MAX_MEMORY_USAGE_MB = 500  # Maximum memory usage threshold
WAVEFORM_MAX_SAMPLES = 2400  # Maximum samples for waveform generation (2 samples per pixel for 1200px width)
PARALLEL_WORKERS = 4  # Number of parallel workers for processing


class AudioProcessingError(Exception):
    """Custom exception for audio processing errors"""

    pass


class AudioFormatError(AudioProcessingError):
    """Exception for unsupported audio formats"""

    pass


class AudioValidationError(AudioProcessingError):
    """Exception for audio validation failures"""

    pass


class AudioProcessor:
    """Processes audio files and generates waveform visualizations"""

    def __init__(self):
        self.file_uploader = FileUploader()
        self.supported_formats = SUPPORTED_AUDIO_FORMATS
        self.max_file_size = MAX_FILE_SIZE
        self.performance_stats = {
            "processing_times": {},
            "memory_usage": {},
            "chunk_processing": False,
        }

    def _monitor_memory_usage(self) -> float:
        """Monitor current memory usage in MB"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb
        except Exception:
            return 0.0

    def _check_memory_threshold(self) -> bool:
        """Check if memory usage exceeds threshold"""
        current_memory = self._monitor_memory_usage()
        return current_memory > MAX_MEMORY_USAGE_MB

    def _force_garbage_collection(self):
        """Force garbage collection to free memory"""
        try:
            gc.collect()
            logger.debug("Garbage collection performed")
        except Exception as e:
            logger.warning(f"Garbage collection failed: {str(e)}")

    def _optimize_audio_data_type(self, audio_data: np.ndarray) -> np.ndarray:
        """Convert audio data to float32 for memory efficiency"""
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
            logger.debug("Converted audio data to float32 for memory efficiency")
        return audio_data

    def _should_use_chunk_processing(self, duration: float, file_size: int) -> bool:
        """Determine if chunk-based processing should be used"""
        # Use chunk processing for files longer than 2 minutes or larger than 50MB
        return duration > 120 or file_size > 50 * 1024 * 1024

    def _process_audio_in_chunks(
        self, file_path: str, sample_rate: int
    ) -> Dict[str, any]:
        """Process large audio files in chunks for memory efficiency"""
        try:
            logger.info(f"Processing audio in chunks: {file_path}")
            self.performance_stats["chunk_processing"] = True

            # Load audio metadata first
            y_full, sr = librosa.load(file_path, sr=sample_rate, duration=1.0)
            duration = librosa.get_duration(filename=file_path)

            chunk_size_samples = int(CHUNK_SIZE_SECONDS * sr)
            num_chunks = int(np.ceil(duration / CHUNK_SIZE_SECONDS))

            logger.info(f"Processing {num_chunks} chunks of {CHUNK_SIZE_SECONDS}s each")

            # Initialize aggregated results
            aggregated_metrics = {
                "duration": duration,
                "sample_rate": sr,
                "chunks_processed": 0,
                "chunk_results": [],
            }

            # Process each chunk
            for chunk_idx in range(num_chunks):
                start_time = chunk_idx * CHUNK_SIZE_SECONDS
                end_time = min((chunk_idx + 1) * CHUNK_SIZE_SECONDS, duration)

                logger.debug(
                    f"Processing chunk {chunk_idx + 1}/{num_chunks}: {start_time:.1f}s - {end_time:.1f}s"
                )

                # Load chunk
                y_chunk, _ = librosa.load(
                    file_path, sr=sr, offset=start_time, duration=end_time - start_time
                )

                # Optimize data type
                y_chunk = self._optimize_audio_data_type(y_chunk)

                # Process chunk
                chunk_metrics = self._process_audio_chunk(y_chunk, sr, chunk_idx)
                aggregated_metrics["chunk_results"].append(chunk_metrics)
                aggregated_metrics["chunks_processed"] += 1

                # Force garbage collection after each chunk
                del y_chunk
                self._force_garbage_collection()

                # Check memory usage
                if self._check_memory_threshold():
                    logger.warning("Memory threshold exceeded, forcing cleanup")
                    self._force_garbage_collection()

            # Aggregate results from all chunks
            final_metrics = self._aggregate_chunk_results(aggregated_metrics)

            logger.info(
                f"Chunk processing completed: {aggregated_metrics['chunks_processed']} chunks"
            )
            return final_metrics

        except Exception as e:
            logger.error(f"Chunk processing failed: {str(e)}")
            raise AudioProcessingError(f"Chunk processing failed: {str(e)}")

    def _process_audio_chunk(
        self, audio_data: np.ndarray, sample_rate: int, chunk_idx: int
    ) -> Dict[str, any]:
        """Process a single audio chunk"""
        try:
            # Basic chunk metrics
            chunk_metrics = {
                "chunk_index": chunk_idx,
                "duration": len(audio_data) / sample_rate,
                "samples": len(audio_data),
                "rms_energy": float(np.sqrt(np.mean(audio_data**2))),
                "peak_amplitude": float(np.max(np.abs(audio_data))),
            }

            # Add spectral features for this chunk
            if len(audio_data) > 1024:  # Only if chunk is large enough
                try:
                    spectral_centroid = librosa.feature.spectral_centroid(
                        y=audio_data, sr=sample_rate
                    )[0]
                    chunk_metrics["spectral_centroid"] = float(
                        np.mean(spectral_centroid)
                    )

                    zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
                    chunk_metrics["zero_crossing_rate"] = float(np.mean(zcr))
                except Exception as e:
                    logger.warning(
                        f"Spectral analysis failed for chunk {chunk_idx}: {str(e)}"
                    )

            return chunk_metrics

        except Exception as e:
            logger.error(f"Chunk processing failed for chunk {chunk_idx}: {str(e)}")
            return {"chunk_index": chunk_idx, "error": str(e)}

    def _aggregate_chunk_results(
        self, aggregated_metrics: Dict[str, any]
    ) -> Dict[str, any]:
        """Aggregate results from all chunks into final metrics"""
        try:
            chunk_results = aggregated_metrics["chunk_results"]

            # Calculate aggregated metrics
            total_duration = aggregated_metrics["duration"]
            sample_rate = aggregated_metrics["sample_rate"]

            # Aggregate RMS energy (weighted by duration)
            total_rms = 0.0
            total_peak = 0.0
            total_spectral_centroid = 0.0
            total_zcr = 0.0
            valid_chunks = 0

            for chunk in chunk_results:
                if "error" not in chunk:
                    chunk_duration = chunk["duration"]
                    weight = chunk_duration / total_duration

                    total_rms += chunk["rms_energy"] * weight
                    total_peak = max(total_peak, chunk["peak_amplitude"])

                    if "spectral_centroid" in chunk:
                        total_spectral_centroid += chunk["spectral_centroid"] * weight
                    if "zero_crossing_rate" in chunk:
                        total_zcr += chunk["zero_crossing_rate"] * weight

                    valid_chunks += 1

            # Build final metrics
            final_metrics = {
                "duration": total_duration,
                "sample_rate": sample_rate,
                "chunks_processed": valid_chunks,
                "rms_energy": total_rms,
                "peak_amplitude": total_peak,
                "dynamic_range": 20 * np.log10(total_peak / (total_rms + 1e-10))
                if total_rms > 0
                else 0,
                "avg_spectral_centroid": total_spectral_centroid
                if valid_chunks > 0
                else 0,
                "zero_crossing_rate": total_zcr if valid_chunks > 0 else 0,
                "processing_method": "chunked",
            }

            return final_metrics

        except Exception as e:
            logger.error(f"Chunk aggregation failed: {str(e)}")
            raise AudioProcessingError(f"Chunk aggregation failed: {str(e)}")

    def validate_audio_file(self, file_path: str) -> Dict[str, any]:
        """
        Validate audio file format, size, and basic properties

        Args:
            file_path: Path to the audio file

        Returns:
            Dict containing validation results and metadata

        Raises:
            AudioFormatError: If file format is not supported
            AudioValidationError: If file validation fails
        """
        try:
            logger.info(f"Validating audio file: {file_path}")

            # Check if file exists
            if not os.path.exists(file_path):
                raise AudioValidationError(f"File does not exist: {file_path}")

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise AudioValidationError(
                    f"File too large: {file_size} bytes (max: {self.max_file_size} bytes)"
                )

            if file_size == 0:
                raise AudioValidationError("File is empty")

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type or not mime_type.startswith("audio/"):
                # Try to detect by extension
                file_ext = Path(file_path).suffix.lower()
                mime_type = self._get_mime_type_by_extension(file_ext)
                if not mime_type:
                    raise AudioFormatError(f"Unsupported file format: {file_ext}")

            # Validate format is supported
            if mime_type not in self.supported_formats:
                raise AudioFormatError(f"Unsupported audio format: {mime_type}")

            # Try to load with librosa to validate audio content
            try:
                y, sr = librosa.load(
                    file_path, sr=None, duration=1.0
                )  # Load only first second for validation
                duration = len(y) / sr if sr > 0 else 0

                if duration == 0:
                    raise AudioValidationError("Audio file has no content")

                if sr < 8000:  # Minimum sample rate
                    raise AudioValidationError(
                        f"Sample rate too low: {sr} Hz (minimum: 8000 Hz)"
                    )

                if sr > 192000:  # Maximum sample rate
                    raise AudioValidationError(
                        f"Sample rate too high: {sr} Hz (maximum: 192000 Hz)"
                    )

            except Exception as e:
                if isinstance(e, (AudioValidationError, AudioFormatError)):
                    raise
                raise AudioValidationError(f"Invalid audio content: {str(e)}")

            validation_result = {
                "valid": True,
                "file_size": file_size,
                "mime_type": mime_type,
                "sample_rate": sr,
                "duration": duration,
                "channels": 1 if len(y.shape) == 1 else y.shape[0],
            }

            logger.info(f"Audio file validation successful: {validation_result}")
            return validation_result

        except (AudioFormatError, AudioValidationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during audio validation: {str(e)}")
            raise AudioValidationError(f"Validation failed: {str(e)}")

    def _get_mime_type_by_extension(self, extension: str) -> Optional[str]:
        """Get MIME type by file extension"""
        for mime_type, extensions in self.supported_formats.items():
            if extension in extensions:
                return mime_type
        return None

    def extract_audio_metadata(self, file_path: str) -> Dict[str, any]:
        """
        Extract comprehensive audio metadata

        Args:
            file_path: Path to the audio file

        Returns:
            Dict containing audio metadata
        """
        try:
            logger.info(f"Extracting metadata from: {file_path}")

            # Load audio file
            y, sr = librosa.load(file_path, sr=None)

            # Basic metadata
            duration = len(y) / sr
            channels = 1 if len(y.shape) == 1 else y.shape[0]

            # Audio quality metrics
            rms_energy = np.sqrt(np.mean(y**2))
            peak_amplitude = np.max(np.abs(y))
            dynamic_range = 20 * np.log10(peak_amplitude / (rms_energy + 1e-10))

            # Spectral analysis
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            avg_spectral_centroid = np.mean(spectral_centroids)

            # Tempo analysis
            try:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            except:
                tempo = 0.0

            # Zero crossing rate (indicator of noisiness)
            zcr = np.mean(librosa.feature.zero_crossing_rate(y)[0])

            metadata = {
                "duration": float(duration),
                "sample_rate": int(sr),
                "channels": int(channels),
                "rms_energy": float(rms_energy),
                "peak_amplitude": float(peak_amplitude),
                "dynamic_range": float(dynamic_range),
                "avg_spectral_centroid": float(avg_spectral_centroid),
                "tempo": float(tempo),
                "zero_crossing_rate": float(zcr),
                "file_size": os.path.getsize(file_path),
            }

            logger.info(f"Metadata extraction completed: {len(metadata)} fields")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting audio metadata: {str(e)}")
            raise AudioProcessingError(f"Metadata extraction failed: {str(e)}")

    def analyze_audio_quality(
        self, file_path: str, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """
        Comprehensive audio quality analysis

        Args:
            file_path: Path to the audio file
            audio_data: Audio data array
            sample_rate: Sample rate of the audio

        Returns:
            Dict containing comprehensive quality metrics
        """
        try:
            logger.info(f"Analyzing audio quality for: {file_path}")

            quality_metrics = {}

            # 1. Bitrate analysis
            quality_metrics.update(self._analyze_bitrate(file_path))

            # 2. Signal-to-Noise Ratio (SNR)
            quality_metrics["snr_db"] = self._calculate_snr(audio_data, sample_rate)

            # 3. Spectral analysis
            quality_metrics.update(
                self._analyze_spectral_features(audio_data, sample_rate)
            )

            # 4. Voice activity detection for speech quality
            quality_metrics.update(
                self._analyze_voice_activity(audio_data, sample_rate)
            )

            # 5. Audio quality scoring
            quality_metrics["quality_score"] = self._calculate_quality_score(
                quality_metrics
            )

            # 6. Noise level analysis
            quality_metrics["noise_level"] = self._analyze_noise_level(
                audio_data, sample_rate
            )

            logger.info(
                f"Audio quality analysis completed: {len(quality_metrics)} metrics"
            )
            return quality_metrics

        except Exception as e:
            logger.error(f"Error in audio quality analysis: {str(e)}")
            raise AudioProcessingError(f"Quality analysis failed: {str(e)}")

    def _analyze_bitrate(self, file_path: str) -> Dict[str, any]:
        """Analyze bitrate and encoding quality"""
        try:
            if not PYDUB_AVAILABLE:
                return {"bitrate": None, "encoding_quality": "unknown"}

            audio_segment = AudioSegment.from_file(file_path)

            # Calculate bitrate
            bitrate = (
                audio_segment.frame_rate
                * audio_segment.frame_width
                * audio_segment.channels
                * 8
            )

            # Determine encoding quality based on bitrate
            if bitrate >= 320000:  # 320 kbps
                encoding_quality = "high"
            elif bitrate >= 192000:  # 192 kbps
                encoding_quality = "medium"
            elif bitrate >= 128000:  # 128 kbps
                encoding_quality = "standard"
            else:
                encoding_quality = "low"

            return {
                "bitrate": int(bitrate),
                "encoding_quality": encoding_quality,
                "frame_rate": audio_segment.frame_rate,
                "frame_width": audio_segment.frame_width,
                "channels": audio_segment.channels,
            }

        except Exception as e:
            logger.warning(f"Bitrate analysis failed: {str(e)}")
            return {"bitrate": None, "encoding_quality": "unknown"}

    def _calculate_snr(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate Signal-to-Noise Ratio"""
        try:
            # Assume first and last 10% of audio are noise (common assumption)
            noise_length = int(0.1 * len(audio_data))
            if noise_length == 0:
                noise_length = 1

            noise = np.concatenate(
                [audio_data[:noise_length], audio_data[-noise_length:]]
            )

            # Calculate power
            signal_power = np.mean(audio_data**2)
            noise_power = np.mean(noise**2)

            # Avoid division by zero
            if noise_power == 0:
                return float("inf")

            snr_db = 10 * np.log10(signal_power / noise_power)
            return float(snr_db)

        except Exception as e:
            logger.warning(f"SNR calculation failed: {str(e)}")
            return 0.0

    def _analyze_spectral_features(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """Analyze spectral features for audio quality assessment"""
        try:
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, sr=sample_rate
            )[0]
            avg_spectral_centroid = np.mean(spectral_centroids)

            # Spectral bandwidth (spectral spread)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(
                y=audio_data, sr=sample_rate
            )[0]
            avg_spectral_bandwidth = np.mean(spectral_bandwidth)

            # Spectral rolloff (frequency below which 85% of energy lies)
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=audio_data, sr=sample_rate
            )[0]
            avg_spectral_rolloff = np.mean(spectral_rolloff)

            # Spectral contrast (difference between peaks and valleys)
            spectral_contrast = librosa.feature.spectral_contrast(
                y=audio_data, sr=sample_rate
            )
            avg_spectral_contrast = np.mean(spectral_contrast)

            # MFCC features (first 13 coefficients)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            mfcc_means = np.mean(mfccs, axis=1)

            return {
                "spectral_centroid": float(avg_spectral_centroid),
                "spectral_bandwidth": float(avg_spectral_bandwidth),
                "spectral_rolloff": float(avg_spectral_rolloff),
                "spectral_contrast": float(avg_spectral_contrast),
                "mfcc_means": [
                    float(x) for x in mfcc_means[:5]
                ],  # First 5 MFCC coefficients
            }

        except Exception as e:
            logger.warning(f"Spectral analysis failed: {str(e)}")
            return {}

    def _analyze_voice_activity(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """Analyze voice activity and speech quality indicators"""
        try:
            # Zero crossing rate (indicator of speech vs music)
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            avg_zcr = np.mean(zcr)

            # RMS energy over time
            rms = librosa.feature.rms(y=audio_data)[0]
            avg_rms = np.mean(rms)
            rms_std = np.std(rms)

            # Estimate voice activity based on energy patterns
            # Higher energy variation often indicates speech
            energy_variation = rms_std / (avg_rms + 1e-10)

            # Classify as speech or music based on features
            is_speech_like = avg_zcr > 0.1 and energy_variation > 0.3

            return {
                "zero_crossing_rate": float(avg_zcr),
                "rms_energy_mean": float(avg_rms),
                "rms_energy_std": float(rms_std),
                "energy_variation": float(energy_variation),
                "is_speech_like": bool(is_speech_like),
                "voice_activity_score": float(min(1.0, energy_variation * 2)),
            }

        except Exception as e:
            logger.warning(f"Voice activity analysis failed: {str(e)}")
            return {}

    def _analyze_noise_level(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """Analyze noise level and characteristics"""
        try:
            # Calculate noise floor using quietest segments
            segment_length = int(0.1 * len(audio_data))  # 10% segments
            if segment_length == 0:
                segment_length = 1

            # Divide audio into segments and find quietest ones
            segments = []
            for i in range(0, len(audio_data) - segment_length, segment_length):
                segment = audio_data[i : i + segment_length]
                segments.append((np.mean(segment**2), segment))

            # Sort by energy and take quietest 20%
            segments.sort(key=lambda x: x[0])
            quiet_segments = segments[: max(1, len(segments) // 5)]

            # Estimate noise floor
            noise_floor = np.mean([seg[0] for seg in quiet_segments])

            # Calculate noise level relative to signal
            signal_energy = np.mean(audio_data**2)
            noise_ratio = noise_floor / (signal_energy + 1e-10)

            # Classify noise level
            if noise_ratio < 0.01:
                noise_level = "very_low"
            elif noise_ratio < 0.05:
                noise_level = "low"
            elif noise_ratio < 0.15:
                noise_level = "moderate"
            else:
                noise_level = "high"

            return {
                "noise_floor": float(noise_floor),
                "noise_ratio": float(noise_ratio),
                "noise_level": noise_level,
                "noise_score": float(min(1.0, noise_ratio * 10)),  # 0-1 scale
            }

        except Exception as e:
            logger.warning(f"Noise analysis failed: {str(e)}")
            return {"noise_level": "unknown", "noise_score": 0.0}

    def _calculate_quality_score(self, quality_metrics: Dict[str, any]) -> float:
        """Calculate overall audio quality score (0-1 scale)"""
        try:
            score = 0.0
            factors = 0

            # SNR contribution (0-0.3)
            if "snr_db" in quality_metrics:
                snr = quality_metrics["snr_db"]
                if snr > 20:
                    snr_score = 0.3
                elif snr > 10:
                    snr_score = 0.2
                elif snr > 0:
                    snr_score = 0.1
                else:
                    snr_score = 0.0
                score += snr_score
                factors += 1

            # Bitrate contribution (0-0.2)
            if "encoding_quality" in quality_metrics:
                quality = quality_metrics["encoding_quality"]
                if quality == "high":
                    bitrate_score = 0.2
                elif quality == "medium":
                    bitrate_score = 0.15
                elif quality == "standard":
                    bitrate_score = 0.1
                else:
                    bitrate_score = 0.05
                score += bitrate_score
                factors += 1

            # Noise level contribution (0-0.2)
            if "noise_score" in quality_metrics:
                noise_score = 0.2 * (1.0 - quality_metrics["noise_score"])
                score += noise_score
                factors += 1

            # Dynamic range contribution (0-0.15)
            if "dynamic_range" in quality_metrics:
                dr = quality_metrics["dynamic_range"]
                if dr > 40:
                    dr_score = 0.15
                elif dr > 20:
                    dr_score = 0.1
                elif dr > 10:
                    dr_score = 0.05
                else:
                    dr_score = 0.0
                score += dr_score
                factors += 1

            # Spectral richness contribution (0-0.15)
            if "spectral_bandwidth" in quality_metrics:
                bw = quality_metrics["spectral_bandwidth"]
                # Normalize bandwidth score (assuming max ~5000 Hz)
                bw_score = 0.15 * min(1.0, bw / 5000.0)
                score += bw_score
                factors += 1

            # Normalize by number of factors
            if factors > 0:
                score = score / factors

            return float(min(1.0, max(0.0, score)))

        except Exception as e:
            logger.warning(f"Quality score calculation failed: {str(e)}")
            return 0.5  # Default middle score

    async def process_audio_file(self, audio_s3_key: str, session_token: str) -> dict:
        """
        Process audio file from S3 and generate waveform
        Returns audio metadata and waveform S3 key
        """
        audio_path = None
        start_time = time.time()
        initial_memory = self._monitor_memory_usage()

        try:
            logger.info(
                f"Processing audio file: {audio_s3_key} for session: {session_token}"
            )
            logger.info(f"Initial memory usage: {initial_memory:.1f}MB")

            # Download audio file from S3/local storage
            download_start = time.time()
            audio_path = await self._download_audio_file(audio_s3_key)
            download_time = time.time() - download_start
            self.performance_stats["processing_times"]["download"] = download_time

            # Validate audio file before processing
            validation_result = self.validate_audio_file(audio_path)
            logger.info(f"Audio validation passed: {validation_result}")

            # Extract comprehensive metadata
            metadata = self.extract_audio_metadata(audio_path)
            logger.info(f"Audio metadata extracted: {len(metadata)} fields")

            # Validate audio duration against settings
            if metadata["duration"] > settings.max_audio_duration:
                raise AudioValidationError(
                    f"Audio too long: {metadata['duration']:.2f}s (max: {settings.max_audio_duration}s)"
                )

            # Determine processing method based on file size and duration
            file_size = os.path.getsize(audio_path)
            duration = metadata["duration"]

            if self._should_use_chunk_processing(duration, file_size):
                logger.info(
                    f"Using chunk-based processing for large file: {duration:.1f}s, {file_size/1024/1024:.1f}MB"
                )
                # Use chunk-based processing for large files
                chunk_metrics = self._process_audio_in_chunks(audio_path, 44100)

                # Load a representative sample for waveform generation
                y, sr = librosa.load(audio_path, sr=44100, duration=min(30, duration))
                y = self._optimize_audio_data_type(y)

                # Perform quality analysis on the sample
                quality_metrics = self.analyze_audio_quality(audio_path, y, sr)

                # Merge chunk metrics with quality metrics
                quality_metrics.update(chunk_metrics)
                quality_metrics["processing_method"] = "chunked"

            else:
                logger.info("Using standard processing for small file")
                # Load and process audio with optimized settings
                y, sr = librosa.load(audio_path, sr=44100)
                y = self._optimize_audio_data_type(y)

                # Perform comprehensive audio quality analysis
                quality_metrics = self.analyze_audio_quality(audio_path, y, sr)
                quality_metrics["processing_method"] = "standard"

            logger.info(
                f"Audio quality analysis completed: {len(quality_metrics)} metrics"
            )

            # Normalize audio
            y = librosa.util.normalize(y)

            # Apply advanced silence trimming
            trimming_start = time.time()
            y_trimmed, trimming_info = self.advanced_silence_trimming(
                y, sr, trim_method="adaptive"
            )
            trimming_time = time.time() - trimming_start
            self.performance_stats["processing_times"][
                "advanced_trimming"
            ] = trimming_time
            logger.info(f"Advanced silence trimming completed in {trimming_time:.2f}s")

            # Detect peaks in the audio
            peak_detection_start = time.time()
            peak_results = self.detect_peaks(
                y_trimmed, sr, peak_types=["onset", "spectral", "envelope"]
            )
            peak_detection_time = time.time() - peak_detection_start
            self.performance_stats["processing_times"][
                "peak_detection"
            ] = peak_detection_time
            logger.info(f"Peak detection completed in {peak_detection_time:.2f}s")

            # Generate waveform visualization
            waveform_buffer = self._generate_waveform_image(y_trimmed, sr)

            # Upload waveform to storage
            waveform_key = await self._upload_waveform(waveform_buffer, session_token)

            # Prepare result with comprehensive metadata and quality analysis
            result = {
                "duration": len(y_trimmed) / sr,
                "original_duration": metadata["duration"],
                "waveform_s3_key": waveform_key,
                "sample_rate": sr,
                "channels": metadata["channels"],
                "rms_energy": metadata["rms_energy"],
                "peak_amplitude": metadata["peak_amplitude"],
                "dynamic_range": metadata["dynamic_range"],
                "tempo": metadata["tempo"],
                "zero_crossing_rate": metadata["zero_crossing_rate"],
                "file_size": metadata["file_size"],
                "mime_type": validation_result["mime_type"],
                "status": "completed",
            }

            # Add quality analysis results
            result.update(quality_metrics)

            # Add advanced trimming information
            result["advanced_trimming"] = trimming_info

            # Add peak detection results
            result["peak_detection"] = peak_results

            # Add performance statistics
            total_time = time.time() - start_time
            final_memory = self._monitor_memory_usage()
            memory_used = final_memory - initial_memory

            result["performance_stats"] = {
                "total_processing_time": total_time,
                "memory_used_mb": memory_used,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "processing_times": self.performance_stats["processing_times"],
                "chunk_processing_used": self.performance_stats["chunk_processing"],
            }

            logger.info(
                f"Audio processing completed successfully for session: {session_token}"
            )
            logger.info(
                f"Total processing time: {total_time:.2f}s, Memory used: {memory_used:.1f}MB"
            )

            # Final cleanup
            self._force_garbage_collection()

            return result

        except (AudioFormatError, AudioValidationError, AudioProcessingError) as e:
            logger.error(f"Audio processing error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during audio processing: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Audio processing failed: {str(e)}"
            )
        finally:
            # Cleanup temporary files
            if (
                audio_path
                and os.path.exists(audio_path)
                and not audio_s3_key.startswith("temp_")
            ):
                try:
                    os.unlink(audio_path)
                    logger.debug(f"Cleaned up temporary file: {audio_path}")
                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup temporary file {audio_path}: {str(e)}"
                    )

    async def _download_audio_file(self, s3_key: str) -> str:
        """Download audio file to temporary location with enhanced error handling"""
        try:
            logger.info(f"Downloading audio file: {s3_key}")

            # First check if this is a local temporary file
            if s3_key.startswith("temp_"):
                from .storage_manager import StorageManager

                storage_manager = StorageManager()
                temp_path = storage_manager.get_temp_file_path(s3_key)
                if temp_path and os.path.exists(temp_path):
                    logger.info(f"Using local temp file: {temp_path}")
                    return temp_path
                else:
                    logger.warning(
                        f"Local temp file not found, will download from S3: {s3_key}"
                    )

            # Handle S3 files (both temporary and permanent)
            if self.file_uploader.s3_client:
                # Download from S3
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                try:
                    logger.debug(f"Downloading from S3: {settings.s3_bucket}/{s3_key}")
                    self.file_uploader.s3_client.download_fileobj(
                        settings.s3_bucket, s3_key, temp_file
                    )
                    temp_file.close()
                    logger.info(f"S3 download completed: {temp_file.name}")
                    return temp_file.name
                except Exception as e:
                    temp_file.close()
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                    logger.error(f"S3 download failed: {str(e)}")
                    raise AudioProcessingError(f"Failed to download from S3: {str(e)}")
            else:
                # Local storage
                local_path = os.path.join(self.file_uploader.local_storage_path, s3_key)
                if not os.path.exists(local_path):
                    logger.error(f"Local file not found: {local_path}")
                    raise AudioProcessingError(f"Audio file not found: {s3_key}")
                logger.info(f"Using local file: {local_path}")
                return local_path

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading audio file: {str(e)}")
            raise AudioProcessingError(f"Download failed: {str(e)}")

    def _generate_waveform_image(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        width: int = 1200,
        height: int = 200,
        color: str = "#000000",
        alpha: float = 0.3,
    ) -> BytesIO:
        """Generate waveform visualization as PNG image with enhanced performance"""
        try:
            start_time = time.time()
            logger.debug(
                f"Generating waveform: {len(audio_data)} samples, {sample_rate}Hz"
            )

            # Optimize data type first
            audio_data = self._optimize_audio_data_type(audio_data)

            # More aggressive downsampling for performance
            max_samples = WAVEFORM_MAX_SAMPLES  # Use constant for consistency
            if len(audio_data) > max_samples:
                # Use more efficient downsampling
                step = max(1, len(audio_data) // max_samples)
                audio_data = audio_data[::step]
                logger.debug(
                    f"Downsampled audio data from {len(audio_data) * step} to {len(audio_data)} samples"
                )

            # Create figure with specific dimensions
            fig, ax = plt.subplots(
                figsize=(width / 100, height / 100), facecolor=(0, 0, 0, 0)
            )
            fig.patch.set_alpha(0.0)  # Make figure background transparent

            # Generate time axis (optimized)
            time_axis = np.linspace(0, len(audio_data) / sample_rate, len(audio_data))

            # Plot waveform with optimized settings
            ax.plot(
                time_axis, audio_data, color=color, linewidth=0.5
            )  # Configurable color waveform
            ax.fill_between(time_axis, audio_data, alpha=alpha, color=color)

            # Remove axes and make it clean
            ax.set_xlim(0, time_axis[-1])
            ax.set_ylim(-1.1, 1.1)
            ax.axis("off")
            ax.patch.set_alpha(0.0)  # Make axes background transparent

            # Remove all padding and margins
            plt.tight_layout(pad=0)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

            # Save to buffer with optimized settings
            buffer = BytesIO()
            plt.savefig(
                buffer,
                format="png",
                dpi=100,
                bbox_inches="tight",
                pad_inches=0,
                facecolor=(0, 0, 0, 0),
                edgecolor="none",
                transparent=True,
            )
            plt.close(fig)  # Important: close figure to free memory

            # Force garbage collection after matplotlib operations
            self._force_garbage_collection()

            buffer.seek(0)
            processing_time = time.time() - start_time
            logger.debug(
                f"Waveform generated: {len(buffer.getvalue())} bytes in {processing_time:.2f}s"
            )

            # Store performance stats
            self.performance_stats["processing_times"][
                "waveform_generation"
            ] = processing_time

            return buffer

        except Exception as e:
            logger.error(f"Error generating waveform: {str(e)}")
            raise AudioProcessingError(f"Waveform generation failed: {str(e)}")

    async def _upload_waveform(
        self, waveform_buffer: BytesIO, session_token: str
    ) -> str:
        """Upload waveform image to storage with enhanced error handling"""
        temp_file = None
        try:
            logger.info(f"Uploading waveform for session: {session_token}")

            # Create a temporary file for upload
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_file.write(waveform_buffer.getvalue())
            temp_file.close()

            waveform_key = f"waveforms/{session_token}.png"

            if self.file_uploader.s3_client:
                # Upload to S3
                logger.debug(f"Uploading to S3: {settings.s3_bucket}/{waveform_key}")
                with open(temp_file.name, "rb") as f:
                    # Waveforms should be publicly readable for preview PDFs
                    extra_args = {
                        "ContentType": "image/png",
                        "ServerSideEncryption": "AES256",
                    }

                    # Try to make waveforms publicly readable
                    try:
                        extra_args["ACL"] = "public-read"
                    except Exception:
                        # If ACL is not supported, we'll rely on bucket policy
                        pass

                    try:
                        self.file_uploader.s3_client.upload_fileobj(
                            f, settings.s3_bucket, waveform_key, ExtraArgs=extra_args
                        )
                        logger.info(f"S3 upload completed: {waveform_key}")
                    except Exception as e:
                        if "AccessControlListNotSupported" in str(e):
                            # Retry without ACL if bucket doesn't support it
                            logger.warning("ACL not supported, retrying without ACL")
                            extra_args.pop("ACL", None)  # Remove ACL if present
                            self.file_uploader.s3_client.upload_fileobj(
                                f,
                                settings.s3_bucket,
                                waveform_key,
                                ExtraArgs=extra_args,
                            )
                            logger.info(f"S3 upload completed (no ACL): {waveform_key}")
                        else:
                            logger.error(f"S3 upload failed: {str(e)}")
                            raise AudioProcessingError(f"S3 upload failed: {str(e)}")
            else:
                # Store locally
                local_path = os.path.join(
                    self.file_uploader.local_storage_path, waveform_key
                )
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                import shutil

                shutil.copy2(temp_file.name, local_path)
                logger.info(f"Local upload completed: {local_path}")

            return waveform_key

        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading waveform: {str(e)}")
            raise AudioProcessingError(f"Waveform upload failed: {str(e)}")
        finally:
            # Cleanup temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                    logger.debug(
                        f"Cleaned up temporary waveform file: {temp_file.name}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup temporary file {temp_file.name}: {str(e)}"
                    )

    def advanced_silence_trimming(
        self, audio_data: np.ndarray, sample_rate: int, trim_method: str = "dynamic"
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """
        Advanced silence trimming with multiple strategies

        Args:
            audio_data: Audio data array
            sample_rate: Sample rate of the audio
            trim_method: Trimming method ('dynamic', 'split', 'segment', 'adaptive')

        Returns:
            Tuple of (trimmed_audio, trimming_info)
        """
        try:
            logger.info(
                f"Applying advanced silence trimming using method: {trim_method}"
            )

            if trim_method == "dynamic":
                return self._dynamic_silence_trimming(audio_data, sample_rate)
            elif trim_method == "split":
                return self._split_based_trimming(audio_data, sample_rate)
            elif trim_method == "segment":
                return self._segment_based_trimming(audio_data, sample_rate)
            elif trim_method == "adaptive":
                return self._adaptive_trimming(audio_data, sample_rate)
            else:
                logger.warning(f"Unknown trim method: {trim_method}, using dynamic")
                return self._dynamic_silence_trimming(audio_data, sample_rate)

        except Exception as e:
            logger.error(f"Advanced silence trimming failed: {str(e)}")
            # Fallback to basic trimming
            try:
                trimmed_audio, _ = librosa.effects.trim(audio_data, top_db=20)
                return trimmed_audio, {"method": "fallback", "error": str(e)}
            except:
                return audio_data, {"method": "none", "error": str(e)}

    def _dynamic_silence_trimming(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """Dynamic thresholding based on audio characteristics"""
        try:
            # Analyze audio amplitude distribution
            rms = librosa.feature.rms(y=audio_data)[0]
            rms_mean = np.mean(rms)
            rms_std = np.std(rms)

            # Calculate dynamic threshold based on audio characteristics
            if rms_std > 0:
                # For variable loudness audio, use percentile-based threshold
                threshold_db = -20 - (rms_std * 10)  # Adaptive threshold
                threshold_db = max(
                    -40, min(-10, threshold_db)
                )  # Clamp between -40 and -10 dB
            else:
                # For constant loudness audio, use fixed threshold
                threshold_db = -20

            logger.debug(f"Dynamic threshold calculated: {threshold_db:.1f} dB")

            # Apply trimming with dynamic threshold
            trimmed_audio, trim_indices = librosa.effects.trim(
                audio_data, top_db=abs(threshold_db)
            )

            # Calculate trimming statistics
            original_duration = len(audio_data) / sample_rate
            trimmed_duration = len(trimmed_audio) / sample_rate
            silence_removed = original_duration - trimmed_duration

            trimming_info = {
                "method": "dynamic",
                "threshold_db": float(threshold_db),
                "original_duration": float(original_duration),
                "trimmed_duration": float(trimmed_duration),
                "silence_removed": float(silence_removed),
                "silence_percentage": float((silence_removed / original_duration) * 100)
                if original_duration > 0
                else 0,
                "trim_indices": trim_indices.tolist(),
            }

            logger.info(
                f"Dynamic trimming completed: {silence_removed:.2f}s removed ({trimming_info['silence_percentage']:.1f}%)"
            )
            return trimmed_audio, trimming_info

        except Exception as e:
            logger.error(f"Dynamic silence trimming failed: {str(e)}")
            raise AudioProcessingError(f"Dynamic trimming failed: {str(e)}")

    def _split_based_trimming(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """Split-based trimming using librosa.effects.split()"""
        try:
            # Split audio into non-silent intervals
            intervals = librosa.effects.split(audio_data, top_db=20)

            if len(intervals) == 0:
                logger.warning(
                    "No non-silent intervals found, returning original audio"
                )
                return audio_data, {
                    "method": "split",
                    "intervals": 0,
                    "error": "no_intervals",
                }

            # Concatenate all non-silent intervals
            trimmed_segments = []
            for start, end in intervals:
                trimmed_segments.append(audio_data[start:end])

            trimmed_audio = np.concatenate(trimmed_segments)

            # Calculate statistics
            original_duration = len(audio_data) / sample_rate
            trimmed_duration = len(trimmed_audio) / sample_rate
            silence_removed = original_duration - trimmed_duration

            trimming_info = {
                "method": "split",
                "intervals_found": len(intervals),
                "original_duration": float(original_duration),
                "trimmed_duration": float(trimmed_duration),
                "silence_removed": float(silence_removed),
                "silence_percentage": float((silence_removed / original_duration) * 100)
                if original_duration > 0
                else 0,
                "interval_details": [
                    {
                        "start": int(start),
                        "end": int(end),
                        "duration": float((end - start) / sample_rate),
                    }
                    for start, end in intervals
                ],
            }

            logger.info(
                f"Split-based trimming completed: {len(intervals)} intervals, {silence_removed:.2f}s removed"
            )
            return trimmed_audio, trimming_info

        except Exception as e:
            logger.error(f"Split-based trimming failed: {str(e)}")
            raise AudioProcessingError(f"Split-based trimming failed: {str(e)}")

    def _segment_based_trimming(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """Segment-based trimming for varying loudness levels"""
        try:
            # Divide audio into segments (5-second segments)
            segment_length = int(5 * sample_rate)  # 5 seconds
            segments = []

            for i in range(0, len(audio_data), segment_length):
                segment = audio_data[i : i + segment_length]
                if len(segment) > 0:
                    segments.append(segment)

            # Trim each segment individually
            trimmed_segments = []
            segment_stats = []

            for i, segment in enumerate(segments):
                try:
                    # Use adaptive threshold for each segment
                    rms = librosa.feature.rms(y=segment)[0]
                    rms_mean = np.mean(rms)

                    # Calculate segment-specific threshold
                    if rms_mean > 0.01:  # If segment has significant content
                        threshold_db = -15 - (
                            rms_mean * 20
                        )  # Adaptive based on segment energy
                        threshold_db = max(-35, min(-5, threshold_db))
                    else:
                        threshold_db = -25  # Lower threshold for quiet segments

                    trimmed_segment, trim_indices = librosa.effects.trim(
                        segment, top_db=abs(threshold_db)
                    )

                    if len(trimmed_segment) > 0:
                        trimmed_segments.append(trimmed_segment)

                    segment_stats.append(
                        {
                            "segment_index": i,
                            "original_length": len(segment),
                            "trimmed_length": len(trimmed_segment),
                            "threshold_used": float(threshold_db),
                            "energy_mean": float(rms_mean),
                        }
                    )

                except Exception as e:
                    logger.warning(f"Failed to trim segment {i}: {str(e)}")
                    # Keep original segment if trimming fails
                    trimmed_segments.append(segment)

            if not trimmed_segments:
                logger.warning(
                    "All segments were empty after trimming, returning original audio"
                )
                return audio_data, {
                    "method": "segment",
                    "segments": len(segments),
                    "error": "all_segments_empty",
                }

            # Concatenate trimmed segments
            trimmed_audio = np.concatenate(trimmed_segments)

            # Calculate statistics
            original_duration = len(audio_data) / sample_rate
            trimmed_duration = len(trimmed_audio) / sample_rate
            silence_removed = original_duration - trimmed_duration

            trimming_info = {
                "method": "segment",
                "segments_processed": len(segments),
                "segments_kept": len(trimmed_segments),
                "original_duration": float(original_duration),
                "trimmed_duration": float(trimmed_duration),
                "silence_removed": float(silence_removed),
                "silence_percentage": float((silence_removed / original_duration) * 100)
                if original_duration > 0
                else 0,
                "segment_details": segment_stats,
            }

            logger.info(
                f"Segment-based trimming completed: {len(trimmed_segments)}/{len(segments)} segments kept"
            )
            return trimmed_audio, trimming_info

        except Exception as e:
            logger.error(f"Segment-based trimming failed: {str(e)}")
            raise AudioProcessingError(f"Segment-based trimming failed: {str(e)}")

    def _adaptive_trimming(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Tuple[np.ndarray, Dict[str, any]]:
        """Adaptive trimming that combines multiple strategies"""
        try:
            # First, try split-based trimming
            try:
                trimmed_audio, split_info = self._split_based_trimming(
                    audio_data, sample_rate
                )
                if split_info.get("intervals_found", 0) > 0:
                    logger.info("Using split-based trimming result")
                    split_info["method"] = "adaptive_split"
                    return trimmed_audio, split_info
            except Exception as e:
                logger.warning(
                    f"Split-based trimming failed in adaptive mode: {str(e)}"
                )

            # Fallback to dynamic trimming
            try:
                trimmed_audio, dynamic_info = self._dynamic_silence_trimming(
                    audio_data, sample_rate
                )
                logger.info("Using dynamic trimming result as fallback")
                dynamic_info["method"] = "adaptive_dynamic"
                return trimmed_audio, dynamic_info
            except Exception as e:
                logger.warning(f"Dynamic trimming failed in adaptive mode: {str(e)}")

            # Final fallback to basic trimming
            trimmed_audio, _ = librosa.effects.trim(audio_data, top_db=20)
            logger.info("Using basic trimming as final fallback")

            original_duration = len(audio_data) / sample_rate
            trimmed_duration = len(trimmed_audio) / sample_rate

            return trimmed_audio, {
                "method": "adaptive_basic",
                "original_duration": float(original_duration),
                "trimmed_duration": float(trimmed_duration),
                "silence_removed": float(original_duration - trimmed_duration),
                "fallback_used": True,
            }

        except Exception as e:
            logger.error(f"Adaptive trimming failed: {str(e)}")
            raise AudioProcessingError(f"Adaptive trimming failed: {str(e)}")

    def detect_peaks(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        peak_types: List[str] = ["onset", "spectral", "envelope"],
    ) -> Dict[str, any]:
        """
        Comprehensive peak detection using multiple methods

        Args:
            audio_data: Audio data array
            sample_rate: Sample rate of the audio
            peak_types: List of peak detection types to perform

        Returns:
            Dict containing peak detection results
        """
        try:
            logger.info(f"Detecting peaks using methods: {peak_types}")

            peak_results = {
                "sample_rate": sample_rate,
                "duration": len(audio_data) / sample_rate,
                "peak_detection_methods": peak_types,
            }

            # Onset detection
            if "onset" in peak_types:
                peak_results["onset_peaks"] = self._detect_onset_peaks(
                    audio_data, sample_rate
                )

            # Spectral peak detection
            if "spectral" in peak_types:
                peak_results["spectral_peaks"] = self._detect_spectral_peaks(
                    audio_data, sample_rate
                )

            # Envelope peak detection
            if "envelope" in peak_types:
                peak_results["envelope_peaks"] = self._detect_envelope_peaks(
                    audio_data, sample_rate
                )

            # Calculate overall peak statistics
            peak_results["peak_statistics"] = self._calculate_peak_statistics(
                peak_results
            )

            logger.info(f"Peak detection completed: {len(peak_results)} analysis types")
            return peak_results

        except Exception as e:
            logger.error(f"Peak detection failed: {str(e)}")
            raise AudioProcessingError(f"Peak detection failed: {str(e)}")

    def _detect_onset_peaks(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """Detect onset peaks using librosa's onset detection"""
        try:
            # Detect onsets with multiple methods
            onset_frames = librosa.onset.onset_detect(
                y=audio_data,
                sr=sample_rate,
                units="time",
                pre_max=3,
                post_max=3,
                pre_avg=3,
                post_avg=5,
                delta=0.2,
                wait=10,
            )

            # Convert to sample indices
            onset_samples = (onset_frames * sample_rate).astype(int)

            # Calculate onset strength
            onset_strength = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)

            # Get peak amplitudes at onset points
            onset_amplitudes = []
            for sample_idx in onset_samples:
                if 0 <= sample_idx < len(audio_data):
                    onset_amplitudes.append(abs(audio_data[sample_idx]))
                else:
                    onset_amplitudes.append(0.0)

            return {
                "onset_times": onset_frames.tolist(),
                "onset_samples": onset_samples.tolist(),
                "onset_amplitudes": onset_amplitudes,
                "onset_count": len(onset_frames),
                "onset_strength_mean": float(np.mean(onset_strength)),
                "onset_strength_std": float(np.std(onset_strength)),
                "onset_rate": float(len(onset_frames) / (len(audio_data) / sample_rate))
                if len(audio_data) > 0
                else 0,
            }

        except Exception as e:
            logger.warning(f"Onset peak detection failed: {str(e)}")
            return {"error": str(e), "onset_count": 0}

    def _detect_spectral_peaks(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """Detect spectral peaks using melspectrogram and chroma analysis"""
        try:
            # Generate melspectrogram
            mel_spec = librosa.feature.melspectrogram(
                y=audio_data, sr=sample_rate, n_mels=128
            )
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

            # Find peaks in melspectrogram
            mel_peaks = []
            for i in range(mel_spec_db.shape[0]):  # For each mel bin
                mel_data = mel_spec_db[i, :]
                # Find peaks in this mel bin
                peaks, _ = librosa.util.peak_pick(
                    mel_data,
                    pre_max=3,
                    post_max=3,
                    pre_avg=3,
                    post_avg=5,
                    delta=0.2,
                    wait=10,
                )
                if len(peaks) > 0:
                    for peak in peaks:
                        mel_peaks.append(
                            {
                                "mel_bin": int(i),
                                "time_frame": int(peak),
                                "magnitude": float(mel_data[peak]),
                            }
                        )

            # Chroma analysis for harmonic peaks
            chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
            chroma_peaks = []
            for i in range(chroma.shape[0]):  # For each chroma bin
                chroma_data = chroma[i, :]
                peaks, _ = librosa.util.peak_pick(
                    chroma_data,
                    pre_max=2,
                    post_max=2,
                    pre_avg=2,
                    post_avg=3,
                    delta=0.1,
                    wait=5,
                )
                if len(peaks) > 0:
                    for peak in peaks:
                        chroma_peaks.append(
                            {
                                "chroma_bin": int(i),
                                "time_frame": int(peak),
                                "magnitude": float(chroma_data[peak]),
                            }
                        )

            return {
                "mel_peaks": mel_peaks,
                "chroma_peaks": chroma_peaks,
                "mel_peak_count": len(mel_peaks),
                "chroma_peak_count": len(chroma_peaks),
                "spectral_peak_count": len(mel_peaks) + len(chroma_peaks),
                "spectral_energy_mean": float(np.mean(mel_spec_db)),
                "spectral_energy_std": float(np.std(mel_spec_db)),
            }

        except Exception as e:
            logger.warning(f"Spectral peak detection failed: {str(e)}")
            return {"error": str(e), "spectral_peak_count": 0}

    def _detect_envelope_peaks(
        self, audio_data: np.ndarray, sample_rate: int
    ) -> Dict[str, any]:
        """Detect peaks in the amplitude envelope"""
        try:
            # Extract amplitude envelope using Hilbert transform
            envelope = np.abs(librosa.effects.hilbert(audio_data))

            # Smooth the envelope to reduce noise
            if SCIPY_AVAILABLE:
                smoothed_envelope = gaussian_filter1d(envelope, sigma=2)
            else:
                # Alternative smoothing using simple moving average
                window_size = min(100, len(envelope) // 10)
                if window_size > 1:
                    smoothed_envelope = np.convolve(
                        envelope, np.ones(window_size) / window_size, mode="same"
                    )
                else:
                    smoothed_envelope = envelope

            # Find peaks in the envelope
            peaks, properties = librosa.util.peak_pick(
                smoothed_envelope,
                pre_max=5,
                post_max=5,
                pre_avg=5,
                post_avg=10,
                delta=0.1,
                wait=20,
            )

            # Calculate peak characteristics
            peak_amplitudes = smoothed_envelope[peaks] if len(peaks) > 0 else []
            peak_times = peaks / sample_rate if len(peaks) > 0 else []

            # Calculate envelope statistics
            envelope_mean = np.mean(envelope)
            envelope_std = np.std(envelope)
            envelope_range = np.max(envelope) - np.min(envelope)

            return {
                "envelope_peaks": peaks.tolist(),
                "peak_times": peak_times.tolist(),
                "peak_amplitudes": peak_amplitudes.tolist(),
                "peak_count": len(peaks),
                "envelope_mean": float(envelope_mean),
                "envelope_std": float(envelope_std),
                "envelope_range": float(envelope_range),
                "peak_rate": float(len(peaks) / (len(audio_data) / sample_rate))
                if len(audio_data) > 0
                else 0,
                "dynamic_range": float(envelope_range / (envelope_mean + 1e-10)),
            }

        except Exception as e:
            logger.warning(f"Envelope peak detection failed: {str(e)}")
            return {"error": str(e), "peak_count": 0}

    def _calculate_peak_statistics(
        self, peak_results: Dict[str, any]
    ) -> Dict[str, any]:
        """Calculate overall statistics from peak detection results"""
        try:
            stats = {
                "total_peaks_detected": 0,
                "peak_types": [],
                "peak_density": 0.0,
                "dominant_peak_type": "none",
            }

            duration = peak_results.get("duration", 1.0)

            # Count peaks by type
            peak_counts = {}
            for key, value in peak_results.items():
                if key.endswith("_peaks") and isinstance(value, dict):
                    peak_type = key.replace("_peaks", "")
                    peak_count = value.get(
                        f"{peak_type}_count", value.get("peak_count", 0)
                    )
                    if isinstance(peak_count, int):
                        peak_counts[peak_type] = peak_count
                        stats["total_peaks_detected"] += peak_count
                        stats["peak_types"].append(peak_type)

            # Calculate peak density (peaks per second)
            if duration > 0:
                stats["peak_density"] = stats["total_peaks_detected"] / duration

            # Determine dominant peak type
            if peak_counts:
                stats["dominant_peak_type"] = max(peak_counts, key=peak_counts.get)
                stats["peak_distribution"] = peak_counts

            return stats

        except Exception as e:
            logger.warning(f"Peak statistics calculation failed: {str(e)}")
            return {"error": str(e), "total_peaks_detected": 0}

    def extract_audio_features(self, audio_data: np.ndarray, sample_rate: int) -> dict:
        """Extract additional audio features for enhanced QR codes (legacy method)"""
        try:
            logger.debug(
                f"Extracting audio features: {len(audio_data)} samples, {sample_rate}Hz"
            )

            # Basic features
            duration = len(audio_data) / sample_rate
            rms_energy = np.sqrt(np.mean(audio_data**2))

            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_data, sr=sample_rate
            )[0]
            avg_spectral_centroid = np.mean(spectral_centroids)

            # Tempo and beat tracking
            try:
                tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            except:
                tempo = 0.0

            # Zero crossing rate
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_data)[0])

            features = {
                "duration": float(duration),
                "rms_energy": float(rms_energy),
                "avg_spectral_centroid": float(avg_spectral_centroid),
                "tempo": float(tempo),
                "zero_crossing_rate": float(zcr),
                "sample_rate": int(sample_rate),
            }

            logger.debug(f"Audio features extracted: {len(features)} fields")
            return features

        except Exception as e:
            logger.warning(f"Error extracting audio features: {str(e)}")
            # Return basic features if advanced analysis fails
            return {
                "duration": len(audio_data) / sample_rate,
                "sample_rate": sample_rate,
                "error": str(e),
            }
