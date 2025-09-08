import os
import tempfile
import shutil
from typing import Optional
from pathlib import Path
from fastapi import UploadFile, HTTPException
from PIL import Image
from io import BytesIO

from ..config import settings
from .file_uploader import FileUploader

class StorageManager:
    """Manages temporary and permanent file storage"""
    
    def __init__(self):
        self.file_uploader = FileUploader()
        self.temp_storage_path = "/tmp/audioposter/temp"
        self.permanent_storage_path = "/tmp/audioposter/permanent"
        
        # Create directories
        os.makedirs(self.temp_storage_path, exist_ok=True)
        os.makedirs(self.permanent_storage_path, exist_ok=True)
    
    async def store_photo_temporarily(self, photo: UploadFile, session_token: str) -> str:
        """Store photo temporarily for preview generation"""
        try:
            # Validate file
            if not photo.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            # Read and process image
            image_content = await photo.read()
            image = Image.open(BytesIO(image_content))
            
            # Process the image (resize, optimize)
            processed_image = self._process_image(image)
            
            # Save to temporary storage
            temp_key = f"temp_photos/{session_token}.jpg"
            temp_path = os.path.join(self.temp_storage_path, temp_key)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            processed_image.save(temp_path, 'JPEG', quality=95, optimize=True)
            
            return temp_key
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Temporary photo storage failed: {str(e)}")
    
    async def store_audio_temporarily(self, audio: UploadFile, session_token: str) -> str:
        """Store audio temporarily for preview generation"""
        try:
            # Validate file
            if not audio.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="File must be an audio file")
            
            # Save to temporary storage
            temp_key = f"temp_audio/{session_token}.{self._get_audio_extension(audio.filename)}"
            temp_path = os.path.join(self.temp_storage_path, temp_key)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # Write audio file
            with open(temp_path, "wb") as buffer:
                content = await audio.read()
                buffer.write(content)
            
            return temp_key
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Temporary audio storage failed: {str(e)}")
    
    async def migrate_to_permanent_storage(self, session_token: str) -> dict:
        """Migrate temporary files to permanent S3 storage after payment"""
        try:
            permanent_keys = {}
            
            # Migrate photo
            temp_photo_key = f"temp_photos/{session_token}.jpg"
            temp_photo_path = os.path.join(self.temp_storage_path, temp_photo_key)
            
            if os.path.exists(temp_photo_path):
                permanent_photo_key = f"photos/{session_token}.jpg"
                await self._upload_to_s3_permanent(temp_photo_path, permanent_photo_key, 'image/jpeg')
                permanent_keys['photo'] = permanent_photo_key
                
                # Clean up temporary file
                os.remove(temp_photo_path)
            
            # Migrate audio
            temp_audio_key = f"temp_audio/{session_token}.*"
            temp_audio_dir = os.path.join(self.temp_storage_path, "temp_audio")
            
            if os.path.exists(temp_audio_dir):
                for filename in os.listdir(temp_audio_dir):
                    if filename.startswith(session_token):
                        temp_audio_path = os.path.join(temp_audio_dir, filename)
                        permanent_audio_key = f"audio/{session_token}.{filename.split('.')[-1]}"
                        await self._upload_to_s3_permanent(temp_audio_path, permanent_audio_key, 'audio/mpeg')
                        permanent_keys['audio'] = permanent_audio_key
                        
                        # Clean up temporary file
                        os.remove(temp_audio_path)
            
            return permanent_keys
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Migration to permanent storage failed: {str(e)}")
    
    def get_temp_file_path(self, temp_key: str) -> Optional[str]:
        """Get local file path for temporary file"""
        temp_path = os.path.join(self.temp_storage_path, temp_key)
        return temp_path if os.path.exists(temp_path) else None
    
    async def get_temp_file_url(self, temp_key: str) -> str:
        """Get URL for temporary file (for preview generation)"""
        if self.file_uploader.s3_client:
            # For S3, we still need to upload temporarily but mark as temporary
            temp_path = os.path.join(self.temp_storage_path, temp_key)
            if os.path.exists(temp_path):
                # Upload to S3 with temporary prefix
                s3_key = f"temp/{temp_key}"
                await self._upload_to_s3_temporary(temp_path, s3_key)
                return f"https://{settings.s3_bucket}.s3.amazonaws.com/{s3_key}"
        else:
            # For local storage, return local URL
            return f"http://localhost:8000/static/temp/{temp_key}"
    
    async def _upload_to_s3_permanent(self, file_path: str, s3_key: str, content_type: str):
        """Upload file to S3 with permanent storage settings"""
        if self.file_uploader.s3_client:
            with open(file_path, 'rb') as f:
                extra_args = {
                    'ContentType': content_type,
                    'ServerSideEncryption': 'AES256',
                    'ACL': 'private'  # Private for permanent storage
                }
                
                self.file_uploader.s3_client.upload_fileobj(
                    f, settings.s3_bucket, s3_key, ExtraArgs=extra_args
                )
    
    async def _upload_to_s3_temporary(self, file_path: str, s3_key: str):
        """Upload file to S3 with temporary storage settings"""
        if self.file_uploader.s3_client:
            with open(file_path, 'rb') as f:
                extra_args = {
                    'ContentType': 'application/octet-stream',
                    'ServerSideEncryption': 'AES256',
                    'ACL': 'public-read'  # Public for temporary preview files
                }
                
                self.file_uploader.s3_client.upload_fileobj(
                    f, settings.s3_bucket, s3_key, ExtraArgs=extra_args
                )
    
    def _process_image(self, image: Image.Image) -> Image.Image:
        """Process image for storage"""
        try:
            # Fix orientation based on EXIF data
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to standard dimensions while maintaining aspect ratio
            max_size = (1200, 1200)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image processing error: {str(e)}")
    
    def _get_audio_extension(self, filename: str) -> str:
        """Get audio file extension"""
        if filename:
            return filename.split('.')[-1].lower()
        return 'mp3'
    
    def cleanup_temp_files(self, session_token: str):
        """Clean up temporary files for a session"""
        try:
            # Clean up photo
            temp_photo_key = f"temp_photos/{session_token}.jpg"
            temp_photo_path = os.path.join(self.temp_storage_path, temp_photo_key)
            if os.path.exists(temp_photo_path):
                os.remove(temp_photo_path)
            
            # Clean up audio
            temp_audio_dir = os.path.join(self.temp_storage_path, "temp_audio")
            if os.path.exists(temp_audio_dir):
                for filename in os.listdir(temp_audio_dir):
                    if filename.startswith(session_token):
                        os.remove(os.path.join(temp_audio_dir, filename))
                        
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
