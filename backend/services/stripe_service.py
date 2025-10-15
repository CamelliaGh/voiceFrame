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

    def create_payment_intent(self, amount: int, email: str, order_id: str) -> Dict[str, Any]:
        """
        Create a Stripe PaymentIntent for anonymous checkout

        Args:
            amount: Amount in cents
            email: Customer email
            order_id: Internal order ID for tracking

        Returns:
            PaymentIntent object with client_secret
        """
        try:
            if not stripe.api_key:
                raise HTTPException(status_code=500, detail="Stripe not configured")

            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                automatic_payment_methods={'enabled': True},
                receipt_email=email,
                metadata={
                    'order_id': order_id,
                    'product': 'audio_poster',
                    'email': email
                },
                description=f'VocaFrame - Custom Audio Poster (Order: {order_id[:8]})',
                # Enable setup for future payments (optional)
                setup_future_usage='off_session',
            )

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
