import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

from backend.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Test the encryption service functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.encryption_service = EncryptionService()
        self.test_content = b"This is test content for encryption"

    def test_encrypt_decrypt_content(self):
        """Test basic encryption and decryption of content"""
        # Encrypt content
        encrypted_content = self.encryption_service.encrypt_file_content(self.test_content)

        # Verify encrypted content is different from original
        assert encrypted_content != self.test_content
        assert len(encrypted_content) > len(self.test_content)

        # Decrypt content
        decrypted_content = self.encryption_service.decrypt_file_content(encrypted_content)

        # Verify decrypted content matches original
        assert decrypted_content == self.test_content

    def test_encrypt_decrypt_file(self):
        """Test file encryption and decryption"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(self.test_content)
            temp_file_path = temp_file.name

        encrypted_file_path = None
        decrypted_file_path = None

        try:
            # Encrypt file
            encrypted_file_path = self.encryption_service.encrypt_file(temp_file_path)

            # Verify encrypted file exists and is different from original
            assert os.path.exists(encrypted_file_path)
            with open(encrypted_file_path, 'rb') as f:
                encrypted_content = f.read()
            assert encrypted_content != self.test_content

            # Decrypt file
            decrypted_file_path = self.encryption_service.decrypt_file(encrypted_file_path)

            # Verify decrypted file exists and matches original
            assert os.path.exists(decrypted_file_path)
            with open(decrypted_file_path, 'rb') as f:
                decrypted_content = f.read()
            assert decrypted_content == self.test_content

        finally:
            # Clean up files
            if encrypted_file_path and os.path.exists(encrypted_file_path):
                os.unlink(encrypted_file_path)
            if decrypted_file_path and os.path.exists(decrypted_file_path):
                os.unlink(decrypted_file_path)
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_verify_encryption(self):
        """Test encryption verification"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(self.test_content)
            temp_file_path = temp_file.name

        try:
            # Verify unencrypted file returns False
            assert not self.encryption_service.verify_encryption(temp_file_path)

            # Encrypt file
            encrypted_file_path = self.encryption_service.encrypt_file(temp_file_path)

            # Verify encrypted file returns True
            assert self.encryption_service.verify_encryption(encrypted_file_path)

            # Clean up
            os.unlink(encrypted_file_path)

        finally:
            os.unlink(temp_file_path)

    def test_get_s3_encryption_config_default(self):
        """Test default S3 encryption configuration"""
        with patch('backend.services.encryption_service.settings') as mock_settings:
            mock_settings.use_kms_encryption = False
            mock_settings.s3_kms_key_id = ""

            config = self.encryption_service.get_s3_encryption_config()

            assert config == {'ServerSideEncryption': 'AES256'}

    def test_get_s3_encryption_config_kms(self):
        """Test KMS encryption configuration"""
        with patch('backend.services.encryption_service.settings') as mock_settings:
            mock_settings.use_kms_encryption = True
            mock_settings.s3_kms_key_id = "arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012"

            config = self.encryption_service.get_s3_encryption_config()

            assert config == {
                'ServerSideEncryption': 'aws:kms',
                'SSEKMSKeyId': 'arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012'
            }

    def test_generate_encryption_key(self):
        """Test encryption key generation"""
        key = EncryptionService.generate_encryption_key()

        # Verify key is a base64 string
        assert isinstance(key, str)
        assert len(key) > 0

        # Verify key can be decoded
        decoded_key = key.encode('utf-8')
        assert len(decoded_key) > 0

    def test_derive_key_from_password(self):
        """Test key derivation from password"""
        password = "test_password"
        key, salt = EncryptionService.derive_key_from_password(password)

        # Verify key and salt are bytes
        assert isinstance(key, bytes)
        assert isinstance(salt, bytes)

        # Verify key length (should be 32 bytes for AES-256)
        assert len(key) == 32

        # Verify salt length (should be 16 bytes)
        assert len(salt) == 16

        # Verify same password with same salt produces same key
        key2, salt2 = EncryptionService.derive_key_from_password(password, salt)
        assert key == key2
        assert salt == salt2

    def test_encryption_with_empty_content(self):
        """Test encryption with empty content"""
        empty_content = b""

        # Encrypt empty content
        encrypted_content = self.encryption_service.encrypt_file_content(empty_content)

        # Decrypt empty content
        decrypted_content = self.encryption_service.decrypt_file_content(encrypted_content)

        # Verify empty content is preserved
        assert decrypted_content == empty_content

    def test_encryption_with_large_content(self):
        """Test encryption with large content"""
        large_content = b"x" * 1024 * 1024  # 1MB of data

        # Encrypt large content
        encrypted_content = self.encryption_service.encrypt_file_content(large_content)

        # Decrypt large content
        decrypted_content = self.encryption_service.decrypt_file_content(encrypted_content)

        # Verify large content is preserved
        assert decrypted_content == large_content

    def test_invalid_encrypted_content(self):
        """Test decryption with invalid content"""
        invalid_content = b"invalid encrypted content"

        # Should raise exception when trying to decrypt invalid content
        with pytest.raises(Exception, match="Decryption failed"):
            self.encryption_service.decrypt_file_content(invalid_content)

    def test_corrupted_encrypted_content(self):
        """Test decryption with corrupted content"""
        # First encrypt valid content
        encrypted_content = self.encryption_service.encrypt_file_content(self.test_content)

        # Corrupt the content by changing some bytes
        corrupted_content = encrypted_content[:-10] + b"corrupted"

        # Should raise exception when trying to decrypt corrupted content
        with pytest.raises(Exception, match="Decryption failed"):
            self.encryption_service.decrypt_file_content(corrupted_content)
