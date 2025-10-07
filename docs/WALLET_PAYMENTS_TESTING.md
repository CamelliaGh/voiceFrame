# Testing Apple Pay & Google Pay

## Quick Test Guide

### On iPhone (Apple Pay)
1. **Open Safari** on your iPhone
2. Navigate to your site (must be HTTPS in production, localhost works for development)
3. Create your audio poster (upload photo and audio)
4. Go to the payment page
5. **Enter your email address**
6. **Apple Pay button should appear** above the card form
7. Click the Apple Pay button
8. Authenticate with Face ID/Touch ID
9. Payment completes and you get your download link

### On Android/Chrome (Google Pay)
1. **Open Chrome browser** on Android or desktop
2. Make sure you have Google Pay set up with a payment method
3. Navigate to your site (must be HTTPS in production)
4. Create your audio poster
5. Go to the payment page
6. **Enter your email address**
7. **Google Pay button should appear** above the card form
8. Click the Google Pay button
9. Authenticate and complete payment

### On Desktop Safari (Apple Pay)
1. **Open Safari** on macOS (with Apple Pay configured on connected iPhone/Watch)
2. Navigate to your site
3. Create your audio poster
4. Go to the payment page
5. **Enter your email address**
6. **Apple Pay button should appear**
7. Click the button and confirm on your paired device

## What You Should See

### Before Entering Email
- Standard card payment form
- No wallet payment buttons visible

### After Entering Email (on supported device/browser)
- **Apple Pay or Google Pay button appears** (dark button with logo)
- "Or pay with card" separator text
- Card form below as fallback

### What the Buttons Look Like
- **Apple Pay**: Black button with Apple Pay logo
- **Google Pay**: Black button with Google Pay logo
- Both buttons say "Buy with [Apple/Google] Pay"
- Height: 48px (same as other form elements)

## If Buttons Don't Appear

This is normal if:
- Using Chrome/Firefox (only supports Google Pay, not Apple Pay)
- Using Safari without Apple Pay configured
- Site is not HTTPS (required in production)
- Browser doesn't support the Payment Request API
- No payment method saved in wallet

**The card payment form always works as a fallback!**

## Testing Payment Flow

### With Stripe Test Keys
1. Wallet buttons will appear in supported browsers
2. Payment won't actually be charged (test mode)
3. Use real wallet authentication (Face ID, etc.)
4. Stripe records the test payment

### Test Card (Fallback)
If wallet payment isn't available, use:
- **Card**: 4242 4242 4242 4242
- **Expiry**: Any future date
- **CVC**: Any 3 digits
- **ZIP**: Any 5 digits

## Development Environment

### Local Testing (HTTPS)
Apple Pay and Google Pay require HTTPS even for testing. Options:

1. **Use ngrok** (easiest):
   ```bash
   ngrok http 5173
   # Use the https:// URL on your phone
   ```

2. **Self-signed certificate** (advanced):
   ```bash
   # Generate certificate
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

   # Update vite.config.ts to use HTTPS
   ```

3. **Use deployed staging site** (recommended):
   - Deploy to staging environment with proper HTTPS
   - Test on real devices with real domain

### Without HTTPS (localhost)
- Wallet buttons will **not appear** on real mobile devices
- Card payment works fine for development testing
- Use production/staging for wallet payment testing

## Monitoring Payments

### Stripe Dashboard
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Check **Payments** section
3. Look for payment method type:
   - `card` - Regular card payment
   - `apple_pay` - Apple Pay payment
   - `google_pay` - Google Pay payment

### Application Logs
- Check browser console for payment flow logs
- Backend logs show payment intent creation
- Order completion logs show successful payments

## Troubleshooting

### Button appears but payment fails
- Check Stripe API keys are correct
- Verify payment intent is created successfully
- Check browser console for specific error
- Review Stripe Dashboard for declined payment details

### Button doesn't appear at all
- Confirm HTTPS is being used
- Check if wallet is configured on device
- Try different browser (Safari for Apple Pay, Chrome for Google Pay)
- Verify email is entered (button only shows after email)

### Payment succeeds but order fails
- Check backend logs for order completion errors
- Verify database connection
- Check PDF generation service
- Review email sending service

## Success Indicators

✅ **Everything working correctly when:**
- Wallet button appears after entering email
- Clicking button opens native payment sheet
- Payment authenticates with biometrics
- Success page shows with download link
- Email is sent with download link
- Stripe dashboard shows successful payment
- Order appears in admin dashboard

## Production Checklist

Before launching wallet payments in production:

- [ ] Site has valid SSL certificate (HTTPS)
- [ ] Stripe production keys are configured
- [ ] Apple Pay domain verification complete (if required)
- [ ] Test on real iPhone with Safari
- [ ] Test on real Android with Chrome
- [ ] Test fallback card payment still works
- [ ] Monitor Stripe Dashboard for test transactions
- [ ] Set up payment failure alerts
- [ ] Document any payment issues in logs

## Support Resources

- [Stripe Payment Request Button Docs](https://stripe.com/docs/stripe-js/elements/payment-request-button)
- [Apple Pay on the Web](https://developer.apple.com/apple-pay/)
- [Google Pay Web Integration](https://developers.google.com/pay/api/web)
- Internal docs: `docs/WALLET_PAYMENTS.md`
