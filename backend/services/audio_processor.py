import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from io import BytesIO
import tempfile
import os
from fastapi import HTTPException

from ..config import settings
from .file_uploader import FileUploader

class AudioProcessor:
    """Processes audio files and generates waveform visualizations"""
    
    def __init__(self):
        self.file_uploader = FileUploader()
    
    async def process_audio_file(self, audio_s3_key: str, session_token: str) -> dict:
        """
        Process audio file from S3 and generate waveform
        Returns audio metadata and waveform S3 key
        """
        try:
            # Download audio file from S3/local storage
            audio_path = await self._download_audio_file(audio_s3_key)
            
            # Load and process audio
            y, sr = librosa.load(audio_path, sr=44100)
            
            # Validate audio duration
            duration = len(y) / sr
            if duration > settings.max_audio_duration:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Audio too long (max {settings.max_audio_duration}s)"
                )
            
            # Normalize audio
            y = librosa.util.normalize(y)
            
            # Trim silence
            y_trimmed, _ = librosa.effects.trim(y, top_db=20)
            
            # Generate waveform visualization
            waveform_buffer = self._generate_waveform_image(y_trimmed, sr)
            
            # Upload waveform to storage
            waveform_key = await self._upload_waveform(waveform_buffer, session_token)
            
            # Cleanup temporary files
            os.unlink(audio_path)
            
            return {
                'duration': len(y_trimmed) / sr,
                'waveform_s3_key': waveform_key,
                'sample_rate': sr,
                'status': 'completed'
            }
            
        except Exception as e:
            # Cleanup on error
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.unlink(audio_path)
            
            if isinstance(e, HTTPException):
                raise e
            
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    
    async def _download_audio_file(self, s3_key: str) -> str:
        """Download audio file to temporary location"""
        # Check if this is a temporary file
        if s3_key.startswith('temp_'):
            # This is a temporary file, get the local path
            from .storage_manager import StorageManager
            storage_manager = StorageManager()
            temp_path = storage_manager.get_temp_file_path(s3_key)
            if temp_path and os.path.exists(temp_path):
                return temp_path
            else:
                raise HTTPException(status_code=404, detail="Temporary audio file not found")
        
        # Handle permanent S3 files
        if self.file_uploader.s3_client:
            # Download from S3
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            try:
                self.file_uploader.s3_client.download_fileobj(
                    settings.s3_bucket, 
                    s3_key, 
                    temp_file
                )
                temp_file.close()
                return temp_file.name
            except Exception as e:
                temp_file.close()
                os.unlink(temp_file.name)
                raise e
        else:
            # Local storage
            local_path = os.path.join(self.file_uploader.local_storage_path, s3_key)
            if not os.path.exists(local_path):
                raise HTTPException(status_code=404, detail="Audio file not found")
            return local_path
    
    def _generate_waveform_image(self, audio_data: np.ndarray, sample_rate: int, 
                                width: int = 1200, height: int = 200) -> BytesIO:
        """Generate waveform visualization as PNG image"""
        # Create figure with specific dimensions
        fig, ax = plt.subplots(figsize=(width/100, height/100), facecolor=(0, 0, 0, 0))
        fig.patch.set_alpha(0.0)  # Make figure background transparent
        
        # Generate time axis
        time_axis = np.linspace(0, len(audio_data) / sample_rate, len(audio_data))
        
        # Plot waveform
        ax.plot(time_axis, audio_data, color='#000000', linewidth=0.5)  # Black waveform
        ax.fill_between(time_axis, audio_data, alpha=0.3, color='#000000')
        
        # Remove axes and make it clean
        ax.set_xlim(0, time_axis[-1])
        ax.set_ylim(-1.1, 1.1)
        ax.axis('off')
        ax.patch.set_alpha(0.0)  # Make axes background transparent
        
        # Remove all padding and margins
        plt.tight_layout(pad=0)
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(
            buffer, 
            format='png', 
            dpi=100, 
            bbox_inches='tight',
            pad_inches=0,
            facecolor=(0, 0, 0, 0), 
            edgecolor='none',
            transparent=True
        )
        plt.close(fig)  # Important: close figure to free memory
        
        buffer.seek(0)
        return buffer
    
    async def _upload_waveform(self, waveform_buffer: BytesIO, session_token: str) -> str:
        """Upload waveform image to storage"""
        # Create a temporary file for upload
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_file.write(waveform_buffer.getvalue())
        temp_file.close()
        
        try:
            waveform_key = f"waveforms/{session_token}.png"
            
            if self.file_uploader.s3_client:
                # Upload to S3
                with open(temp_file.name, 'rb') as f:
                    # Waveforms should be publicly readable for preview PDFs
                    extra_args = {
                        'ContentType': 'image/png',
                        'ServerSideEncryption': 'AES256'
                    }
                    
                    # Try to make waveforms publicly readable
                    try:
                        extra_args['ACL'] = 'public-read'
                    except Exception:
                        # If ACL is not supported, we'll rely on bucket policy
                        pass
                    
                    try:
                        self.file_uploader.s3_client.upload_fileobj(
                            f,
                            settings.s3_bucket,
                            waveform_key,
                            ExtraArgs=extra_args
                        )
                    except Exception as e:
                        if 'AccessControlListNotSupported' in str(e):
                            # Retry without ACL if bucket doesn't support it
                            extra_args.pop('ACL', None)  # Remove ACL if present
                            self.file_uploader.s3_client.upload_fileobj(
                                f,
                                settings.s3_bucket,
                                waveform_key,
                                ExtraArgs=extra_args
                            )
                        else:
                            raise e
            else:
                # Store locally
                local_path = os.path.join(self.file_uploader.local_storage_path, waveform_key)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                import shutil
                shutil.copy2(temp_file.name, local_path)
            
            return waveform_key
            
        finally:
            # Cleanup temporary file
            os.unlink(temp_file.name)
    
    def extract_audio_features(self, audio_data: np.ndarray, sample_rate: int) -> dict:
        """Extract additional audio features for enhanced QR codes"""
        try:
            # Basic features
            duration = len(audio_data) / sample_rate
            rms_energy = np.sqrt(np.mean(audio_data**2))
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
            avg_spectral_centroid = np.mean(spectral_centroids)
            
            # Tempo and beat tracking
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            
            return {
                'duration': duration,
                'rms_energy': float(rms_energy),
                'avg_spectral_centroid': float(avg_spectral_centroid),
                'tempo': float(tempo),
                'sample_rate': sample_rate
            }
            
        except Exception as e:
            # Return basic features if advanced analysis fails
            return {
                'duration': len(audio_data) / sample_rate,
                'sample_rate': sample_rate
            }
