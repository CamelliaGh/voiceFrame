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

    def get_discount_percentage(self, db: Session) -> int:
        """
        Get the current discount percentage

        Args:
            db: Database session

        Returns:
            Discount percentage (default: 0 for no discount)
        """
        return self.get_config_as_int(db, "discount_percentage", default=0)

    def get_discount_enabled(self, db: Session) -> bool:
        """
        Check if discount is currently enabled

        Args:
            db: Database session

        Returns:
            True if discount is enabled, False otherwise
        """
        return self.get_config_as_bool(db, "discount_enabled", default=False)

    def get_discounted_price_cents(self, db: Session) -> dict:
        """
        Get pricing information including discount

        Args:
            db: Database session

        Returns:
            Dictionary with original_price, discount_percentage, discounted_price, and discount_enabled
        """
        original_price = self.get_price_cents(db)
        discount_percentage = self.get_discount_percentage(db)
        discount_enabled = self.get_discount_enabled(db)

        # Validate discount percentage
        if discount_percentage < 0:
            discount_percentage = 0
        elif discount_percentage > 100:
            discount_percentage = 100

        # Validate original price
        if original_price <= 0:
            original_price = 299  # Default fallback price

        if discount_enabled and discount_percentage > 0:
            discount_amount = int(original_price * discount_percentage / 100)
            discounted_price = original_price - discount_amount

            # Ensure discounted price is never negative or zero
            if discounted_price <= 0:
                discounted_price = 1  # Minimum price of 1 cent
                discount_amount = original_price - discounted_price
        else:
            discount_amount = 0
            discounted_price = original_price

        return {
            "original_price": original_price,
            "discount_percentage": discount_percentage,
            "discount_amount": discount_amount,
            "discounted_price": discounted_price,
            "discount_enabled": discount_enabled
        }

    def validate_discount_config(self, db: Session, discount_percentage: int, discount_enabled: bool) -> dict:
        """
        Validate discount configuration before saving

        Args:
            db: Database session
            discount_percentage: Proposed discount percentage
            discount_enabled: Whether discount should be enabled

        Returns:
            Dictionary with validation results and any errors
        """
        errors = []
        warnings = []

        # Validate discount percentage
        if discount_percentage < 0:
            errors.append("Discount percentage cannot be negative")
        elif discount_percentage > 100:
            errors.append("Discount percentage cannot exceed 100%")
        elif discount_percentage > 90:
            warnings.append("Discount percentage over 90% may result in very low prices")

        # Check if discount would result in unreasonably low prices
        if discount_enabled and discount_percentage > 0:
            original_price = self.get_price_cents(db)
            discounted_price = original_price - int(original_price * discount_percentage / 100)

            if discounted_price <= 0:
                errors.append(f"Discount of {discount_percentage}% would result in zero or negative price")
            elif discounted_price < 50:  # Less than $0.50
                warnings.append(f"Discount would result in very low price: ${discounted_price / 100:.2f}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def clear_cache(self):
        """Clear the configuration cache"""
        self._cache.clear()

    def invalidate_cache_key(self, key: str):
        """Invalidate a specific cache key"""
        if key in self._cache:
            del self._cache[key]


# Global instance
config_service = ConfigService()
