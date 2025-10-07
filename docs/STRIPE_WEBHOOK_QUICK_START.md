# Stripe Webhook Quick Start

## 🚀 5-Minute Setup

### For Local Development (Easiest)

1. **Install Stripe CLI**
   ```bash
   brew install stripe/stripe-cli/stripe
   ```

2. **Login**
   ```bash
   stripe login
   ```

3. **Forward webhooks** (in one terminal)
   ```bash
   stripe listen --forward-to localhost:8000/api/stripe/webhook
   ```
   Copy the webhook secret from the output (starts with `whsec_`)

4. **Add to .env**
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
   ```

5. **Restart backend**
   ```bash
   docker-compose restart api
   ```

6. **Test it** (in another terminal)
   ```bash
   stripe trigger payment_intent.succeeded
   ```

7. **Check logs**
   ```bash
   docker-compose logs -f api | grep "Stripe webhook"
   ```

✅ You should see: `Stripe webhook received: payment_intent.succeeded`

---

### For Production

1. **Go to**: https://dashboard.stripe.com/webhooks
2. **Click**: "Add endpoint"
3. **Enter**: `https://vocaframe.com/api/stripe/webhook`
4. **Select events**:
   - `payment_intent.succeeded` ✅
   - `payment_intent.payment_failed` ❌
   - `payment_intent.canceled` 🚫
   - `charge.refunded` 💰
5. **Copy webhook secret**: Click "Reveal" and copy `whsec_...`
6. **Add to production .env**: `STRIPE_WEBHOOK_SECRET=whsec_...`
7. **Restart server**

---

## What It Does

| Event | What Happens |
|-------|-------------|
| Payment succeeds | Order → `completed`, email sent |
| Payment fails | Order → `failed` |
| Payment canceled | Order → `canceled` |
| Payment refunded | Order → `refunded` |

---

## Test Commands

```bash
# Test different scenarios
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
stripe trigger charge.refunded
stripe trigger payment_intent.canceled
```

---

## Verify It's Working

✅ **Check logs**: See "Stripe webhook received" messages
✅ **Check database**: Order status updates correctly
✅ **Check Stripe Dashboard**: Webhooks → Recent deliveries → 200 OK

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Webhook secret not configured" | Add `STRIPE_WEBHOOK_SECRET` to .env |
| "Missing stripe-signature header" | URL wrong in Stripe Dashboard |
| Not receiving webhooks | Restart `stripe listen` command |
| 500 errors | Check backend logs for details |

---

## Webhook URL

✨ **Your webhook is now live at:**
```
http://localhost:8000/api/stripe/webhook       (local)
https://vocaframe.com/api/stripe/webhook       (production)
```

---

See [STRIPE_WEBHOOK_SETUP.md](./STRIPE_WEBHOOK_SETUP.md) for detailed documentation.
