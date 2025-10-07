#!/usr/bin/env python3
"""
Test script for mobile image preview functionality
"""

import requests
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_image_preview_endpoint():
    """Test the image preview endpoint"""
    base_url = "http://localhost:8000"

    # Test with a sample session token (you'll need to replace this with a real one)
    session_token = "test-session-token"

    print("🧪 Testing Image Preview Endpoint")
    print("=" * 50)

    # Test the image preview endpoint
    image_url = f"{base_url}/api/session/{session_token}/preview/image"
    print(f"Testing: {image_url}")

    try:
        response = requests.get(image_url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ Image preview endpoint is working!")
        else:
            print(f"❌ Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

    print("\n" + "=" * 50)

    # Test the regular PDF preview endpoint for comparison
    pdf_url = f"{base_url}/api/session/{session_token}/preview"
    print(f"Testing PDF endpoint: {pdf_url}")

    try:
        response = requests.get(pdf_url, timeout=30)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ PDF preview endpoint is working!")
        else:
            print(f"❌ Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_mobile_detection():
    """Test mobile detection logic"""
    print("\n🧪 Testing Mobile Detection Logic")
    print("=" * 50)

    # Test user agents
    test_user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]

    for user_agent in test_user_agents:
        print(f"\nUser Agent: {user_agent}")

        # Simulate mobile detection logic
        mobile_regex = r"android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile|tablet"
        import re
        is_mobile = bool(re.search(mobile_regex, user_agent, re.IGNORECASE))

        print(f"Detected as mobile: {is_mobile}")

if __name__ == "__main__":
    print("🚀 Mobile Preview Test Suite")
    print("=" * 50)

    # Test mobile detection
    test_mobile_detection()

    # Test image preview endpoint (only if server is running)
    try:
        test_image_preview_endpoint()
    except Exception as e:
        print(f"⚠️  Could not test image preview endpoint: {e}")
        print("Make sure the backend server is running on localhost:8000")

    print("\n✅ Test suite completed!")
