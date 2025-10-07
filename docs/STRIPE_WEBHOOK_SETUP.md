# Stripe Webhook Setup Guide

This guide walks you through setting up Stripe webhooks for VoiceFrame to handle payment events automatically.

## Why Webhooks?

Webhooks provide a reliable backup to client-side payment verification. They notify your server about:
- ✅ Successful payments
- ❌ Failed payments
- 💰 Refunds
- 🚫 Canceled payments
- 🔄 Payment disputes

## Webhook URL

Your webhook endpoint is now live at:

```
Production: https://vocaframe.com/api/stripe/webhook
Development: http://localhost:8000/api/stripe/webhook (use ngrok/stripe CLI)
```

**Note**: Use `vocaframe.com` (without www) - the www subdomain redirects to the apex domain.

---

## Setup Instructions

### Option 1: Stripe Dashboard (Production)

1. **Go to Stripe Dashboard**
   - Navigate to: https://dashboard.stripe.com/webhooks
   - Click "Add endpoint"

2. **Configure Endpoint**
   - **Endpoint URL**: `https://vocaframe.com/api/stripe/webhook`
   - **Description**: "VoiceFrame Payment Events"
   - **Events to send**: Select these events:
     - ✅ `payment_intent.succeeded`
     - ❌ `payment_intent.payment_failed`
     - 🚫 `payment_intent.canceled`
     - 💰 `charge.refunded`
     - ℹ️ `payment_intent.created` (optional - informational)
     - ℹ️ `payment_intent.processing` (optional - informational)

3. **Get Webhook Secret**
   - After creating the endpoint, click on it
   - Click "Reveal" under "Signing secret"
   - Copy the secret (starts with `whsec_...`)

4. **Add to Environment Variables**
   ```bash
   # In your .env file
   STRIPE_WEBHOOK_SECRET=whsec_your_secret_here_from_stripe_dashboard
   ```

5. **Restart Your Server**
   ```bash
   docker-compose restart api
   # or
   uvicorn backend.main:app --reload
   ```

---

### Option 2: Local Testing with Stripe CLI (Development)

For local development, use the Stripe CLI to forward webhooks:

1. **Install Stripe CLI**
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe

   # Other platforms: https://stripe.com/docs/stripe-cli
   ```

2. **Login to Stripe**
   ```bash
   stripe login
   ```

3. **Forward Webhooks to Localhost**
   ```bash
   stripe listen --forward-to localhost:8000/api/stripe/webhook
   ```

   This will output a webhook secret like: `whsec_...`

4. **Add Secret to .env**
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_from_stripe_cli_output
   ```

5. **Test a Payment**
   ```bash
   # In another terminal, trigger a test payment
   stripe trigger payment_intent.succeeded
   ```

---

### Option 3: Ngrok (Alternative for Local Testing)

If you don't want to use Stripe CLI:

1. **Start Ngrok**
   ```bash
   ngrok http 8000
   ```

2. **Copy the HTTPS URL**
   ```
   Example: https://abc123.ngrok.io
   ```

3. **Add Webhook in Stripe Dashboard**
   - URL: `https://abc123.ngrok.io/api/stripe/webhook`
   - Select events (same as Option 1)
   - Copy the webhook secret

4. **Add to .env and restart server**

---

## Webhook Event Handling

The webhook endpoint handles these events:

### ✅ `payment_intent.succeeded`
- **Action**: Marks order as `completed`
- **Side Effect**: Sends download email to customer (if not already sent)
- **Idempotent**: Safe to receive multiple times

### ❌ `payment_intent.payment_failed`
- **Action**: Marks order as `failed`
- **Logs**: Payment failure message for debugging

### 💰 `charge.refunded`
- **Action**: Marks order as `refunded`
- **Use Case**: Customer service refunds

### 🚫 `payment_intent.canceled`
- **Action**: Marks order as `canceled` (only if currently `pending`)
- **Use Case**: Customer abandons payment

### ℹ️ Informational Events
These are logged but don't change order status:
- `payment_intent.created`
- `payment_intent.processing`
- `charge.succeeded`
- `payment_method.attached`

---

## Verifying Webhook Setup

### 1. Check Logs
Monitor your application logs for webhook events:
```bash
# Docker
docker-compose logs -f api | grep "Stripe webhook"

# Local
# Check terminal output for log messages like:
# "Stripe webhook received: payment_intent.succeeded - ID: evt_..."
```

### 2. Test with Stripe Dashboard
1. Go to: https://dashboard.stripe.com/test/payments
2. Create a test payment
3. Check your logs for webhook receipt
4. Verify order status updated in database

### 3. Test with Stripe CLI
```bash
# Trigger specific events
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
stripe trigger charge.refunded
```

### 4. Check Webhook Delivery in Stripe
- Go to: https://dashboard.stripe.com/webhooks
- Click on your endpoint
- View "Recent deliveries" tab
- Check for successful 200 responses

---

## Security Features

✅ **Signature Verification**: Every webhook is verified using Stripe's signature
✅ **Idempotency**: Multiple deliveries of the same event are safe
✅ **Error Handling**: Returns 200 even on errors (prevents retry storms)
✅ **Logging**: All events and errors are logged for debugging
✅ **Database Transactions**: Order updates are atomic

---

## Troubleshooting

### Webhook Returns 400 "Missing stripe-signature header"
- **Cause**: Request not from Stripe or misconfigured
- **Fix**: Verify the URL is correct in Stripe Dashboard

### Webhook Returns 500 "Webhook secret not configured"
- **Cause**: `STRIPE_WEBHOOK_SECRET` not set in environment
- **Fix**: Add secret to `.env` and restart server

### Order Status Not Updating
- **Check**: Webhook is being received (check logs)
- **Check**: `stripe_payment_intent_id` matches in database
- **Check**: Order isn't already in final state (`completed`, `refunded`)

### Duplicate Emails Sent
- **Normal**: Webhook provides backup - email may send twice (once from `/complete`, once from webhook)
- **Solution**: Add email tracking to prevent duplicates (future enhancement)

### Stripe CLI "Connection refused"
- **Cause**: Backend server not running on localhost:8000
- **Fix**: Start your backend first, then run `stripe listen`

---

## Order Status Flow

```
pending → completed  (payment succeeds)
        → failed     (payment fails)
        → canceled   (payment canceled before completion)
        → refunded   (completed, then refunded by admin)
```

---

## Production Checklist

Before going live:

- [ ] Webhook endpoint added in Stripe Dashboard (production keys)
- [ ] `STRIPE_WEBHOOK_SECRET` set in production environment
- [ ] HTTPS enabled (webhooks require HTTPS in production)
- [ ] Webhook endpoint accessible (not behind firewall)
- [ ] Logs configured for webhook monitoring
- [ ] Tested with real payment in test mode
- [ ] Backup email notifications working
- [ ] Database backups enabled

---

## Additional Resources

- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Testing Webhooks](https://stripe.com/docs/webhooks/test)
- [Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)

---

## Need Help?

If webhooks aren't working:
1. Check server logs for errors
2. Verify webhook secret is correct
3. Test with `stripe trigger` command
4. Check Stripe Dashboard webhook delivery logs
5. Ensure server is accessible (not localhost in production)
