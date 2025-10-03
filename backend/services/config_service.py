"""
Configuration Service

Handles retrieval and management of application configuration settings
stored in the database.
"""

from typing import Optional, Union
from sqlalchemy.orm import Session
from ..models import AdminConfig


class ConfigService:
    """Service for managing application configuration settings"""

    def __init__(self):
        self._cache = {}  # Simple in-memory cache for frequently accessed configs

    def get_config_value(self, db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value by key

        Args:
            db: Database session
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value as string or default
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        config = db.query(AdminConfig).filter(
            AdminConfig.key == key,
            AdminConfig.is_active == True
        ).first()

        if config:
            # Cache the value
            self._cache[key] = config.value
            return config.value

        return default

    def get_config_as_int(self, db: Session, key: str, default: int = 0) -> int:
        """
        Get a configuration value as integer

        Args:
            db: Database session
            key: Configuration key
            default: Default value if key not found or conversion fails

        Returns:
            Configuration value as integer
        """
        value = self.get_config_value(db, key)
        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_config_as_float(self, db: Session, key: str, default: float = 0.0) -> float:
        """
        Get a configuration value as float

        Args:
            db: Database session
            key: Configuration key
            default: Default value if key not found or conversion fails

        Returns:
            Configuration value as float
        """
        value = self.get_config_value(db, key)
        if value is None:
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_config_as_bool(self, db: Session, key: str, default: bool = False) -> bool:
        """
        Get a configuration value as boolean

        Args:
            db: Database session
            key: Configuration key
            default: Default value if key not found or conversion fails

        Returns:
            Configuration value as boolean
        """
        value = self.get_config_value(db, key)
        if value is None:
            return default

        # Handle various boolean representations
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')

        return bool(value)

    def get_price_cents(self, db: Session) -> int:
        """
        Get the current price in cents

        Args:
            db: Database session

        Returns:
            Price in cents (default: 299 for $2.99)
        """
        return self.get_config_as_int(db, "price_cents", default=299)

    def clear_cache(self):
        """Clear the configuration cache"""
        self._cache.clear()

    def invalidate_cache_key(self, key: str):
        """Invalidate a specific cache key"""
        if key in self._cache:
            del self._cache[key]


# Global instance
config_service = ConfigService()
