# Resend Email Service Setup Guide

VoiceFrame has migrated from SendGrid to **Resend** for email delivery. This guide will help you set up and configure Resend.

## Why Resend?

✅ **Better Free Tier**: 3,000 emails/month (vs SendGrid's 100/day)
✅ **Simpler API**: Modern, developer-friendly interface
✅ **Better Deliverability**: High inbox placement rates
✅ **No Credit Card Required**: Free tier doesn't require payment info
✅ **React Email Support**: Built-in support for React email templates

---

## Quick Setup (5 Minutes)

### 1. Create Resend Account

1. Go to [resend.com](https://resend.com)
2. Click **"Sign Up"** (free, no credit card required)
3. Verify your email address

### 2. Get API Key

1. Go to [API Keys](https://resend.com/api-keys)
2. Click **"Create API Key"**
3. Name it: `VoiceFrame Production`
4. Select permissions: **"Sending access"**
5. Click **"Add"**
6. **Copy the API key** (starts with `re_`) - you can only see it once!

### 3. Verify Your Domain

**Option A: Quick Test (Use Resend's Test Domain)**
- Resend provides `onboarding@resend.dev` for testing
- Skip to step 4 and use `onboarding@resend.dev` as FROM_EMAIL
- **Note**: Test domain has limits, verify your own domain for production

**Option B: Verify Your Own Domain (Recommended for Production)**

1. Go to [Domains](https://resend.com/domains)
2. Click **"Add Domain"**
3. Enter your domain (e.g., `vocaframe.com`)
4. Add the DNS records shown to your domain provider:
   - **SPF Record** (TXT)
   - **DKIM Record** (TXT)
   - **DMARC Record** (TXT)
5. Click **"Verify DNS Records"**
6. Wait for verification (usually 5-15 minutes)

### 4. Update Environment Variables

Edit your `.env` file:

```bash
# Email Service Configuration (Resend)
RESEND_API_KEY=re_your_actual_api_key_here
FROM_EMAIL=noreply@vocaframe.com  # Or onboarding@resend.dev for testing
```

**Important**:
- Replace `re_your_actual_api_key_here` with your real API key
- Use your verified domain email or `onboarding@resend.dev`

### 5. Install Dependencies & Restart

```bash
# Install Resend package
pip install resend==0.8.0

# Or install all requirements
pip install -r requirements.txt

# Restart services
docker-compose down
docker-compose up -d
```

---

## Testing Your Setup

### Method 1: Test Script (Coming Soon)
```bash
./test_resend.sh your-email@example.com
```

### Method 2: API Endpoint
```bash
# Get admin token
TOKEN=$(curl -s -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}' | jq -r '.access_token')

# Test Resend
curl -X POST http://localhost:8000/api/test/resend \
  -H "Authorization: Bearer $TOKEN" \
  -F "test_email=your-email@example.com"
```

### Method 3: Check Logs
```bash
docker-compose logs -f api | grep -i resend
```

---

## Resend Free Tier Limits

| Feature | Free Tier | Pro Plan |
|---------|-----------|----------|
| **Emails/Month** | 3,000 | 50,000+ |
| **Emails/Day** | 100 | Unlimited |
| **Domains** | 1 | Unlimited |
| **Team Members** | 1 | Unlimited |
| **API Keys** | Unlimited | Unlimited |
| **Email Logs** | 30 days | 90 days |
| **Support** | Community | Priority |

**Cost**: Free tier is completely free, Pro starts at $20/month

---

## DNS Configuration

When verifying your domain, you'll need to add these DNS records:

### SPF Record
```
Type: TXT
Name: @
Value: v=spf1 include:_spf.resend.com ~all
```

### DKIM Record
```
Type: TXT
Name: resend._domainkey
Value: (provided by Resend dashboard)
```

### DMARC Record
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
```

**DNS Propagation**: Usually takes 5-15 minutes, can take up to 48 hours

---

## Common Issues & Solutions

### Issue 1: "Invalid API key"

**Cause**: API key is incorrect or not set

**Solutions**:
1. Check your API key in `.env` starts with `re_`
2. Verify you copied the entire key from Resend dashboard
3. Create a new API key if needed
4. Restart your services after updating `.env`

### Issue 2: "Domain not verified"

**Cause**: DNS records not set up or not propagated

**Solutions**:
1. Go to [Resend Domains](https://resend.com/domains)
2. Click on your domain
3. Verify all DNS records are added correctly
4. Wait for DNS propagation (5-15 minutes)
5. Click "Verify DNS Records" button
6. Or use `onboarding@resend.dev` for testing

### Issue 3: "Rate limit exceeded"

**Cause**: Exceeded free tier limits (100 emails/day or 3,000/month)

**Solutions**:
1. Check your usage in [Resend Dashboard](https://resend.com/overview)
2. Wait for daily/monthly reset
3. Upgrade to Pro plan if needed
4. Implement email queuing/throttling

### Issue 4: Emails going to spam

**Causes**: Domain not verified, missing DNS records, poor sender reputation

**Solutions**:
1. Verify your domain completely (SPF, DKIM, DMARC)
2. Use a professional FROM_EMAIL (not gmail, yahoo, etc.)
3. Warm up your domain (start with low volume)
4. Add unsubscribe links to all emails
5. Monitor bounce rates in Resend dashboard

---

## Migration from SendGrid

If you're migrating from SendGrid:

### What Changed

| SendGrid | Resend |
|----------|--------|
| `SENDGRID_API_KEY` | `RESEND_API_KEY` |
| Starts with `SG.` | Starts with `re_` |
| Single Sender Verification | Domain Verification |
| 100 emails/day free | 3,000 emails/month free |
| Complex API | Simple API |

### Migration Steps

1. ✅ Get Resend API key
2. ✅ Verify domain in Resend
3. ✅ Update `.env` file
4. ✅ Install `resend` package
5. ✅ Remove `sendgrid` package
6. ✅ Restart services
7. ✅ Test email sending
8. ✅ Monitor for issues

### Code Changes (Already Done)

- ✅ Updated `email_service.py` to use Resend
- ✅ Updated `config.py` for Resend API key
- ✅ Updated `requirements.txt`
- ✅ Updated test endpoint
- ✅ Updated environment variable names

---

## Resend Dashboard Features

### Overview
- Email statistics
- Delivery rates
- Bounce rates
- Recent activity

### Emails
- View all sent emails
- Search by recipient, subject, status
- View email content
- Check delivery status

### API Keys
- Create/manage API keys
- Set permissions
- Revoke keys

### Domains
- Add/verify domains
- Check DNS records
- View domain health

### Logs
- Detailed email logs
- Webhook events
- API requests
- Error tracking

---

## Best Practices

### Development
- Use `onboarding@resend.dev` for testing
- Test with your own email first
- Monitor Resend dashboard for errors
- Keep API key in `.env`, never commit

### Production
- Verify your own domain
- Use professional FROM_EMAIL
- Implement email queuing
- Monitor delivery rates
- Set up error alerts
- Keep logs for debugging

### Security
- Never commit API keys to git
- Rotate API keys regularly (every 3-6 months)
- Use environment variables
- Limit API key permissions
- Monitor for suspicious activity

### Deliverability
- Verify domain completely (SPF, DKIM, DMARC)
- Warm up new domains gradually
- Include unsubscribe links
- Monitor bounce rates
- Keep email list clean
- Use double opt-in for subscribers

---

## Monitoring & Analytics

### Check Email Status
```bash
# View recent emails in Resend dashboard
https://resend.com/emails

# Check application logs
docker-compose logs -f api | grep -i "email"
```

### Key Metrics to Monitor
- **Delivery Rate**: Should be >95%
- **Bounce Rate**: Should be <5%
- **Spam Rate**: Should be <0.1%
- **Open Rate**: Varies by industry (15-25% typical)

---

## Troubleshooting Commands

```bash
# Check environment variables
cat .env | grep RESEND

# Check if Resend package is installed
pip list | grep resend

# Test API key
curl https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"onboarding@resend.dev","to":"test@example.com","subject":"Test","html":"<p>Test</p>"}'

# View logs
docker-compose logs -f api | grep -i resend

# Restart services
docker-compose down && docker-compose up -d
```

---

## Getting Help

- **Resend Docs**: https://resend.com/docs
- **Resend Support**: support@resend.com
- **Resend Discord**: https://resend.com/discord
- **Status Page**: https://status.resend.com

---

## Comparison: Resend vs SendGrid

| Feature | Resend | SendGrid |
|---------|--------|----------|
| **Free Tier** | 3,000/month | 100/day |
| **Setup Time** | 5 minutes | 15 minutes |
| **API Complexity** | Simple | Complex |
| **Dashboard** | Modern | Legacy |
| **Deliverability** | Excellent | Good |
| **Support** | Community/Email | Tiered |
| **React Email** | Built-in | No |
| **Pricing** | $20/month | $19.95/month |

---

## Next Steps

1. **Create Resend account** at [resend.com](https://resend.com)
2. **Get API key** from dashboard
3. **Verify domain** or use test domain
4. **Update `.env` file** with credentials
5. **Restart services** and test
6. **Monitor dashboard** for delivery stats

---

**Need help?** Check the [Resend documentation](https://resend.com/docs) or contact support.
