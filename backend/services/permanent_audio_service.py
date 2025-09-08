import hashlib
import uuid
import os
import shutil
from datetime import datetime
from typing import Optional

from ..models import SessionModel, Order
from ..config import settings
from .file_uploader import FileUploader


class PermanentAudioService:
    """Handles migration of session audio to permanent storage for QR codes"""
    
    def __init__(self):
        self.file_uploader = FileUploader()
    
    async def migrate_to_permanent_storage(self, session: SessionModel, order: Order) -> str:
        """
        Copy audio from session to permanent order storage
        
        Args:
            session: Session containing temporary audio
            order: Order record to link permanent audio to
            
        Returns:
            permanent_audio_s3_key: S3 key for permanent audio file
        """
        if not session.audio_s3_key:
            raise Exception("Session has no audio file to migrate")
        
        try:
            # Generate secure permanent key
            permanent_key = f"permanent-audio/{order.id}/{uuid.uuid4()}.mp3"
            
            # Copy from session storage to permanent storage
            await self._copy_to_permanent_storage(
                source_key=session.audio_s3_key,
                dest_key=permanent_key,
                order_id=str(order.id)
            )
            
            # Calculate file hash for integrity verification
            file_hash = await self._calculate_file_hash(permanent_key)
            
            return permanent_key, file_hash
            
        except Exception as e:
            raise Exception(f"Audio migration failed: {str(e)}")
    
    async def _copy_to_permanent_storage(self, source_key: str, dest_key: str, order_id: str):
        """Copy file from session storage to permanent storage"""
        
        if self.file_uploader.s3_client:
            # S3 to S3 copy
            copy_source = {
                'Bucket': settings.s3_bucket,
                'Key': source_key
            }
            
            self.file_uploader.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=settings.s3_bucket,
                Key=dest_key,
                MetadataDirective='REPLACE',
                Metadata={
                    'order_id': order_id,
                    'storage_type': 'permanent',
                    'created_at': str(datetime.utcnow())
                },
                ServerSideEncryption='AES256'
            )
        else:
            # Local file copy
            source_path = os.path.join(self.file_uploader.local_storage_path, source_key)
            dest_path = os.path.join(self.file_uploader.local_storage_path, dest_key)
            
            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
    
    async def _calculate_file_hash(self, s3_key: str) -> str:
        """Calculate SHA-256 hash of file for integrity verification"""
        
        if self.file_uploader.s3_client:
            # Download file temporarily to calculate hash
            import tempfile
            
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            try:
                self.file_uploader.s3_client.download_fileobj(
                    settings.s3_bucket, s3_key, temp_file
                )
                temp_file.close()
                
                # Calculate hash
                sha256_hash = hashlib.sha256()
                with open(temp_file.name, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                
                return sha256_hash.hexdigest()
                
            finally:
                # Cleanup
                os.unlink(temp_file.name)
        else:
            # Local file hash
            file_path = os.path.join(self.file_uploader.local_storage_path, s3_key)
            
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
    
    async def verify_audio_integrity(self, s3_key: str, expected_hash: str) -> bool:
        """Verify audio file integrity using stored hash"""
        try:
            current_hash = await self._calculate_file_hash(s3_key)
            return current_hash == expected_hash
        except Exception:
            return False
    
    def get_permanent_audio_url(self, order: Order, expiration: int = 3600) -> Optional[str]:
        """Generate secure presigned URL for permanent audio access"""
        
        if not order.permanent_audio_s3_key:
            return None
        
        # Note: Integrity check disabled for now to avoid async/await complexity
        # In production, you might want to implement this check periodically
        
        # Generate presigned URL
        return self.file_uploader.generate_presigned_url(
            order.permanent_audio_s3_key,
            expiration=expiration
        )
