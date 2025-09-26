#!/usr/bin/env python3
"""
Test script to reproduce photo upload issues and diagnose the problem
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_photo.jpg"  # You can replace this with your actual photo

def test_photo_upload():
    """Test the photo upload process step by step"""

    print("🔍 Testing Photo Upload Process...")
    print("=" * 50)

    # Step 1: Create a session
    print("1. Creating session...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/session")
        response.raise_for_status()
        session_data = response.json()
        session_token = session_data["session_token"]
        print(f"   ✅ Session created: {session_token}")
    except Exception as e:
        print(f"   ❌ Session creation failed: {e}")
        return False

    # Step 2: Check if test image exists
    print("2. Checking test image...")
    test_image = Path(TEST_IMAGE_PATH)
    if not test_image.exists():
        print(f"   ⚠️  Test image '{TEST_IMAGE_PATH}' not found")
        print("   Please provide a test image or update TEST_IMAGE_PATH in this script")

        # Create a simple test image using PIL if available
        try:
            from PIL import Image
            import io

            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(TEST_IMAGE_PATH)
            print(f"   ✅ Created test image: {TEST_IMAGE_PATH}")
        except ImportError:
            print("   ❌ PIL not available. Please install Pillow or provide a test image")
            return False
        except Exception as e:
            print(f"   ❌ Failed to create test image: {e}")
            return False

    # Step 3: Upload photo
    print("3. Uploading photo...")
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'photo': (TEST_IMAGE_PATH, f, 'image/jpeg')}
            response = requests.post(
                f"{API_BASE_URL}/api/session/{session_token}/photo",
                files=files
            )

            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Photo uploaded successfully: {result}")
                return True
            else:
                print(f"   ❌ Photo upload failed:")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"   ❌ Photo upload error: {e}")
        return False

def test_content_filter_status():
    """Test the content filter status"""
    print("\n🔍 Testing Content Filter Status...")
    print("=" * 50)

    try:
        response = requests.get(f"{API_BASE_URL}/api/security/content-filter-status")
        response.raise_for_status()
        status = response.json()
        print(f"   Content Filter Status: {json.dumps(status, indent=2)}")
    except Exception as e:
        print(f"   ❌ Failed to get content filter status: {e}")

if __name__ == "__main__":
    print("🚀 Photo Upload Diagnostic Tool")
    print("=" * 50)

    # Test content filter status first
    test_content_filter_status()

    # Test photo upload
    success = test_photo_upload()

    if success:
        print("\n✅ Photo upload test PASSED!")
    else:
        print("\n❌ Photo upload test FAILED!")
        print("Check the error messages above for details.")

    sys.exit(0 if success else 1)
