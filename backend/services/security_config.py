"""
Security Configuration Service

This service provides secure configuration management and validation
to prevent hardcoded credentials and security vulnerabilities.
"""

import os
import secrets
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Secure configuration management service"""

    def __init__(self):
        self.required_env_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'S3_BUCKET',
            'STRIPE_SECRET_KEY',
            'SENDGRID_API_KEY'
        ]

        self.sensitive_env_vars = [
            'SECRET_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET',
            'SENDGRID_API_KEY',
            'LOCAL_ENCRYPTION_KEY'
        ]

    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate that all required environment variables are set
        and check for security issues
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_vars': [],
            'security_issues': []
        }

        # Check for required environment variables
        for var in self.required_env_vars:
            if not os.getenv(var):
                validation_result['missing_vars'].append(var)
                validation_result['valid'] = False

        # Check for hardcoded credentials in environment variables
        for var in self.sensitive_env_vars:
            value = os.getenv(var)
            if value:
                if self._is_hardcoded_credential(value):
                    validation_result['security_issues'].append(f"Hardcoded credential detected in {var}")
                    validation_result['warnings'].append(f"Consider using a secrets management service for {var}")

        # Check for default/example values
        default_values = {
            'SECRET_KEY': ['your-secret-key-change-this', 'your-super-secret-key-change-this-in-production'],
            'AWS_ACCESS_KEY_ID': ['your_aws_access_key', 'AKIAIOSFODNN7EXAMPLE'],
            'AWS_SECRET_ACCESS_KEY': ['your_aws_secret_key', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'],
            'STRIPE_SECRET_KEY': ['sk_test_your_stripe_secret_key'],
            'SENDGRID_API_KEY': ['sendgrid_api_key']
        }

        for var, defaults in default_values.items():
            value = os.getenv(var)
            if value and value in defaults:
                validation_result['security_issues'].append(f"Default/example value detected in {var}")
                validation_result['valid'] = False

        # Check for weak secret keys
        secret_key = os.getenv('SECRET_KEY')
        if secret_key and len(secret_key) < 32:
            validation_result['security_issues'].append("SECRET_KEY is too short (minimum 32 characters)")
            validation_result['valid'] = False

        # Check for debug mode in production
        if os.getenv('DEBUG', '').lower() == 'true' and os.getenv('ENVIRONMENT') == 'production':
            validation_result['warnings'].append("Debug mode is enabled in production environment")

        return validation_result

    def generate_secure_secret_key(self, length: int = 64) -> str:
        """Generate a cryptographically secure secret key"""
        return secrets.token_urlsafe(length)

    def generate_encryption_key(self) -> str:
        """Generate a secure encryption key for local file encryption"""
        key = Fernet.generate_key()
        return base64.b64encode(key).decode('utf-8')

    def derive_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Derive a key from a password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def mask_sensitive_value(self, value: str, show_chars: int = 4) -> str:
        """Mask sensitive values for logging"""
        if not value or len(value) <= show_chars:
            return "*" * len(value) if value else ""

        return value[:show_chars] + "*" * (len(value) - show_chars)

    def _is_hardcoded_credential(self, value: str) -> bool:
        """Check if a value looks like a hardcoded credential"""
        hardcoded_patterns = [
            'your_',
            'test_',
            'example',
            'change-this',
            'replace-me',
            'dummy',
            'placeholder'
        ]

        value_lower = value.lower()
        return any(pattern in value_lower for pattern in hardcoded_patterns)

    def get_secure_config_summary(self) -> Dict[str, Any]:
        """Get a summary of configuration security status"""
        validation = self.validate_environment()

        return {
            'environment_valid': validation['valid'],
            'missing_variables': validation['missing_vars'],
            'security_issues': validation['security_issues'],
            'warnings': validation['warnings'],
            'sensitive_vars_configured': len([var for var in self.sensitive_env_vars if os.getenv(var)]),
            'total_sensitive_vars': len(self.sensitive_env_vars)
        }

class SecretsManager:
    """Secrets management service for production environments"""

    def __init__(self):
        self.providers = {
            'aws': self._get_aws_secret,
            'azure': self._get_azure_secret,
            'gcp': self._get_gcp_secret,
            'env': self._get_env_secret
        }

    def get_secret(self, secret_name: str, provider: str = 'env') -> Optional[str]:
        """
        Get a secret from the specified provider

        Args:
            secret_name: Name of the secret to retrieve
            provider: Provider to use ('aws', 'azure', 'gcp', 'env')

        Returns:
            Secret value or None if not found
        """
        try:
            if provider in self.providers:
                return self.providers[provider](secret_name)
            else:
                logger.error(f"Unknown secrets provider: {provider}")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name} from {provider}: {str(e)}")
            return None

    def _get_aws_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except ImportError:
            logger.error("boto3 not available for AWS Secrets Manager")
            return None
        except ClientError as e:
            logger.error(f"AWS Secrets Manager error: {str(e)}")
            return None

    def _get_azure_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=os.getenv('AZURE_KEY_VAULT_URL'), credential=credential)
            secret = client.get_secret(secret_name)
            return secret.value
        except ImportError:
            logger.error("Azure SDK not available for Key Vault")
            return None
        except Exception as e:
            logger.error(f"Azure Key Vault error: {str(e)}")
            return None

    def _get_gcp_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Google Cloud Secret Manager"""
        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except ImportError:
            logger.error("Google Cloud SDK not available for Secret Manager")
            return None
        except Exception as e:
            logger.error(f"Google Cloud Secret Manager error: {str(e)}")
            return None

    def _get_env_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from environment variables"""
        return os.getenv(secret_name)

# Global instances
security_config = SecurityConfig()
secrets_manager = SecretsManager()
