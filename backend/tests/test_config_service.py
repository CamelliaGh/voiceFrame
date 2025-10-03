"""
Tests for the configuration service
"""
from unittest.mock import MagicMock
import sys
import os

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.config_service import ConfigService
from backend.models import AdminConfig


def test_config_service_get_price_cents_default():
    """Test that get_price_cents returns default value when no config exists"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock query to return None (no config found)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    price = config_service.get_price_cents(mock_db)
    assert price == 299  # Default price


def test_config_service_get_price_cents_from_db():
    """Test that get_price_cents returns value from database"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock config object
    mock_config = MagicMock()
    mock_config.value = "399"  # $3.99

    # Mock query to return the config
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    price = config_service.get_price_cents(mock_db)
    assert price == 399


def test_config_service_get_config_as_int():
    """Test getting configuration as integer"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock config object
    mock_config = MagicMock()
    mock_config.value = "500"

    # Mock query to return the config
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    value = config_service.get_config_as_int(mock_db, "test_key", default=100)
    assert value == 500


def test_config_service_get_config_as_int_invalid():
    """Test getting configuration as integer with invalid value"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock config object with invalid integer value
    mock_config = MagicMock()
    mock_config.value = "not_a_number"

    # Mock query to return the config
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    value = config_service.get_config_as_int(mock_db, "test_key", default=100)
    assert value == 100  # Should return default


def test_config_service_get_config_as_bool():
    """Test getting configuration as boolean"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Test various boolean representations
    test_cases = [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("enabled", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("disabled", False),
    ]

    for value, expected in test_cases:
        mock_config = MagicMock()
        mock_config.value = value
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = config_service.get_config_as_bool(mock_db, "test_key", default=False)
        assert result == expected, f"Expected {expected} for value '{value}', got {result}"


def test_config_service_cache():
    """Test that configuration values are cached"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock config object
    mock_config = MagicMock()
    mock_config.value = "cached_value"

    # Mock query to return the config
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    # First call should query database
    value1 = config_service.get_config_value(mock_db, "test_key")
    assert value1 == "cached_value"
    assert mock_db.query.called

    # Reset mock to verify second call doesn't query database
    mock_db.reset_mock()

    # Second call should use cache
    value2 = config_service.get_config_value(mock_db, "test_key")
    assert value2 == "cached_value"
    assert not mock_db.query.called  # Should not query database again


def test_config_service_cache_invalidation():
    """Test cache invalidation"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock config object
    mock_config = MagicMock()
    mock_config.value = "initial_value"

    # Mock query to return the config
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    # First call caches the value
    value1 = config_service.get_config_value(mock_db, "test_key")
    assert value1 == "initial_value"

    # Invalidate cache
    config_service.invalidate_cache_key("test_key")

    # Update mock to return new value
    mock_config.value = "updated_value"

    # Next call should query database again
    value2 = config_service.get_config_value(mock_db, "test_key")
    assert value2 == "updated_value"


def test_config_service_clear_cache():
    """Test clearing entire cache"""
    config_service = ConfigService()
    mock_db = MagicMock()

    # Mock config object
    mock_config = MagicMock()
    mock_config.value = "test_value"

    # Mock query to return the config
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    # Cache a value
    config_service.get_config_value(mock_db, "test_key")
    assert "test_key" in config_service._cache

    # Clear cache
    config_service.clear_cache()
    assert len(config_service._cache) == 0


if __name__ == "__main__":
    # Run tests directly
    test_config_service_get_price_cents_default()
    test_config_service_get_price_cents_from_db()
    test_config_service_get_config_as_int()
    test_config_service_get_config_as_int_invalid()
    test_config_service_get_config_as_bool()
    test_config_service_cache()
    test_config_service_cache_invalidation()
    test_config_service_clear_cache()
    print("✅ All config service tests passed!")
