# SendGrid Test Options

You have **3 ways** to test your SendGrid configuration. Choose the one that works best for you:

## Option 1: Simple Shell Script (Recommended - No Dependencies!) ⭐

**Best for**: Quick testing without installing Python packages

```bash
./test_sendgrid_simple.sh your-email@example.com
```

**Advantages**:
- ✅ No Python packages required
- ✅ Works with just curl and bash
- ✅ Loads .env file automatically
- ✅ Clear error messages
- ✅ Fast and simple

**Requirements**:
- curl (already installed on most systems)
- bash shell

---

## Option 2: Python Test Script

**Best for**: Detailed diagnostics and troubleshooting

```bash
# Install dependencies first
pip install python-dotenv sendgrid

# Run test
python3 test_sendgrid.py your-email@example.com
```

**Advantages**:
- ✅ Detailed step-by-step diagnostics
- ✅ Better error categorization
- ✅ More verbose output
- ✅ Works without .env if vars are exported

**Requirements**:
- Python 3
- `python-dotenv` package
- `sendgrid` package

---

## Option 3: API Endpoint (Production Testing)

**Best for**: Testing live server configuration

```bash
# Get admin token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}' | jq -r '.access_token')

# Test SendGrid
curl -X POST http://localhost:8000/api/test/sendgrid \
  -H "Authorization: Bearer $TOKEN" \
  -F "test_email=your-email@example.com"
```

**Advantages**:
- ✅ Tests actual production config
- ✅ JSON response format
- ✅ Admin authentication required
- ✅ Works with running server

**Requirements**:
- Server must be running
- Admin credentials
- curl or similar HTTP client

---

## Quick Comparison

| Feature | Shell Script | Python Script | API Endpoint |
|---------|-------------|--------------|--------------|
| **No dependencies** | ✅ | ❌ | ❌ |
| **Detailed diagnostics** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Server required** | ❌ | ❌ | ✅ |
| **Easy to use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Production testing** | ✅ | ✅ | ✅ |

---

## Installation Issues?

### If `python-dotenv` is missing:
```bash
pip install python-dotenv
```

### If `sendgrid` is missing:
```bash
pip install sendgrid
```

### If you don't want to install anything:
```bash
# Just use the shell script!
./test_sendgrid_simple.sh your-email@example.com
```

---

## Environment Variables

All methods support loading from `.env` file:

```bash
# .env file
SENDGRID_API_KEY=SG.your_key_here
FROM_EMAIL=your-email@example.com
```

Or export directly in shell:

```bash
export SENDGRID_API_KEY=SG.your_key_here
export FROM_EMAIL=your-email@example.com
```

---

## Troubleshooting

### Shell script fails with "command not found"
```bash
chmod +x test_sendgrid_simple.sh
./test_sendgrid_simple.sh your-email@example.com
```

### Python script has import errors
```bash
pip install python-dotenv sendgrid
```

### API endpoint returns 401
```bash
# Get a fresh admin token
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}'
```

---

## Recommended Workflow

1. **First time setup**: Use the **shell script** (easiest, no dependencies)
   ```bash
   ./test_sendgrid_simple.sh your-email@example.com
   ```

2. **Troubleshooting issues**: Use the **Python script** (more details)
   ```bash
   python3 test_sendgrid.py your-email@example.com
   ```

3. **Production verification**: Use the **API endpoint** (tests live config)
   ```bash
   curl -X POST http://localhost:8000/api/test/sendgrid ...
   ```

---

## Example Output (Shell Script)

### Success ✅
```
================================================================================
SendGrid Configuration Test (Simple Version)
================================================================================

✅ Loading .env file...

Step 1: Checking SendGrid API Key...
✅ API key is set and has correct format (SG.abc123xyz...)

Step 2: Checking FROM_EMAIL configuration...
   FROM_EMAIL: your-name@gmail.com

Step 3: Testing SendGrid API with curl...
   Sending test email to: your-email@example.com

✅ SUCCESS: Test email sent successfully!
   HTTP Status Code: 202
   To: your-email@example.com

Check your inbox (and spam folder) for the test email.

================================================================================
🎉 All tests passed! Your SendGrid configuration is working.
================================================================================
```

### Failure ❌
```
Step 3: Testing SendGrid API with curl...
   Sending test email to: your-email@example.com

❌ ERROR: Failed to send test email
   HTTP Status Code: 401

Error Response:
{
  "errors": [
    {
      "message": "The provided authorization grant is invalid, expired, or revoked",
      "field": null,
      "help": null
    }
  ]
}

Solution:
1. Your API key is invalid or has been deleted
2. Go to https://app.sendgrid.com/settings/api_keys
3. Create a new API key with 'Mail Send' permissions
4. Update SENDGRID_API_KEY in your .env file
```

---

**Choose the method that works best for your situation!**
