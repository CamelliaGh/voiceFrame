import os
import base64
import hashlib
from typing import Optional, BinaryIO
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from io import BytesIO

from ..config import settings


class EncryptionService:
    """Handles encryption and decryption of files for both local and S3 storage"""

    def __init__(self):
        self.local_key = self._get_or_generate_local_key()

    def _get_or_generate_local_key(self) -> bytes:
        """Get or generate local encryption key"""
        if settings.local_encryption_key:
            try:
                # Decode base64 key
                return base64.b64decode(settings.local_encryption_key)
            except Exception:
                # If decoding fails, generate new key
                pass

        # Generate new 32-byte (256-bit) key
        key = os.urandom(32)

        # In production, this should be stored securely
        if settings.debug:
            encoded_key = base64.b64encode(key).decode('utf-8')
            print(f"Generated local encryption key: {encoded_key}")
            print("Add this to your .env file as LOCAL_ENCRYPTION_KEY for persistence")

        return key

    def encrypt_file_content(self, file_content: bytes) -> bytes:
        """Encrypt file content using AES-256-GCM"""
        try:
            # Generate random IV
            iv = os.urandom(12)  # 96-bit IV for GCM

            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.local_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Encrypt the data
            ciphertext = encryptor.update(file_content) + encryptor.finalize()

            # Return IV + tag + ciphertext
            return iv + encryptor.tag + ciphertext

        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """Decrypt file content using AES-256-GCM"""
        try:
            if len(encrypted_content) < 28:  # IV (12) + tag (16) + minimum ciphertext
                raise ValueError("Invalid encrypted content")

            # Extract IV, tag, and ciphertext
            iv = encrypted_content[:12]
            tag = encrypted_content[12:28]
            ciphertext = encrypted_content[28:]

            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.local_key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt the data
            return decryptor.update(ciphertext) + decryptor.finalize()

        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Encrypt a file and optionally save to different path"""
        try:
            # Read original file
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Encrypt content
            encrypted_content = self.encrypt_file_content(file_content)

            # Determine output path
            if output_path is None:
                output_path = file_path + '.encrypted'

            # Write encrypted file
            with open(output_path, 'wb') as f:
                f.write(encrypted_content)

            return output_path

        except Exception as e:
            raise Exception(f"File encryption failed: {str(e)}")

    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None) -> str:
        """Decrypt a file and optionally save to different path"""
        try:
            # Read encrypted file
            with open(encrypted_file_path, 'rb') as f:
                encrypted_content = f.read()

            # Decrypt content
            decrypted_content = self.decrypt_file_content(encrypted_content)

            # Determine output path
            if output_path is None:
                if encrypted_file_path.endswith('.encrypted'):
                    output_path = encrypted_file_path[:-10]  # Remove .encrypted
                else:
                    output_path = encrypted_file_path + '.decrypted'

            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted_content)

            return output_path

        except Exception as e:
            raise Exception(f"File decryption failed: {str(e)}")

    def get_s3_encryption_config(self) -> dict:
        """Get S3 encryption configuration based on settings"""
        if settings.use_kms_encryption and settings.s3_kms_key_id:
            return {
                'ServerSideEncryption': 'aws:kms',
                'SSEKMSKeyId': settings.s3_kms_key_id
            }
        else:
            return {
                'ServerSideEncryption': 'AES256'
            }

    def verify_encryption(self, file_path: str) -> bool:
        """Verify that a file is properly encrypted (for local files)"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # Check if file has minimum length for encrypted content
            if len(content) < 28:
                return False

            # Try to decrypt to verify encryption
            self.decrypt_file_content(content)
            return True

        except Exception:
            return False

    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key and return as base64 string"""
        key = os.urandom(32)
        return base64.b64encode(key).decode('utf-8')

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = kdf.derive(password.encode())
        return key, salt
