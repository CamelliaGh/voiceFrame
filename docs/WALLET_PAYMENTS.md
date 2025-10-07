# Wallet Payments (Apple Pay & Google Pay)

## Overview
The application now supports Apple Pay and Google Pay payments using Stripe's Payment Request Button API. These payment methods provide a faster, more convenient checkout experience for mobile and desktop users.

## How It Works

### Frontend Implementation

#### 1. Payment Request Button Component (`PaymentRequestButton.tsx`)
- Creates a Stripe PaymentRequest object
- Checks browser/device support for Apple Pay or Google Pay
- Displays the appropriate payment button when supported
- Handles the payment flow when user authorizes payment

#### 2. Integration in PricingSection
- Shows wallet payment buttons after user enters email
- Creates payment intent early (when email is entered)
- Reuses the same payment intent for both wallet and card payments
- Shows "Or pay with card" separator when wallet buttons are visible

### When Wallet Buttons Appear

**Apple Pay** will show when:
- Using Safari on iOS/macOS
- Device has Apple Pay configured
- Website served over HTTPS

**Google Pay** will show when:
- Using Chrome on Android/Desktop
- Google Pay is available
- Website served over HTTPS

### Payment Flow

1. **User enters email** → Payment intent is created (debounced 500ms)
2. **Wallet button appears** (if browser supports it)
3. **User clicks Apple Pay/Google Pay**:
   - Native payment sheet opens
   - User authorizes payment with Face ID/Touch ID/PIN
   - Payment is confirmed using existing payment intent
   - Order is completed and download link provided
4. **Alternative: Card payment**:
   - User fills in card details and postal code
   - Same payment intent is reused
   - Payment confirmed with card details

## Backend Configuration

### Stripe Settings
The backend already supports wallet payments through:
```python
payment_intent = stripe.PaymentIntent.create(
    amount=amount,
    currency='usd',
    automatic_payment_methods={'enabled': True},  # ✅ This enables Apple Pay/Google Pay
    receipt_email=email,
    ...
)
```

The `automatic_payment_methods` setting automatically enables all supported payment methods including:
- Credit/debit cards
- Apple Pay
- Google Pay
- Other regional payment methods

## Testing

### Test on Real Devices
**Apple Pay:**
1. Open site on iPhone/iPad with Safari
2. Ensure device has Apple Pay configured (Wallet app)
3. Site must be served over HTTPS (localhost is fine for testing)
4. Enter email and Apple Pay button should appear

**Google Pay:**
1. Open site on Chrome browser
2. Have a Google account with payment method saved
3. Site must be served over HTTPS
4. Enter email and Google Pay button should appear

### Stripe Test Mode
When using Stripe test keys:
- Wallet buttons will appear in supported browsers
- Actual payment won't be charged (test mode)
- Use Stripe test cards for card payment testing

## Troubleshooting

### Button Not Appearing
- Check if site is served over HTTPS (required for production)
- Verify browser supports wallet payments
- Check browser console for errors
- Ensure email is entered (button only shows after email input)

### Payment Fails
- Check Stripe dashboard for error details
- Verify API keys are correct
- Check browser console for client-side errors
- Ensure payment intent is created successfully

## User Experience

### Benefits
- **Faster checkout**: No need to manually enter card details
- **More secure**: Biometric authentication (Face ID, Touch ID)
- **Better mobile experience**: Native payment sheet
- **Convenience**: Uses saved payment methods

### Fallback
If wallet payments aren't available:
- Standard card payment form is always available
- All users can complete payment with credit/debit card
- Postal code collected for card payments only

## Future Enhancements
- Add support for more payment methods (Link, PayPal)
- Collect shipping address (if needed for physical goods)
- Add payment method icons/logos
- Show payment method fee differences (if applicable)
- A/B test wallet button placement and styling

## Technical Notes

### Payment Intent Reuse
- Single payment intent created per session
- Reused for both wallet and card payments
- Prevents duplicate orders
- 500ms debounce on creation to avoid excessive API calls

### Security
- All payment data handled by Stripe
- No card data touches our servers
- PCI compliance maintained
- Biometric auth for wallet payments

### Browser Support
- Apple Pay: Safari 10+, iOS 10+
- Google Pay: Chrome 66+, Edge 79+
- Card payment: All modern browsers

## References
- [Stripe Payment Request Button API](https://stripe.com/docs/stripe-js/elements/payment-request-button)
- [Apple Pay Documentation](https://stripe.com/docs/apple-pay)
- [Google Pay Documentation](https://stripe.com/docs/google-pay)
