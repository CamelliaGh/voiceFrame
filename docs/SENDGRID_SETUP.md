# SendGrid Setup & Troubleshooting Guide

This guide will help you set up and troubleshoot SendGrid email functionality in VoiceFrame.

## Quick Start

### 1. Get SendGrid API Key

1. Sign up or log in at [SendGrid](https://sendgrid.com/)
2. Navigate to **Settings** → **API Keys**
3. Click **Create API Key**
4. Name it (e.g., "VoiceFrame Production")
5. Select **Full Access** or at minimum **Mail Send** permission
6. Copy the API key (starts with `SG.`)
   - ⚠️ **Important**: You can only see this key once! Save it immediately.

### 2. Verify Sender Email

SendGrid requires you to verify the email address you'll send from:

**Option A: Single Sender Verification (Quick)**
1. Go to **Settings** → **Sender Authentication** → **Single Sender Verification**
2. Click **Create New Sender**
3. Fill in your details (use a real email you have access to)
4. Check your email for verification link
5. Click the verification link

**Option B: Domain Authentication (Recommended for Production)**
1. Go to **Settings** → **Sender Authentication** → **Domain Authentication**
2. Follow the wizard to add DNS records to your domain
3. This allows you to send from any email @yourdomain.com

### 3. Configure Environment Variables

Update your `.env` file in the project root:

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.your_actual_api_key_here
FROM_EMAIL=your-verified-email@yourdomain.com
```

**Important**:
- Replace `SG.your_actual_api_key_here` with your real API key
- Replace `your-verified-email@yourdomain.com` with the email you verified in step 2

### 4. Restart Services

If using Docker:
```bash
docker-compose down
docker-compose up -d
```

If running locally:
```bash
# Just restart your FastAPI server
```

## Testing Your Configuration

### Method 1: Using the Test Script (Recommended)

Run the provided test script:

```bash
python3 test_sendgrid.py your-email@example.com
```

This will:
- ✅ Check if API key is set
- ✅ Verify API key format
- ✅ Check FROM_EMAIL configuration
- ✅ Test SendGrid package installation
- ✅ Send a real test email
- ✅ Provide specific error solutions

### Method 2: Using the API Endpoint

If your server is running, you can test via the API:

```bash
# Get admin token first (if needed)
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}'

# Test SendGrid (replace TOKEN and EMAIL)
curl -X POST http://localhost:8000/api/test/sendgrid \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "test_email=your-email@example.com"
```

### Method 3: Check Logs

Monitor your application logs for SendGrid-related messages:

```bash
# Docker
docker-compose logs -f api | grep -i sendgrid

# Local
# Check your terminal where the server is running
```

## Common Issues & Solutions

### Issue 1: "HTTP Error 401: Unauthorized"

**Cause**: Invalid or expired API key

**Solutions**:
1. Verify your API key in `.env` starts with `SG.`
2. Check if the key was deleted in SendGrid dashboard
3. Create a new API key:
   - Go to https://app.sendgrid.com/settings/api_keys
   - Create new key with "Mail Send" permissions
   - Update `.env` with new key
4. Restart your services

### Issue 2: "HTTP Error 403: Forbidden"

**Cause**: API key doesn't have required permissions

**Solutions**:
1. Go to https://app.sendgrid.com/settings/api_keys
2. Find your API key
3. Edit permissions to include "Mail Send"
4. Or create a new key with "Full Access"
5. Update `.env` and restart services

### Issue 3: Sender Email Not Verified

**Error**: "The from address does not match a verified Sender Identity"

**Solutions**:
1. Go to https://app.sendgrid.com/settings/sender_auth
2. Verify your sender email via:
   - **Single Sender Verification** (quick, for testing)
   - **Domain Authentication** (recommended for production)
3. Update `FROM_EMAIL` in `.env` to match verified email
4. Restart services

### Issue 4: API Key Not Set

**Error**: "Warning: SendGrid API key not configured - emails will be logged only"

**Solutions**:
1. Check if `.env` file exists in project root
2. Add or update: `SENDGRID_API_KEY=SG.your_key_here`
3. Ensure `.env` is not in `.gitignore` (it should be!)
4. For Docker, ensure environment variables are passed in `docker-compose.yml`
5. Restart services

### Issue 5: Emails Not Received

**Possible Causes**:
- Email in spam folder
- Sender reputation issues
- Invalid recipient email
- SendGrid account suspended

**Solutions**:
1. Check recipient's spam/junk folder
2. Check SendGrid Activity Feed:
   - Go to https://app.sendgrid.com/email_activity
   - Search for your email
   - Check delivery status
3. Verify recipient email is valid
4. Check SendGrid account status
5. Review SendGrid's sender reputation

### Issue 6: Docker Environment Variables Not Loading

**Symptoms**: API key works locally but not in Docker

**Solutions**:

1. Check `docker-compose.yml` includes SendGrid variables:
```yaml
services:
  api:
    environment:
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
      - FROM_EMAIL=${FROM_EMAIL}
```

2. Verify `.env` file is in the same directory as `docker-compose.yml`

3. Rebuild and restart containers:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

4. Verify environment variables are loaded:
```bash
docker-compose exec api env | grep SENDGRID
```

## Verification Checklist

Before going to production, verify:

- [ ] SendGrid API key is created and has "Mail Send" permissions
- [ ] API key starts with `SG.` and is not the placeholder value
- [ ] Sender email is verified in SendGrid dashboard
- [ ] `SENDGRID_API_KEY` is set in `.env` file
- [ ] `FROM_EMAIL` matches a verified sender
- [ ] Test script runs successfully
- [ ] Test email is received (check spam folder)
- [ ] Docker containers have access to environment variables
- [ ] Application logs show no SendGrid errors
- [ ] SendGrid Activity Feed shows successful deliveries

## Development vs Production

### Development
- Use Single Sender Verification
- Can use personal email (e.g., your-name@gmail.com)
- Test with your own email addresses
- Monitor SendGrid Activity Feed closely

### Production
- Use Domain Authentication
- Use professional domain (e.g., noreply@yourdomain.com)
- Set up proper DNS records
- Monitor delivery rates and sender reputation
- Consider SendGrid's Email Validation API
- Set up webhook for delivery notifications

## Monitoring SendGrid

### SendGrid Dashboard
- **Activity Feed**: https://app.sendgrid.com/email_activity
  - View all sent emails
  - Check delivery status
  - See bounce/spam reports

- **Statistics**: https://app.sendgrid.com/statistics
  - Delivery rates
  - Open rates
  - Click rates
  - Bounce rates

### Application Logs
Monitor your application logs for SendGrid-related events:

```bash
# Docker
docker-compose logs -f api | grep -i "email\|sendgrid"

# Local
# Check terminal output for email-related logs
```

## Rate Limits

SendGrid free tier limits:
- **100 emails/day** (Free Forever plan)
- **40,000 emails/month** for first 30 days

If you need more:
- Upgrade to a paid plan
- Consider implementing email queuing
- Monitor usage in SendGrid dashboard

## Security Best Practices

1. **Never commit API keys to git**
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Rotate API keys regularly**
   - Create new keys every 3-6 months
   - Delete old keys after rotation

3. **Use minimal permissions**
   - Only grant "Mail Send" permission
   - Avoid "Full Access" unless necessary

4. **Monitor for suspicious activity**
   - Check SendGrid Activity Feed regularly
   - Set up alerts for unusual sending patterns

5. **Verify sender domain**
   - Use Domain Authentication in production
   - Improves deliverability and security

## Getting Help

If you're still having issues:

1. **Check SendGrid Status**: https://status.sendgrid.com/
2. **SendGrid Support**: https://support.sendgrid.com/
3. **SendGrid Docs**: https://docs.sendgrid.com/
4. **Run the test script**: `python3 test_sendgrid.py your-email@example.com`
5. **Check application logs** for detailed error messages
6. **Review SendGrid Activity Feed** for delivery issues

## Additional Resources

- [SendGrid API Documentation](https://docs.sendgrid.com/api-reference/mail-send/mail-send)
- [SendGrid Python Library](https://github.com/sendgrid/sendgrid-python)
- [Email Best Practices](https://docs.sendgrid.com/ui/sending-email/email-best-practices)
- [Sender Authentication Guide](https://docs.sendgrid.com/ui/account-and-settings/how-to-set-up-domain-authentication)
