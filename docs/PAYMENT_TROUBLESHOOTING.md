# Payment Error Fixes

## Issues Fixed ✅

### 1. **422 Payment Error** - FIXED
**Problem**: Frontend was sending `tier: 'standard'` but backend only accepted `tier: 'download'`

**Solution**: Updated `backend/schemas.py` to accept all tier values:
```python
tier: Literal["download", "standard", "premium"] = "download"
```

### 2. **Stripe Wallets Warning** - FIXED
**Problem**: `[Stripe.js] Unrecognized create() parameter: wallets`

**Solution**: Removed invalid `wallets` parameter from CardElement options. The Payment Request Button API (for Apple Pay/Google Pay) requires a different implementation approach.

**Note**: Apple Pay/Google Pay can be added later using the Payment Request Button API, which is a separate component from CardElement.

### 3. **Missing Session Token** - FIXED
**Problem**: `completeOrder()` wasn't sending the required `session_token`

**Solution**: Updated frontend to pass session token:
```typescript
completeOrder(order_id, paymentIntent.id, session.session_token)
```

---

## Remaining Issues ⚠️

### QUIC Protocol Errors (Lower Priority)

These errors indicate HTTP/3 (QUIC) connection issues:
```
Failed to load resource: net::ERR_QUIC_PROTOCOL_ERROR
- /backgrounds/beautiful-roses-great-white-wooden-background-with-space-right.jpg
- vintage-4IofzG4D.ttf
- classic-C-Ab5JES.ttf
- elegant-CwCW13Ks.ttf
- modern-CuD15gln.ttf
```

#### What This Means:
- Browser trying to use HTTP/3 (QUIC protocol)
- Connection failing, falling back to HTTP/2
- Files still load (via fallback), but with delays

#### Possible Causes:
1. **Nginx QUIC/HTTP3 not configured** (most likely)
2. **CDN/proxy interference**
3. **Firewall blocking UDP port 443**
4. **Client network issues**

#### Solutions:

##### Option 1: Disable HTTP/3 (Quickest Fix)
If HTTP/3 isn't needed, you can hint browsers to not attempt it:

**In nginx config** (`nginx-sites/vocaframe.com.conf`):
```nginx
# Add this header to tell browsers not to use HTTP/3
add_header Alt-Svc 'clear' always;
```

##### Option 2: Enable HTTP/3 Properly (Recommended for Performance)

**Prerequisites**:
- Nginx 1.25+ with `--with-http_v3_module`
- UDP port 443 open in firewall

**Update nginx config**:
```nginx
server {
    listen 443 ssl http2;
    listen 443 quic reuseport;  # Add QUIC/HTTP3 support

    http2 on;
    http3 on;

    # Advertise HTTP/3 availability
    add_header Alt-Svc 'h3=":443"; ma=86400' always;

    # Rest of config...
}
```

**Open UDP port**:
```bash
# UFW
sudo ufw allow 443/udp

# iptables
sudo iptables -A INPUT -p udp --dport 443 -j ACCEPT
```

##### Option 3: Ignore (Files Still Load)
These errors don't break functionality - files load via HTTP/2 fallback. If users aren't complaining about slow load times, you can safely ignore this.

---

## Testing Payments After Fix

### 1. Rebuild Frontend
```bash
npm run build
docker-compose restart frontend
```

### 2. Test Payment Flow
1. Go to vocaframe.com
2. Upload photo and audio
3. Customize poster
4. Preview poster
5. Click "Download Your Poster"
6. Enter email and postal code
7. Enter test card: `4242 4242 4242 4242`
8. Any future date and any CVC
9. Click "Pay"

### 3. Expected Result
✅ Payment succeeds
✅ PDF generated
✅ Download link provided
✅ Email sent
✅ No 422 errors
✅ No Stripe warnings (wallets)

### 4. Check Logs
```bash
# Backend logs
docker-compose logs -f api | grep -E "payment|order"

# Frontend logs (browser console)
# Should see: "Payment successful" and download URL
```

---

## Stripe Test Cards

| Card | Behavior |
|------|----------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 9995 | Decline (insufficient funds) |
| 4000 0000 0000 9987 | Decline (lost card) |
| 4000 0025 0000 3155 | 3D Secure authentication required |

More test cards: https://stripe.com/docs/testing

---

## Apple Pay / Google Pay Implementation (Future)

To properly add Apple Pay and Google Pay, you need to use the **Payment Request Button API**, not CardElement options:

```typescript
// Create payment request
const paymentRequest = stripe.paymentRequest({
  country: 'US',
  currency: 'usd',
  total: {
    label: 'Audio Poster',
    amount: 299, // Amount in cents
  },
  requestPayerName: true,
  requestPayerEmail: true,
});

// Check if browser supports Apple Pay / Google Pay
const canMakePayment = await paymentRequest.canMakePayment();
if (canMakePayment) {
  // Show Payment Request Button
  const elements = stripe.elements();
  const prButton = elements.create('paymentRequestButton', {
    paymentRequest: paymentRequest,
  });
  prButton.mount('#payment-request-button');
}
```

**Reference**: https://stripe.com/docs/stripe-js/elements/payment-request-button

This is a more complex implementation and can be added later as an enhancement.

---

## Summary

✅ **Fixed**:
- 422 payment error (tier mismatch)
- Stripe wallets warning
- Missing session token

⚠️ **Optional**:
- QUIC errors (files still load, just slower)
- Apple Pay / Google Pay (requires Payment Request Button API)

**Payment flow should now work correctly!** 🎉
