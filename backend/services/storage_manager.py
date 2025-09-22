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
from .encryption_service import EncryptionService

class StorageManager:
    """Manages temporary and permanent file storage"""

    def __init__(self):
        self.file_uploader = FileUploader()
        self.encryption_service = EncryptionService()
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
            # Validate file - check content_type before reading
            if not audio.content_type or not audio.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail="File must be an audio file")

            # Generate temp key for S3
            temp_key = f"temp_audio/{session_token}.{self._get_audio_extension(audio.filename)}"

            # Upload directly to S3 using file_uploader
            if self.file_uploader.s3_client:
                # Reset file position
                await audio.seek(0)

                # Upload to S3
                try:
                    self.file_uploader.s3_client.upload_fileobj(
                        audio.file,
                        settings.s3_bucket,
                        temp_key,
                        ExtraArgs={
                            'ContentType': audio.content_type,
                            **self.encryption_service.get_s3_encryption_config()
                        }
                    )
                    print(f"DEBUG: Audio uploaded to S3: {temp_key}")
                except Exception as s3_error:
                    print(f"ERROR: S3 upload failed: {s3_error}")
                    raise HTTPException(status_code=500, detail=f"Failed to upload audio to S3: {str(s3_error)}")
            else:
                # Fallback to local storage for development
                temp_path = os.path.join(self.temp_storage_path, temp_key)
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)

                # Write audio file
                await audio.seek(0)
                with open(temp_path, "wb") as buffer:
                    content = await audio.read()
                    buffer.write(content)
                print(f"DEBUG: Audio stored locally: {temp_path}")

            return temp_key

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Temporary audio storage failed: {str(e)}")

    async def migrate_all_session_files(self, session_token: str, order_id: str) -> dict:
        """Migrate all files for a session to permanent storage after payment"""
        try:
            permanent_keys = {}
            migration_log = []

            # Migrate photo
            temp_photo_key = f"temp_photos/{session_token}.jpg"
            temp_photo_path = os.path.join(self.temp_storage_path, temp_photo_key)

            if os.path.exists(temp_photo_path):
                permanent_photo_key = f"permanent/photos/{order_id}.jpg"
                await self._upload_to_s3_permanent(temp_photo_path, permanent_photo_key, 'image/jpeg')
                permanent_keys['permanent_photo_s3_key'] = permanent_photo_key
                migration_log.append(f"Migrated photo: {temp_photo_key} -> {permanent_photo_key}")

                # Clean up temporary file
                os.remove(temp_photo_path)
                migration_log.append(f"Cleaned up temp photo: {temp_photo_path}")

            # Migrate audio
            temp_audio_dir = os.path.join(self.temp_storage_path, "temp_audio")

            if os.path.exists(temp_audio_dir):
                for filename in os.listdir(temp_audio_dir):
                    if filename.startswith(session_token):
                        temp_audio_path = os.path.join(temp_audio_dir, filename)
                        file_extension = filename.split('.')[-1]
                        permanent_audio_key = f"permanent/audio/{order_id}.{file_extension}"

                        # Determine content type based on extension
                        content_type = self._get_audio_content_type(file_extension)
                        await self._upload_to_s3_permanent(temp_audio_path, permanent_audio_key, content_type)
                        permanent_keys['permanent_audio_s3_key'] = permanent_audio_key
                        migration_log.append(f"Migrated audio: {temp_audio_path} -> {permanent_audio_key}")

                        # Clean up temporary file
                        os.remove(temp_audio_path)
                        migration_log.append(f"Cleaned up temp audio: {temp_audio_path}")

            # Migrate waveform (if exists in S3)
            waveform_s3_key = f"waveforms/{session_token}.png"
            if self.file_uploader.file_exists(waveform_s3_key):
                permanent_waveform_key = f"permanent/waveforms/{order_id}.png"
                await self._copy_s3_file(waveform_s3_key, permanent_waveform_key)
                permanent_keys['permanent_waveform_s3_key'] = permanent_waveform_key
                migration_log.append(f"Migrated waveform: {waveform_s3_key} -> {permanent_waveform_key}")

            # Log migration success
            print(f"Migration completed for order {order_id}: {len(permanent_keys)} files migrated")
            for log_entry in migration_log:
                print(f"  - {log_entry}")

            return permanent_keys

        except Exception as e:
            error_msg = f"Migration to permanent storage failed: {str(e)}"
            print(f"Migration error for order {order_id}: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    async def migrate_file_to_permanent(self, temp_key: str, permanent_key: str, content_type: str) -> bool:
        """Migrate a single file from temp to permanent storage"""
        try:
            temp_path = os.path.join(self.temp_storage_path, temp_key)

            if not os.path.exists(temp_path):
                print(f"Temporary file not found: {temp_path}")
                return False

            await self._upload_to_s3_permanent(temp_path, permanent_key, content_type)
            print(f"Successfully migrated: {temp_key} -> {permanent_key}")
            return True

        except Exception as e:
            print(f"Failed to migrate file {temp_key}: {str(e)}")
            return False

    def verify_migration_success(self, permanent_keys: list) -> bool:
        """Verify all permanent files exist in S3"""
        try:
            for key in permanent_keys:
                if key and not self.file_uploader.file_exists(key):
                    print(f"Migration verification failed: {key} not found in S3")
                    return False
            print(f"Migration verification successful: {len(permanent_keys)} files verified")
            return True

        except Exception as e:
            print(f"Migration verification error: {str(e)}")
            return False

    async def rollback_migration(self, permanent_keys: list) -> bool:
        """Rollback migration by deleting permanent files"""
        try:
            for key in permanent_keys:
                if key and self.file_uploader.file_exists(key):
                    self.file_uploader.delete_file(key)
                    print(f"Rolled back permanent file: {key}")

            print(f"Migration rollback completed: {len(permanent_keys)} files removed")
            return True

        except Exception as e:
            print(f"Migration rollback error: {str(e)}")
            return False

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
            return f"{settings.base_url}/static/temp/{temp_key}"

    async def _upload_to_s3_permanent(self, file_path: str, s3_key: str, content_type: str):
        """Upload file to S3 with permanent storage settings"""
        if self.file_uploader.s3_client:
            with open(file_path, 'rb') as f:
                extra_args = {
                    'ContentType': content_type,
                    **self.encryption_service.get_s3_encryption_config(),
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
                    **self.encryption_service.get_s3_encryption_config(),
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

    def _get_audio_content_type(self, extension: str) -> str:
        """Get content type based on audio file extension"""
        content_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'aac': 'audio/aac',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac'
        }
        return content_types.get(extension.lower(), 'audio/mpeg')

    async def _copy_s3_file(self, source_key: str, dest_key: str):
        """Copy file within S3 from source to destination"""
        if self.file_uploader.s3_client:
            copy_source = {
                'Bucket': settings.s3_bucket,
                'Key': source_key
            }

            copy_args = {
                **self.encryption_service.get_s3_encryption_config(),
                'ACL': 'private'
            }

            self.file_uploader.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=settings.s3_bucket,
                Key=dest_key,
                **copy_args
            )

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
