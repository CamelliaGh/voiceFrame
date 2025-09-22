import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException
import uuid
from typing import BinaryIO, Optional
import os
from datetime import datetime

from ..config import settings
from .encryption_service import EncryptionService

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

    async def upload_file(self, file: UploadFile, prefix: str = "") -> str:
        """Upload file to S3 or local storage and return the key/path"""
        file_extension = self._get_file_extension(file.filename)
        file_key = f"{prefix}/{uuid.uuid4()}{file_extension}"

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

    def delete_file(self, key: str):
        """Delete file from storage"""
        if self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=settings.s3_bucket, Key=key)
            except ClientError:
                pass  # File might not exist
        else:
            file_path = os.path.join(self.local_storage_path, key)
            if os.path.exists(file_path):
                os.remove(file_path)

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
