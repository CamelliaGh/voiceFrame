#!/bin/bash

# Simple SendGrid Test Script (No Python dependencies required)
# Usage: ./test_sendgrid_simple.sh your-email@example.com

set -e

echo "================================================================================"
echo "SendGrid Configuration Test (Simple Version)"
echo "================================================================================"
echo ""

# Check if email argument is provided
if [ -z "$1" ]; then
    echo "❌ ERROR: No email address provided"
    echo ""
    echo "Usage: ./test_sendgrid_simple.sh your-email@example.com"
    exit 1
fi

TEST_EMAIL="$1"

# Load .env file if it exists
if [ -f .env ]; then
    echo "✅ Loading .env file..."
    export $(cat .env | grep -v '^#' | xargs)
    echo ""
else
    echo "⚠️  WARNING: .env file not found"
    echo "   Using environment variables from shell"
    echo ""
fi

# Step 1: Check SendGrid API Key
echo "Step 1: Checking SendGrid API Key..."
if [ -z "$SENDGRID_API_KEY" ]; then
    echo "❌ ERROR: SENDGRID_API_KEY not found in environment"
    echo ""
    echo "Solution:"
    echo "1. Create a .env file in the project root"
    echo "2. Add: SENDGRID_API_KEY=SG.your_actual_key_here"
    echo "3. Get your key from: https://app.sendgrid.com/settings/api_keys"
    exit 1
fi

if [ "$SENDGRID_API_KEY" = "sendgrid_api_key" ]; then
    echo "❌ ERROR: SENDGRID_API_KEY is still the placeholder value"
    echo ""
    echo "Solution:"
    echo "1. Go to https://app.sendgrid.com/settings/api_keys"
    echo "2. Create a new API key with 'Mail Send' permissions"
    echo "3. Replace 'sendgrid_api_key' in .env with the real key"
    exit 1
fi

if [[ $SENDGRID_API_KEY == SG.* ]]; then
    echo "✅ API key is set and has correct format (${SENDGRID_API_KEY:0:13}...)"
else
    echo "⚠️  WARNING: API key doesn't start with 'SG.' - may be invalid"
    echo "   Current value: ${SENDGRID_API_KEY:0:10}..."
fi

echo ""

# Step 2: Check FROM_EMAIL
echo "Step 2: Checking FROM_EMAIL configuration..."
FROM_EMAIL="${FROM_EMAIL:-noreply@audioposter.com}"
echo "   FROM_EMAIL: $FROM_EMAIL"

if [ "$FROM_EMAIL" = "noreply@audioposter.com" ]; then
    echo "⚠️  WARNING: Using default FROM_EMAIL - verify this in SendGrid"
fi

echo ""

# Step 3: Test with curl
echo "Step 3: Testing SendGrid API with curl..."
echo "   Sending test email to: $TEST_EMAIL"
echo ""

# Create JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
  "personalizations": [
    {
      "to": [
        {
          "email": "$TEST_EMAIL"
        }
      ],
      "subject": "✅ VoiceFrame - SendGrid Test Successful!"
    }
  ],
  "from": {
    "email": "$FROM_EMAIL",
    "name": "VoiceFrame Test"
  },
  "content": [
    {
      "type": "text/plain",
      "value": "✅ SendGrid Test Successful!\n\nCongratulations! Your SendGrid configuration is working correctly.\nThis test email was sent from your VoiceFrame application.\n\nConfiguration Details:\nFrom Email: $FROM_EMAIL\nTo Email: $TEST_EMAIL\nTimestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    },
    {
      "type": "text/html",
      "value": "<html><body style='font-family: Arial, sans-serif; padding: 20px;'><h2 style='color: #8b5cf6;'>✅ SendGrid Test Successful!</h2><p>Congratulations! Your SendGrid configuration is working correctly.</p><p>This test email was sent from your VoiceFrame application.</p><hr style='margin: 20px 0;'><p style='color: #666; font-size: 14px;'><strong>Configuration Details:</strong><br>From Email: $FROM_EMAIL<br>To Email: $TEST_EMAIL<br>Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')</p></body></html>"
    }
  ]
}
EOF
)

# Send request to SendGrid API
HTTP_CODE=$(curl -s -o /tmp/sendgrid_response.txt -w "%{http_code}" \
    -X POST "https://api.sendgrid.com/v3/mail/send" \
    -H "Authorization: Bearer $SENDGRID_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD")

# Check response
if [ "$HTTP_CODE" = "202" ]; then
    echo "✅ SUCCESS: Test email sent successfully!"
    echo "   HTTP Status Code: $HTTP_CODE"
    echo "   To: $TEST_EMAIL"
    echo ""
    echo "Check your inbox (and spam folder) for the test email."
    echo ""
    echo "If you don't receive the email within a few minutes:"
    echo "1. Check SendGrid dashboard for delivery logs"
    echo "2. Verify the sender email is verified in SendGrid"
    echo "3. Check if the recipient email is valid"
    echo ""
    echo "================================================================================"
    echo "🎉 All tests passed! Your SendGrid configuration is working."
    echo "================================================================================"
    exit 0
else
    echo "❌ ERROR: Failed to send test email"
    echo "   HTTP Status Code: $HTTP_CODE"
    echo ""

    # Display error response
    if [ -f /tmp/sendgrid_response.txt ]; then
        echo "Error Response:"
        cat /tmp/sendgrid_response.txt | python3 -m json.tool 2>/dev/null || cat /tmp/sendgrid_response.txt
        echo ""
    fi

    # Provide specific solutions based on error code
    case $HTTP_CODE in
        401)
            echo "Solution:"
            echo "1. Your API key is invalid or has been deleted"
            echo "2. Go to https://app.sendgrid.com/settings/api_keys"
            echo "3. Create a new API key with 'Mail Send' permissions"
            echo "4. Update SENDGRID_API_KEY in your .env file"
            ;;
        403)
            echo "Solution:"
            echo "1. Your API key doesn't have the required permissions"
            echo "2. Go to https://app.sendgrid.com/settings/api_keys"
            echo "3. Edit your API key to add 'Mail Send' permissions"
            echo "4. Or create a new key with 'Full Access' permissions"
            ;;
        *)
            echo "Solution:"
            echo "1. Check the error response above for details"
            echo "2. Visit SendGrid dashboard: https://app.sendgrid.com"
            echo "3. Check Activity Feed for more information"
            ;;
    esac

    echo ""
    echo "================================================================================"
    echo "❌ SendGrid configuration test failed."
    echo "================================================================================"
    exit 1
fi
