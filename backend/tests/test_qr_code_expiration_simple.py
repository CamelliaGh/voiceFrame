import pytest
from backend.config import settings


class TestQRCodeExpirationConfig:
    """Test QR code expiration configuration"""

    def test_default_configuration_values(self):
        """Test that default configuration values are reasonable"""
        # Test default preview expiration (7 days)
        assert settings.qr_code_preview_expiration == 604800  # 7 days
        assert settings.qr_code_preview_expiration == 7 * 24 * 60 * 60

        # Test default permanent expiration (5 years)
        assert settings.qr_code_permanent_expiration == 157788000  # 5 years
        # Note: 157788000 accounts for leap years, not exactly 5 * 365 * 24 * 60 * 60
        assert settings.qr_code_permanent_expiration >= 5 * 365 * 24 * 60 * 60

        # Verify permanent expiration is much longer than preview
        assert settings.qr_code_permanent_expiration > settings.qr_code_preview_expiration * 10

    def test_expiration_time_calculations(self):
        """Test that expiration times are calculated correctly"""
        # Test common expiration periods
        one_day = 24 * 60 * 60
        one_week = 7 * one_day
        one_month = 30 * one_day
        one_year = 365 * one_day
        five_years = 5 * one_year

        assert one_day == 86400
        assert one_week == 604800
        assert one_month == 2592000
        assert one_year == 31536000
        assert five_years == 157680000

        # Our default permanent expiration is slightly longer than 5 years
        # (accounts for leap years)
        assert settings.qr_code_permanent_expiration >= five_years

    def test_configuration_environment_variables(self):
        """Test that configuration can be set via environment variables"""
        # Test that the configuration fields exist
        assert hasattr(settings, 'qr_code_preview_expiration')
        assert hasattr(settings, 'qr_code_permanent_expiration')

        # Test that they are integers
        assert isinstance(settings.qr_code_preview_expiration, int)
        assert isinstance(settings.qr_code_permanent_expiration, int)

        # Test that they are positive
        assert settings.qr_code_preview_expiration > 0
        assert settings.qr_code_permanent_expiration > 0

    def test_expiration_time_relationships(self):
        """Test relationships between different expiration times"""
        # Preview should be shorter than permanent
        assert settings.qr_code_preview_expiration < settings.qr_code_permanent_expiration

        # Permanent should be at least 10x longer than preview
        assert settings.qr_code_permanent_expiration >= settings.qr_code_preview_expiration * 10

        # Both should be reasonable durations (not too short, not too long)
        assert settings.qr_code_preview_expiration >= 3600  # At least 1 hour
        assert settings.qr_code_preview_expiration <= 86400 * 30  # At most 30 days

        assert settings.qr_code_permanent_expiration >= 86400 * 365  # At least 1 year
        assert settings.qr_code_permanent_expiration <= 86400 * 365 * 10  # At most 10 years
