#!/usr/bin/env python3
"""
Test script to isolate the method call issue
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent / "backend"))


def test_method_call():
    """Test the method call directly"""

    try:
        from PIL import Image

        from backend.models import SessionModel
        from backend.services.visual_pdf_generator import VisualPDFGenerator

        print("Testing method call...")

        # Create a simple test
        generator = VisualPDFGenerator()

        # Check if the method exists
        if hasattr(generator, "_add_text_to_template"):
            print("Method _add_text_to_template exists")

            # Try to inspect the method
            import inspect

            signature = inspect.signature(generator._add_text_to_template)
            print(f"Method signature: {signature}")

            # Check if it's an async method
            if inspect.iscoroutinefunction(generator._add_text_to_template):
                print("Method is async")
            else:
                print("Method is NOT async")

        else:
            print("Method _add_text_to_template does NOT exist")

    except Exception as e:
        print(f"Error in method test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_method_call()
