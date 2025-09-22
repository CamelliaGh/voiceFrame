#!/usr/bin/env python3
"""
Test script to verify the API session update flow
"""
import json

import requests


def test_api_flow():
    """Test the API session update and preview flow"""

    base_url = "http://localhost:8000"

    print("Testing API flow...")

    # First, let's get the current session
    try:
        # Get session token from a real session (you'll need to replace this with an actual token)
        session_token = "0370adce-7cf5-4118-9367-068eb3f32da2"  # From the logs

        # Get current session
        response = requests.get(f"{base_url}/api/session/{session_token}")
        if response.status_code == 200:
            session_data = response.json()
            print(f"Current session data:")
            print(f"  custom_text: '{session_data.get('custom_text')}'")
            print(f"  font_id: '{session_data.get('font_id')}'")
            print(f"  template_id: '{session_data.get('template_id')}'")

            # Update the session with custom text
            update_data = {
                "custom_text": "TEST TEXT FROM API FLOW",
                "font_id": "script",
            }

            print(f"\nUpdating session with: {update_data}")
            update_response = requests.put(
                f"{base_url}/api/session/{session_token}", json=update_data
            )

            if update_response.status_code == 200:
                print("Session updated successfully")

                # Get the updated session
                updated_response = requests.get(
                    f"{base_url}/api/session/{session_token}"
                )
                if updated_response.status_code == 200:
                    updated_session = updated_response.json()
                    print(f"Updated session data:")
                    print(f"  custom_text: '{updated_session.get('custom_text')}'")
                    print(f"  font_id: '{updated_session.get('font_id')}'")
                    print(f"  template_id: '{updated_session.get('template_id')}'")

                    # Try to generate preview
                    print(f"\nAttempting to generate preview...")
                    preview_response = requests.get(
                        f"{base_url}/api/session/{session_token}/preview"
                    )
                    print(f"Preview response status: {preview_response.status_code}")

                    if preview_response.status_code != 200:
                        print(f"Preview error: {preview_response.text}")
                    else:
                        print("Preview generated successfully!")

                else:
                    print(
                        f"Failed to get updated session: {updated_response.status_code}"
                    )
            else:
                print(f"Failed to update session: {update_response.status_code}")
                print(f"Error: {update_response.text}")
        else:
            print(f"Failed to get session: {response.status_code}")
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error in API test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_api_flow()
