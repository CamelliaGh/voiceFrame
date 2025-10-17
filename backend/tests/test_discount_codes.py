"""
Tests for discount code functionality
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.services.stripe_service import StripeService
from backend.schemas import DiscountCodeValidationRequest, DiscountCodeValidationResponse


class TestDiscountCodeValidation:
    """Test discount code validation endpoint"""

    def test_validate_discount_code_success(self, client: TestClient):
        """Test successful discount code validation"""
        with patch('backend.main.stripe_service') as mock_stripe_service:
            # Mock successful validation
            mock_stripe_service.validate_promotion_code.return_value = {
                "valid": True,
                "discount_type": "percentage",
                "discount_value": 20,
                "coupon_id": "coupon_123",
                "promotion_code_id": "promo_123",
                "max_redemptions": 100,
                "times_redeemed": 5,
                "expires_at": 1234567890
            }

            response = client.post(
                "/api/validate-discount-code",
                json={"code": "SUMMER2024"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["discount_type"] == "percentage"
            assert data["discount_value"] == 20
            assert data["coupon_id"] == "coupon_123"
            assert data["message"] == "Discount code is valid"

    def test_validate_discount_code_invalid(self, client: TestClient):
        """Test invalid discount code validation"""
        with patch('backend.main.stripe_service') as mock_stripe_service:
            # Mock invalid code
            mock_stripe_service.validate_promotion_code.side_effect = Exception("Invalid discount code")

            response = client.post(
                "/api/validate-discount-code",
                json={"code": "INVALID"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert "Invalid discount code" in data["message"]

    def test_validate_discount_code_fixed_amount(self, client: TestClient):
        """Test fixed amount discount code validation"""
        with patch('backend.main.stripe_service') as mock_stripe_service:
            # Mock fixed amount discount
            mock_stripe_service.validate_promotion_code.return_value = {
                "valid": True,
                "discount_type": "fixed",
                "discount_value": 500,  # $5.00 in cents
                "coupon_id": "coupon_456",
                "promotion_code_id": "promo_456",
                "max_redemptions": None,
                "times_redeemed": 0,
                "expires_at": None
            }

            response = client.post(
                "/api/validate-discount-code",
                json={"code": "SAVE5"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["discount_type"] == "fixed"
            assert data["discount_value"] == 500

    def test_validate_discount_code_empty(self, client: TestClient):
        """Test validation with empty code"""
        response = client.post(
            "/api/validate-discount-code",
            json={"code": ""}
        )

        assert response.status_code == 422  # Validation error

    def test_validate_discount_code_missing(self, client: TestClient):
        """Test validation with missing code"""
        response = client.post(
            "/api/validate-discount-code",
            json={}
        )

        assert response.status_code == 422  # Validation error


class TestStripeServiceDiscountCodes:
    """Test StripeService discount code functionality"""

    def test_validate_promotion_code_success(self):
        """Test successful promotion code validation"""
        with patch('stripe.PromotionCode') as mock_promotion_code:
            # Mock Stripe API response
            mock_coupon = MagicMock()
            mock_coupon.id = "coupon_123"
            mock_coupon.amount_off = None
            mock_coupon.percent_off = 20

            mock_promo = MagicMock()
            mock_promo.coupon = mock_coupon
            mock_promo.id = "promo_123"
            mock_promo.max_redemptions = 100
            mock_promo.times_redeemed = 5
            mock_promo.expires_at = 1234567890

            mock_promotion_code.list.return_value = MagicMock(data=[mock_promo])

            with patch('time.time', return_value=1234567800):
                service = StripeService()
                result = service.validate_promotion_code("SUMMER2024")

                assert result["valid"] is True
                assert result["discount_type"] == "percentage"
                assert result["discount_value"] == 20
                assert result["coupon_id"] == "coupon_123"

    def test_validate_promotion_code_not_found(self):
        """Test promotion code not found"""
        with patch('stripe.PromotionCode') as mock_promotion_code:
            # Mock empty response
            mock_promotion_code.list.return_value = MagicMock(data=[])

            service = StripeService()

            with pytest.raises(Exception) as exc_info:
                service.validate_promotion_code("INVALID")

            assert "Invalid discount code" in str(exc_info.value)

    def test_validate_promotion_code_max_redemptions_reached(self):
        """Test promotion code with max redemptions reached"""
        with patch('stripe.PromotionCode') as mock_promotion_code:
            # Mock Stripe API response
            mock_coupon = MagicMock()
            mock_coupon.id = "coupon_123"
            mock_coupon.amount_off = None
            mock_coupon.percent_off = 20

            mock_promo = MagicMock()
            mock_promo.coupon = mock_coupon
            mock_promo.id = "promo_123"
            mock_promo.max_redemptions = 10
            mock_promo.times_redeemed = 10  # Max reached
            mock_promo.expires_at = None

            mock_promotion_code.list.return_value = MagicMock(data=[mock_promo])

            service = StripeService()

            with pytest.raises(Exception) as exc_info:
                service.validate_promotion_code("MAXEDOUT")

            assert "maximum redemptions" in str(exc_info.value)

    def test_validate_promotion_code_expired(self):
        """Test expired promotion code"""
        with patch('stripe.PromotionCode') as mock_promotion_code:
            # Mock Stripe API response
            mock_coupon = MagicMock()
            mock_coupon.id = "coupon_123"
            mock_coupon.amount_off = None
            mock_coupon.percent_off = 20

            mock_promo = MagicMock()
            mock_promo.coupon = mock_coupon
            mock_promo.id = "promo_123"
            mock_promo.max_redemptions = None
            mock_promo.times_redeemed = 0
            mock_promo.expires_at = 1234567800  # Expired

            mock_promotion_code.list.return_value = MagicMock(data=[mock_promo])

            with patch('time.time', return_value=1234567900):
                service = StripeService()

                with pytest.raises(Exception) as exc_info:
                    service.validate_promotion_code("EXPIRED")

                assert "expired" in str(exc_info.value)

    def test_create_payment_intent_with_promotion_code(self):
        """Test creating payment intent with promotion code"""
        with patch('stripe.PaymentIntent') as mock_payment_intent:
            # Mock successful payment intent creation
            mock_payment_intent.create.return_value = {
                "id": "pi_123",
                "client_secret": "pi_123_secret",
                "amount": 299,
                "currency": "usd"
            }

            service = StripeService()
            result = service.create_payment_intent(
                amount=299,
                email="test@example.com",
                order_id="order_123",
                promotion_code="SUMMER2024"
            )

            assert result["id"] == "pi_123"
            assert result["client_secret"] == "pi_123_secret"

            # Verify promotion code was passed to Stripe
            mock_payment_intent.create.assert_called_once()
            call_args = mock_payment_intent.create.call_args[1]
            assert call_args["promotion_code"] == "SUMMER2024"
            assert call_args["metadata"]["promotion_code"] == "SUMMER2024"

    def test_create_payment_intent_without_promotion_code(self):
        """Test creating payment intent without promotion code"""
        with patch('stripe.PaymentIntent') as mock_payment_intent:
            # Mock successful payment intent creation
            mock_payment_intent.create.return_value = {
                "id": "pi_123",
                "client_secret": "pi_123_secret",
                "amount": 299,
                "currency": "usd"
            }

            service = StripeService()
            result = service.create_payment_intent(
                amount=299,
                email="test@example.com",
                order_id="order_123"
            )

            assert result["id"] == "pi_123"
            assert result["client_secret"] == "pi_123_secret"

            # Verify promotion code was not passed to Stripe
            mock_payment_intent.create.assert_called_once()
            call_args = mock_payment_intent.create.call_args[1]
            assert "promotion_code" not in call_args
            assert "promotion_code" not in call_args["metadata"]


class TestPaymentIntentWithDiscountCodes:
    """Test payment intent creation with discount codes"""

    def test_payment_intent_schema_includes_promotion_code(self):
        """Test that PaymentIntentRequest schema includes promotion_code field"""
        from backend.schemas import PaymentIntentRequest

        # Test with promotion code
        request_with_code = PaymentIntentRequest(
            email="test@example.com",
            tier="standard",
            promotion_code="SUMMER2024"
        )
        assert request_with_code.promotion_code == "SUMMER2024"

        # Test without promotion code
        request_without_code = PaymentIntentRequest(
            email="test@example.com",
            tier="standard"
        )
        assert request_without_code.promotion_code is None

    def test_discount_code_validation_schema(self):
        """Test discount code validation schemas"""
        from backend.schemas import DiscountCodeValidationRequest, DiscountCodeValidationResponse

        # Test request schema
        request = DiscountCodeValidationRequest(code="SUMMER2024")
        assert request.code == "SUMMER2024"

        # Test response schema
        response = DiscountCodeValidationResponse(
            valid=True,
            discount_type="percentage",
            discount_value=20,
            message="Valid discount code"
        )
        assert response.valid is True
        assert response.discount_type == "percentage"
        assert response.discount_value == 20
