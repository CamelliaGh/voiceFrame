# SendGrid 401 Error - Quick Fix Guide

## The Problem
You're seeing: `SendGrid error: HTTP Error 401: Unauthorized`

## The Solution (3 Steps)

### Step 1: Get Your SendGrid API Key
1. Go to https://app.sendgrid.com/settings/api_keys
2. Click **"Create API Key"**
3. Name it: `VoiceFrame`
4. Select **"Full Access"** or **"Mail Send"** permission
5. Click **"Create & View"**
6. **COPY THE KEY** (starts with `SG.`) - you can only see it once!

### Step 2: Verify Your Sender Email
1. Go to https://app.sendgrid.com/settings/sender_auth
2. Click **"Single Sender Verification"** → **"Create New Sender"**
3. Fill in your email (use a real email you can access)
4. Check your email inbox for verification link
5. Click the verification link

### Step 3: Update Your .env File
Edit `.env` in your project root:

```bash
# Replace these with your actual values
SENDGRID_API_KEY=SG.paste_your_key_here
FROM_EMAIL=your-verified-email@example.com
```

### Step 4: Restart & Test
```bash
# If using Docker
docker-compose down
docker-compose up -d

# Test it (choose one method)

# Method 1: Simple shell script (no dependencies)
./test_sendgrid_simple.sh your-email@example.com

# Method 2: Python script (requires: pip install python-dotenv sendgrid)
python3 test_sendgrid.py your-email@example.com
```

## Expected Result
You should see:
```
✅ API key is set and has correct format
✅ SendGrid package is installed
✅ SUCCESS: Test email sent successfully!
```

And receive a test email in your inbox!

## Still Not Working?

### Check 1: Is your API key valid?
```bash
# Should show your key starting with SG.
cat .env | grep SENDGRID_API_KEY
```

### Check 2: Is your sender verified?
- Go to https://app.sendgrid.com/settings/sender_auth
- Your email should show as "Verified"

### Check 3: Are environment variables loaded?
```bash
# Docker
docker-compose exec api env | grep SENDGRID

# Should show:
# SENDGRID_API_KEY=SG.xxxxx
# FROM_EMAIL=your-email@example.com
```

## Common Mistakes

❌ **Using the placeholder key**
```bash
SENDGRID_API_KEY=sendgrid_api_key  # This won't work!
```

✅ **Using a real key**
```bash
SENDGRID_API_KEY=SG.abc123xyz...  # Correct!
```

❌ **Unverified sender email**
```bash
FROM_EMAIL=noreply@audioposter.com  # Not verified!
```

✅ **Verified sender email**
```bash
FROM_EMAIL=your-name@gmail.com  # Verified in SendGrid!
```

## Need More Help?

Run the diagnostic script:
```bash
python3 test_sendgrid.py your-email@example.com
```

Or read the full guide:
```bash
cat docs/SENDGRID_SETUP.md
```

## Quick Links
- Create API Key: https://app.sendgrid.com/settings/api_keys
- Verify Sender: https://app.sendgrid.com/settings/sender_auth
- Check Activity: https://app.sendgrid.com/email_activity
- SendGrid Status: https://status.sendgrid.com/
