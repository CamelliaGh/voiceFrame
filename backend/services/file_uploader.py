import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException
import uuid
from typing import BinaryIO, Optional
import os
from datetime import datetime
import time
import hashlib

from ..config import settings
from .encryption_service import EncryptionService
from .file_audit_logger import file_audit_logger, FileOperationType, FileType, FileOperationStatus, FileOperationContext, FileOperationDetails

class FileUploader:
    """Handles file uploads to AWS S3"""

    def __init__(self):
        self.encryption_service = EncryptionService()

        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.s3_region,
                config=boto3.session.Config(
                    signature_version='s3v4'  # Force AWS4-HMAC-SHA256 signature
                )
            )
        else:
            # For development, might use local storage
            self.s3_client = None
            self.local_storage_path = "/tmp/audioposter"
            os.makedirs(self.local_storage_path, exist_ok=True)

    async def upload_file(self, file: UploadFile, prefix: str = "", context: Optional[FileOperationContext] = None, db=None) -> str:
        """Upload file to S3 or local storage and return the key/path"""
        file_extension = self._get_file_extension(file.filename)
        file_key = f"{prefix}/{uuid.uuid4()}{file_extension}"

        # Determine file type
        file_type = self._determine_file_type(file.content_type, file.filename)

        # Calculate file hash and size
        file_content = await file.read()
        file_size = len(file_content)
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Reset file position
        await file.seek(0)

        start_time = time.time()
        status = FileOperationStatus.SUCCESS
        error_message = None

        try:
            if self.s3_client:
                # Upload to S3
                await self._upload_to_s3(file, file_key)
            else:
                # Store locally for development
                await self._upload_to_local(file, file_key)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log successful upload
            if context and db:
                file_audit_logger.log_file_upload(
                    file_type=file_type,
                    file_path=file_key,
                    file_size=file_size,
                    content_type=file.content_type,
                    context=context,
                    status=status,
                    processing_time_ms=processing_time_ms,
                    db=db
                )

            return file_key

        except Exception as e:
            status = FileOperationStatus.FAILED
            error_message = str(e)
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log failed upload
            if context and db:
                file_audit_logger.log_file_upload(
                    file_type=file_type,
                    file_path=file_key,
                    file_size=file_size,
                    content_type=file.content_type,
                    context=context,
                    status=status,
                    error_message=error_message,
                    processing_time_ms=processing_time_ms,
                    db=db
                )

            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    async def upload_file_with_key(self, file: UploadFile, file_key: str) -> str:
        """Upload file to S3 or local storage with a specific key/path"""
        try:
            if self.s3_client:
                # Upload to S3
                await self._upload_to_s3(file, file_key)
            else:
                # Store locally for development
                await self._upload_to_local(file, file_key)

            return file_key

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    async def _upload_to_s3(self, file: UploadFile, key: str):
        """Upload file to S3"""
        try:
            # Determine if this should be public (preview PDFs)
            is_public = 'preview' in key.lower()

            extra_args = {
                'ContentType': file.content_type,
                **self.encryption_service.get_s3_encryption_config()
            }

            # Try to make preview PDFs publicly readable
            if is_public:
                try:
                    extra_args['ACL'] = 'public-read'
                except Exception:
                    # If ACL is not supported, we'll rely on bucket policy
                    pass

            self.s3_client.upload_fileobj(
                file.file,
                settings.s3_bucket,
                key,
                ExtraArgs=extra_args
            )
        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except ClientError as e:
            if 'AccessControlListNotSupported' in str(e):
                # Retry without ACL if bucket doesn't support it
                try:
                    extra_args.pop('ACL', None)  # Remove ACL if present
                    self.s3_client.upload_fileobj(
                        file.file,
                        settings.s3_bucket,
                        key,
                        ExtraArgs=extra_args
                    )
                except ClientError as retry_e:
                    raise HTTPException(status_code=500, detail=f"S3 upload failed (retry without ACL): {str(retry_e)}")
            else:
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    async def _upload_to_local(self, file: UploadFile, key: str):
        """Store file locally for development with encryption"""
        file_path = os.path.join(self.local_storage_path, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Read file content
        content = await file.read()

        # Encrypt content before storing locally
        encrypted_content = self.encryption_service.encrypt_file_content(content)

        with open(file_path, "wb") as buffer:
            buffer.write(encrypted_content)

        # Reset file pointer for potential reuse
        await file.seek(0)

    def get_file_url(self, key: str) -> str:
        """Get public URL for a file"""
        if self.s3_client:
            return f"https://{settings.s3_bucket}.s3.amazonaws.com/{key}"
        else:
            return f"{settings.base_url}/static/{key}"

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for secure file access"""
        if self.s3_client:
            try:
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': settings.s3_bucket, 'Key': key},
                    ExpiresIn=expiration
                )
            except ClientError:
                return self.get_file_url(key)
        else:
            return self.get_file_url(key)

    def delete_file(self, key: str, context: Optional[FileOperationContext] = None, db=None):
        """Delete file from storage"""
        # Determine file type from key
        file_type = self._determine_file_type_from_key(key)

        start_time = time.time()
        status = FileOperationStatus.SUCCESS
        error_message = None
        success = True

        try:
            if self.s3_client:
                try:
                    self.s3_client.delete_object(Bucket=settings.s3_bucket, Key=key)
                except ClientError as e:
                    success = False
                    error_message = str(e)
            else:
                file_path = os.path.join(self.local_storage_path, key)
                if os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    success = False
                    error_message = "File not found"

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log deletion
            if context and db:
                file_audit_logger.log_file_deletion(
                    file_type=file_type,
                    file_path=key,
                    context=context,
                    status=status if success else FileOperationStatus.FAILED,
                    error_message=error_message if not success else None,
                    db=db
                )

        except Exception as e:
            status = FileOperationStatus.FAILED
            error_message = str(e)
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log failed deletion
            if context and db:
                file_audit_logger.log_file_deletion(
                    file_type=file_type,
                    file_path=key,
                    context=context,
                    status=status,
                    error_message=error_message,
                    db=db
                )

    def file_exists(self, key: str) -> bool:
        """Check if file exists in storage"""
        if self.s3_client:
            try:
                self.s3_client.head_object(Bucket=settings.s3_bucket, Key=key)
                return True
            except ClientError:
                return False
        else:
            file_path = os.path.join(self.local_storage_path, key)
            return os.path.exists(file_path)

    def list_files_with_prefix(self, prefix: str) -> list:
        """List all files with given prefix"""
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=settings.s3_bucket,
                    Prefix=prefix
                )
                return [obj['Key'] for obj in response.get('Contents', [])]
            except ClientError:
                return []
        else:
            # For local storage, simulate S3 behavior
            prefix_path = os.path.join(self.local_storage_path, prefix)
            if not os.path.exists(prefix_path):
                return []

            files = []
            for root, dirs, filenames in os.walk(prefix_path):
                for filename in filenames:
                    rel_path = os.path.relpath(os.path.join(root, filename), self.local_storage_path)
                    files.append(rel_path.replace('\\', '/'))  # Normalize path separators
            return files

    def get_file_creation_time(self, key: str) -> Optional[datetime]:
        """Get file creation/modification time"""
        from datetime import datetime

        if self.s3_client:
            try:
                response = self.s3_client.head_object(Bucket=settings.s3_bucket, Key=key)
                # S3 returns LastModified time
                return response['LastModified'].replace(tzinfo=None)
            except ClientError:
                return None
        else:
            # For local storage, use file modification time
            file_path = os.path.join(self.local_storage_path, key)
            if os.path.exists(file_path):
                mtime = os.path.getmtime(file_path)
                return datetime.fromtimestamp(mtime)
            return None

    def get_local_file_content(self, key: str) -> bytes:
        """Get decrypted content of a local file"""
        if not self.s3_client:  # Only for local storage
            file_path = os.path.join(self.local_storage_path, key)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    encrypted_content = f.read()
                return self.encryption_service.decrypt_file_content(encrypted_content)
        return b""

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        if not filename:
            return ""
        return os.path.splitext(filename)[1].lower()

    def _determine_file_type(self, content_type: str, filename: str) -> FileType:
        """Determine file type based on content type and filename"""
        if not content_type:
            content_type = ""

        content_type = content_type.lower()
        filename = filename.lower() if filename else ""

        if content_type.startswith('image/') or any(ext in filename for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            return FileType.PHOTO
        elif content_type.startswith('audio/') or any(ext in filename for ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']):
            return FileType.AUDIO
        elif content_type == 'application/pdf' or filename.endswith('.pdf'):
            return FileType.PDF
        elif 'waveform' in filename or filename.endswith('.png') and 'waveform' in content_type:
            return FileType.WAVEFORM
        elif 'template' in filename or 'template' in content_type:
            return FileType.TEMPLATE
        elif 'background' in filename or 'background' in content_type:
            return FileType.BACKGROUND
        elif 'font' in filename or 'font' in content_type or filename.endswith(('.ttf', '.otf', '.woff', '.woff2')):
            return FileType.FONT
        else:
            return FileType.OTHER

    def _determine_file_type_from_key(self, key: str) -> FileType:
        """Determine file type from file key/path"""
        if not key:
            return FileType.OTHER

        key_lower = key.lower()

        if any(path in key_lower for path in ['photo', 'image', 'temp_photos', 'permanent/photos']):
            return FileType.PHOTO
        elif any(path in key_lower for path in ['audio', 'temp_audio', 'permanent/audio']):
            return FileType.AUDIO
        elif any(path in key_lower for path in ['pdf', 'permanent/pdf']):
            return FileType.PDF
        elif any(path in key_lower for path in ['waveform', 'permanent/waveforms']):
            return FileType.WAVEFORM
        elif any(path in key_lower for path in ['template']):
            return FileType.TEMPLATE
        elif any(path in key_lower for path in ['background']):
            return FileType.BACKGROUND
        elif any(path in key_lower for path in ['font']):
            return FileType.FONT
        else:
            # Try to determine from file extension
            if key_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                return FileType.PHOTO
            elif key_lower.endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac')):
                return FileType.AUDIO
            elif key_lower.endswith('.pdf'):
                return FileType.PDF
            else:
                return FileType.OTHER
