#!/usr/bin/env python3
"""
SendGrid Configuration Test Script

This script tests your SendGrid configuration by attempting to send a test email.
It provides detailed diagnostics to help identify configuration issues.

Usage:
    python3 test_sendgrid.py your-email@example.com
"""

import os
import sys
from datetime import datetime

# Try to load dotenv if available, otherwise use environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("ℹ️  dotenv not installed - reading from environment variables")
    print("   (Install with: pip install python-dotenv)")
    print()

def test_sendgrid_config(test_email: str):
    """Test SendGrid configuration and send a test email"""

    print("=" * 80)
    print("SendGrid Configuration Test")
    print("=" * 80)
    print()

    # Step 1: Check if SendGrid API key is set
    print("Step 1: Checking SendGrid API Key...")
    api_key = os.getenv('SENDGRID_API_KEY')

    if not api_key:
        print("❌ ERROR: SENDGRID_API_KEY not found in environment variables")
        print()
        print("Solution:")
        print("1. Create or update your .env file in the project root")
        print("2. Add: SENDGRID_API_KEY=SG.your_actual_key_here")
        print("3. Get your API key from: https://app.sendgrid.com/settings/api_keys")
        return False

    # Check if it's the placeholder value
    if api_key == "sendgrid_api_key":
        print("❌ ERROR: SENDGRID_API_KEY is still the placeholder value")
        print()
        print("Solution:")
        print("1. Go to https://app.sendgrid.com/settings/api_keys")
        print("2. Create a new API key with 'Mail Send' permissions")
        print("3. Replace 'sendgrid_api_key' in your .env file with the real key")
        return False

    # Check if it has the correct format
    if not api_key.startswith('SG.'):
        print("⚠️  WARNING: API key doesn't start with 'SG.' - may be invalid")
        print(f"   Current value starts with: {api_key[:10]}...")
    else:
        print(f"✅ API key is set and has correct format (SG.{api_key[3:13]}...)")

    print()

    # Step 2: Check FROM_EMAIL
    print("Step 2: Checking FROM_EMAIL configuration...")
    from_email = os.getenv('FROM_EMAIL', 'noreply@audioposter.com')
    print(f"   FROM_EMAIL: {from_email}")

    if from_email == 'noreply@audioposter.com':
        print("⚠️  WARNING: Using default FROM_EMAIL - you should verify this in SendGrid")

    print()

    # Step 3: Try to import SendGrid
    print("Step 3: Checking SendGrid package installation...")
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content
        print("✅ SendGrid package is installed")
    except ImportError as e:
        print(f"❌ ERROR: SendGrid package not installed: {e}")
        print()
        print("Solution:")
        print("   pip install sendgrid")
        return False

    print()

    # Step 4: Try to send a test email
    print(f"Step 4: Attempting to send test email to {test_email}...")

    try:
        sg = SendGridAPIClient(api_key=api_key)

        message = Mail(
            from_email=Email(from_email, "VoiceFrame Test"),
            to_emails=To(test_email),
            subject="✅ VoiceFrame - SendGrid Test Successful!",
            html_content=Content("text/html", f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #8b5cf6;">✅ SendGrid Test Successful!</h2>
                    <p>Congratulations! Your SendGrid configuration is working correctly.</p>
                    <p>This test email was sent from your VoiceFrame application.</p>
                    <hr style="margin: 20px 0;">
                    <p style="color: #666; font-size: 14px;">
                        <strong>Configuration Details:</strong><br>
                        From Email: {from_email}<br>
                        To Email: {test_email}<br>
                        Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                    </p>
                </body>
            </html>
            """),
            plain_text_content=Content("text/plain", f"""
            ✅ SendGrid Test Successful!

            Congratulations! Your SendGrid configuration is working correctly.
            This test email was sent from your VoiceFrame application.

            Configuration Details:
            From Email: {from_email}
            To Email: {test_email}
            Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
            """)
        )

        response = sg.send(message)

        if response.status_code == 202:
            print("✅ SUCCESS: Test email sent successfully!")
            print(f"   Status Code: {response.status_code}")
            print(f"   To: {test_email}")
            print()
            print("Check your inbox (and spam folder) for the test email.")
            print()
            print("If you don't receive the email within a few minutes:")
            print("1. Check SendGrid dashboard for delivery logs")
            print("2. Verify the sender email is verified in SendGrid")
            print("3. Check if the recipient email is valid")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response body: {response.body}")
            return False

    except Exception as e:
        error_message = str(e)
        print(f"❌ ERROR: Failed to send test email")
        print(f"   Error: {error_message}")
        print()

        # Provide specific solutions based on error type
        if "401" in error_message or "Unauthorized" in error_message:
            print("Solution:")
            print("1. Your API key is invalid or has been deleted")
            print("2. Go to https://app.sendgrid.com/settings/api_keys")
            print("3. Create a new API key with 'Mail Send' permissions")
            print("4. Update SENDGRID_API_KEY in your .env file")
        elif "403" in error_message or "Forbidden" in error_message:
            print("Solution:")
            print("1. Your API key doesn't have the required permissions")
            print("2. Go to https://app.sendgrid.com/settings/api_keys")
            print("3. Edit your API key to add 'Mail Send' permissions")
            print("4. Or create a new key with 'Full Access' permissions")
        elif "sender" in error_message.lower() or "from" in error_message.lower():
            print("Solution:")
            print(f"1. The sender email '{from_email}' is not verified in SendGrid")
            print("2. Go to https://app.sendgrid.com/settings/sender_auth")
            print("3. Verify your sender email or domain")
            print("4. Or update FROM_EMAIL in .env to a verified email")
        else:
            print("Solution:")
            print("1. Check the error message above for details")
            print("2. Visit SendGrid dashboard: https://app.sendgrid.com")
            print("3. Check Activity Feed for more information")

        return False

    print()
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_sendgrid.py your-email@example.com")
        sys.exit(1)

    test_email = sys.argv[1]

    # Validate email format (basic check)
    if "@" not in test_email or "." not in test_email:
        print(f"❌ ERROR: Invalid email format: {test_email}")
        sys.exit(1)

    success = test_sendgrid_config(test_email)

    if success:
        print()
        print("🎉 All tests passed! Your SendGrid configuration is working.")
        sys.exit(0)
    else:
        print()
        print("❌ SendGrid configuration test failed. Please fix the issues above.")
        sys.exit(1)
