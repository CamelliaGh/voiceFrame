#!/bin/bash

# Resend Configuration Test Script
# Usage: ./test_resend.sh your-email@example.com

set -e

echo "================================================================================"
echo "Resend Configuration Test"
echo "================================================================================"
echo ""

# Check if email argument is provided
if [ -z "$1" ]; then
    echo "❌ ERROR: No email address provided"
    echo ""
    echo "Usage: ./test_resend.sh your-email@example.com"
    exit 1
fi

TEST_EMAIL="$1"

# Load .env file if it exists
if [ -f .env ]; then
    echo "✅ Loading .env file..."
    # Properly parse .env file, ignoring comments and handling values with spaces
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        # Remove inline comments
        line="${line%%#*}"
        # Trim whitespace
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        # Export the variable
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            export "$line"
        fi
    done < .env
    echo ""
else
    echo "⚠️  WARNING: .env file not found"
    echo "   Using environment variables from shell"
    echo ""
fi

# Step 1: Check Resend API Key
echo "Step 1: Checking Resend API Key..."
if [ -z "$RESEND_API_KEY" ]; then
    echo "❌ ERROR: RESEND_API_KEY not found in environment"
    echo ""
    echo "Solution:"
    echo "1. Create a .env file in the project root"
    echo "2. Add: RESEND_API_KEY=re_your_actual_key_here"
    echo "3. Get your key from: https://resend.com/api-keys"
    exit 1
fi

if [ "$RESEND_API_KEY" = "resend_api_key" ] || [ "$RESEND_API_KEY" = "re_your_resend_api_key_here" ]; then
    echo "❌ ERROR: RESEND_API_KEY is still the placeholder value"
    echo ""
    echo "Solution:"
    echo "1. Go to https://resend.com/api-keys"
    echo "2. Create a new API key with 'Sending access' permissions"
    echo "3. Replace the placeholder in .env with the real key"
    exit 1
fi

if [[ $RESEND_API_KEY == re_* ]]; then
    echo "✅ API key is set and has correct format (${RESEND_API_KEY:0:10}...)"
else
    echo "⚠️  WARNING: API key doesn't start with 're_' - may be invalid"
    echo "   Current value: ${RESEND_API_KEY:0:10}..."
fi

echo ""

# Step 2: Check FROM_EMAIL
echo "Step 2: Checking FROM_EMAIL configuration..."
FROM_EMAIL="${FROM_EMAIL:-noreply@audioposter.com}"
echo "   FROM_EMAIL: $FROM_EMAIL"

if [ "$FROM_EMAIL" = "noreply@audioposter.com" ]; then
    echo "⚠️  WARNING: Using default FROM_EMAIL - verify this domain in Resend"
fi

echo ""

# Step 3: Test with curl
echo "Step 3: Testing Resend API with curl..."
echo "   Sending test email to: $TEST_EMAIL"
echo ""

# Create JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
  "from": "$FROM_EMAIL",
  "to": ["$TEST_EMAIL"],
  "subject": "✅ VoiceFrame - Resend Test Successful!",
  "html": "<html><body style='font-family: Arial, sans-serif; padding: 20px;'><h2 style='color: #8b5cf6;'>✅ Resend Test Successful!</h2><p>Congratulations! Your Resend configuration is working correctly.</p><p>This test email was sent from your VoiceFrame application.</p><hr style='margin: 20px 0;'><p style='color: #666; font-size: 14px;'><strong>Configuration Details:</strong><br>From Email: $FROM_EMAIL<br>To Email: $TEST_EMAIL<br>Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')</p></body></html>",
  "text": "✅ Resend Test Successful!\n\nCongratulations! Your Resend configuration is working correctly.\nThis test email was sent from your VoiceFrame application.\n\nConfiguration Details:\nFrom Email: $FROM_EMAIL\nTo Email: $TEST_EMAIL\nTimestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
}
EOF
)

# Send request to Resend API
HTTP_CODE=$(curl -s -o /tmp/resend_response.txt -w "%{http_code}" \
    -X POST "https://api.resend.com/emails" \
    -H "Authorization: Bearer $RESEND_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD")

# Check response
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS: Test email sent successfully!"
    echo "   HTTP Status Code: $HTTP_CODE"
    echo "   To: $TEST_EMAIL"

    # Show email ID if available
    if [ -f /tmp/resend_response.txt ]; then
        EMAIL_ID=$(cat /tmp/resend_response.txt | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'N/A'))" 2>/dev/null || echo "N/A")
        if [ "$EMAIL_ID" != "N/A" ]; then
            echo "   Email ID: $EMAIL_ID"
        fi
    fi

    echo ""
    echo "Check your inbox (and spam folder) for the test email."
    echo ""
    echo "If you don't receive the email within a few minutes:"
    echo "1. Check Resend dashboard for delivery logs: https://resend.com/emails"
    echo "2. Verify the sender domain is verified in Resend"
    echo "3. Check if the recipient email is valid"
    echo "4. Look for the email in spam/junk folder"
    echo ""
    echo "================================================================================"
    echo "🎉 All tests passed! Your Resend configuration is working."
    echo "================================================================================"
    exit 0
else
    echo "❌ ERROR: Failed to send test email"
    echo "   HTTP Status Code: $HTTP_CODE"
    echo ""

    # Display error response
    if [ -f /tmp/resend_response.txt ]; then
        echo "Error Response:"
        cat /tmp/resend_response.txt | python3 -m json.tool 2>/dev/null || cat /tmp/resend_response.txt
        echo ""
    fi

    # Check for specific error messages
    ERROR_MSG=$(cat /tmp/resend_response.txt 2>/dev/null)

    if echo "$ERROR_MSG" | grep -qi "invalid.*api.*key\|unauthorized"; then
        echo "Solution:"
        echo "1. Your API key is invalid or has been deleted"
        echo "2. Go to https://resend.com/api-keys"
        echo "3. Create a new API key with 'Sending access' permissions"
        echo "4. Update RESEND_API_KEY in your .env file"
    elif echo "$ERROR_MSG" | grep -qi "domain.*not.*verified\|domain.*not.*found"; then
        echo "Solution:"
        echo "1. The sender domain '$FROM_EMAIL' is not verified in Resend"
        echo "2. Go to https://resend.com/domains"
        echo "3. Add and verify your domain"
        echo "4. Or use 'onboarding@resend.dev' for testing"
        echo "5. Update FROM_EMAIL in .env"
    elif echo "$ERROR_MSG" | grep -qi "rate.*limit\|too.*many.*requests"; then
        echo "Solution:"
        echo "1. You've exceeded Resend's rate limits"
        echo "2. Free tier: 100 emails/day, 3,000 emails/month"
        echo "3. Check your usage: https://resend.com/overview"
        echo "4. Wait for the limit to reset"
        echo "5. Or upgrade your plan: https://resend.com/pricing"
    else
        echo "Solution:"
        echo "1. Check the error response above for details"
        echo "2. Visit Resend dashboard: https://resend.com"
        echo "3. Check email logs for more information"
        echo "4. Verify your domain is set up correctly"
    fi

    echo ""
    echo "================================================================================"
    echo "❌ Resend configuration test failed."
    echo "================================================================================"
    exit 1
fi
