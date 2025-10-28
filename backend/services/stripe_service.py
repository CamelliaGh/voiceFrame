import stripe
from typing import Dict, Any
from fastapi import HTTPException

from ..config import settings

class StripeService:
    """Handles Stripe payment processing for anonymous checkout"""

    def __init__(self):
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
        else:
            print("Warning: Stripe secret key not configured")

    def create_payment_intent(self, amount: int, email: str, order_id: str, promotion_code: str = None) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent for anonymous checkout

        Args:
            amount: Amount in cents
            email: Customer email
            order_id: Internal order ID for tracking
            promotion_code: Optional Stripe promotion code for discounts

        Returns:
            PaymentIntent object with client_secret
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            final_amount = amount
            discount_info = None

            # Validate promotion code if provided
            promotion_code_obj = None
            if promotion_code:
                try:
                    print(f"DEBUG: Validating promotion code: {promotion_code}")
                    # Validate the promotion code to get its details
                    promotion_codes = stripe.PromotionCode.list(
                        code=promotion_code,
                        active=True,
                        limit=1
                    )

                    print(f"DEBUG: Promotion code lookup result: {len(promotion_codes.data)} codes found")
                    if not promotion_codes.data:
                        print(f"DEBUG: No promotion codes found for: {promotion_code}")
                        raise HTTPException(status_code=404, detail="Invalid discount code")

                    promotion_code_obj = promotion_codes.data[0]
                    coupon = promotion_code_obj.coupon
                    print(f"DEBUG: Found promotion code: {promotion_code_obj.id}, coupon: {coupon.id}")

                    # Check if code is still valid
                    if promotion_code_obj.max_redemptions and promotion_code_obj.times_redeemed >= promotion_code_obj.max_redemptions:
                        print(f"DEBUG: Promotion code has reached max redemptions: {promotion_code_obj.times_redeemed}/{promotion_code_obj.max_redemptions}")
                        raise HTTPException(status_code=400, detail="Discount code has reached maximum redemptions")

                    # Check expiration date
                    import time
                    if promotion_code_obj.expires_at and promotion_code_obj.expires_at < int(time.time()):
                        print(f"DEBUG: Promotion code has expired: {promotion_code_obj.expires_at} < {int(time.time())}")
                        raise HTTPException(status_code=400, detail="Discount code has expired")

                    print(f"DEBUG: Promotion code validation successful")

                except stripe.error.StripeError as e:
                    print(f"DEBUG: Stripe error validating promotion code: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Invalid promotion code: {str(e)}")
                except HTTPException:
                    # Re-raise HTTP exceptions as-is
                    raise
                except Exception as e:
                    print(f"DEBUG: Unexpected error validating promotion code: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Promotion code validation failed: {str(e)}")

            payment_intent_params = {
                'amount': amount,  # Use original amount, let Stripe apply discount
                'currency': 'usd',
                'automatic_payment_methods': {'enabled': True},
                'receipt_email': email,
                'metadata': {
                    'order_id': order_id,
                    'product': 'audio_poster',
                    'email': email
                },
                'description': f'VocaFrame - Custom Audio Poster (Order: {order_id[:8]})',
                # Enable setup for future payments (optional)
                'setup_future_usage': 'off_session',
            }

            # Create PaymentIntent first
            print(f"DEBUG: Creating PaymentIntent with params: amount={amount}, email={email}, order_id={order_id}")
            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)
            print(f"DEBUG: PaymentIntent created successfully: {payment_intent.id}")

            # Add promotion code metadata for tracking (promotion codes are applied client-side)
            if promotion_code and promotion_code_obj:
                try:
                    print(f"DEBUG: Adding promotion code metadata to PaymentIntent")
                    # Update metadata with promotion code info
                    stripe.PaymentIntent.modify(
                        payment_intent.id,
                        metadata={
                            **payment_intent_params['metadata'],
                            'promotion_code': promotion_code,
                            'promotion_code_id': promotion_code_obj.id,
                            'coupon_id': promotion_code_obj.coupon.id,
                            'coupon_type': 'amount_off' if promotion_code_obj.coupon.amount_off else 'percent_off',
                            'coupon_value': str(promotion_code_obj.coupon.amount_off or promotion_code_obj.coupon.percent_off)
                        }
                    )
                    print(f"DEBUG: Promotion code metadata added successfully")
                except stripe.error.StripeError as e:
                    # If metadata update fails, log but don't fail the entire request
                    print(f"Warning: Failed to update PaymentIntent metadata with promotion code {promotion_code}: {str(e)}")

            print(f"DEBUG: Returning PaymentIntent: {payment_intent.id}")
            return payment_intent

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payment creation failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def verify_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Verify that a payment has been completed successfully

        Args:
            payment_intent_id: The Stripe PaymentIntent ID

        Returns:
            PaymentIntent object
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return payment_intent

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payment verification failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def refund_payment(self, payment_intent_id: str, amount: int = None,
                      reason: str = 'requested_by_customer') -> Dict[str, Any]:
        """
        Refund a payment (for customer service purposes)

        Args:
            payment_intent_id: The Stripe PaymentIntent ID
            amount: Amount to refund in cents (None for full refund)
            reason: Reason for refund

        Returns:
            Refund object
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            refund_params = {
                'payment_intent': payment_intent_id,
                'reason': reason
            }

            if amount:
                refund_params['amount'] = amount

            refund = stripe.Refund.create(**refund_params)

            return refund

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Refund failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events

        Args:
            payload: Raw webhook payload
            sig_header: Stripe signature header

        Returns:
            Event object
        """
        try:
            if not settings.stripe_webhook_secret:
                raise HTTPException(status_code=500, detail="Webhook secret not configured")

            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )

            return event

        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

    def get_payment_methods(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Get available payment methods for a PaymentIntent

        Args:
            payment_intent_id: The Stripe PaymentIntent ID

        Returns:
            Available payment methods
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                'automatic_payment_methods': payment_intent.automatic_payment_methods,
                'payment_method_types': payment_intent.payment_method_types,
                'currency': payment_intent.currency,
                'amount': payment_intent.amount
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Failed to get payment methods: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def create_customer(self, email: str, name: str = None) -> Dict[str, Any]:
        """
        Create a Stripe customer (for future use if implementing subscriptions)

        Args:
            email: Customer email
            name: Customer name (optional)

        Returns:
            Customer object
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            customer_params = {'email': email}
            if name:
                customer_params['name'] = name

            customer = stripe.Customer.create(**customer_params)

            return customer

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Customer creation failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def calculate_application_fee(self, amount: int) -> int:
        """
        Calculate application fee for marketplace scenarios
        (Not needed for basic implementation, but useful for future expansion)

        Args:
            amount: Transaction amount in cents

        Returns:
            Application fee in cents
        """
        # Example: 2.9% + 30¢ fee structure
        return int(amount * 0.029) + 30

    def validate_promotion_code(self, code: str) -> Dict[str, Any]:
        """
        Validate a Stripe promotion code and return discount information

        Args:
            code: The promotion code to validate

        Returns:
            Dictionary with validation results and discount information
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            # Retrieve promotion code from Stripe
            promotion_codes = stripe.PromotionCode.list(
                code=code,
                active=True,
                limit=1
            )

            if not promotion_codes.data:
                raise HTTPException(status_code=404, detail="Invalid discount code")

            promotion_code = promotion_codes.data[0]
            coupon = promotion_code.coupon

            # Check if code is still valid
            if promotion_code.max_redemptions and promotion_code.times_redeemed >= promotion_code.max_redemptions:
                raise HTTPException(status_code=400, detail="Discount code has reached maximum redemptions")

            # Check expiration date
            import time
            if promotion_code.expires_at and promotion_code.expires_at < int(time.time()):
                raise HTTPException(status_code=400, detail="Discount code has expired")

            # Determine discount type and value
            discount_type = "fixed" if coupon.amount_off else "percentage"
            discount_value = coupon.amount_off or coupon.percent_off

            return {
                "valid": True,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "coupon_id": coupon.id,
                "promotion_code_id": promotion_code.id,
                "max_redemptions": promotion_code.max_redemptions,
                "times_redeemed": promotion_code.times_redeemed,
                "expires_at": promotion_code.expires_at
            }

        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Error validating code: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def format_amount_for_display(self, amount: int, currency: str = 'usd') -> str:
        """
        Format amount for display purposes

        Args:
            amount: Amount in cents
            currency: Currency code

        Returns:
            Formatted amount string
        """
        if currency.lower() == 'usd':
            return f"${amount / 100:.2f}"
        else:
            # For other currencies, you'd need proper formatting logic
            return f"{amount / 100:.2f} {currency.upper()}"
