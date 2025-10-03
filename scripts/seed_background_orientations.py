#!/usr/bin/env python3
"""
Seed Background Orientations Script

This script analyzes existing background images and assigns appropriate orientation values
based on their aspect ratios and visual characteristics.
"""

import os
import sys
from PIL import Image

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db
from backend.models import AdminBackground
from sqlalchemy.orm import Session

def analyze_image_orientation(image_path: str) -> str:
    """
    Analyze an image to determine its best orientation.
    Returns 'portrait', 'landscape', or 'both'
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            aspect_ratio = width / height

            # Determine orientation based on aspect ratio
            if aspect_ratio > 1.3:  # Significantly wider than tall
                return 'landscape'
            elif aspect_ratio < 0.77:  # Significantly taller than wide
                return 'portrait'
            else:  # Close to square or moderate aspect ratio
                return 'both'
    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")
        return 'both'  # Default to both if we can't analyze

def seed_background_orientations():
    """Seed existing backgrounds with orientation values"""

    # Background orientation mappings based on visual analysis
    background_orientations = {
        '237.jpg': 'both',  # Abstract blurred - works for both
        'beautiful-roses-great-white-wooden-background-with-space-right.jpg': 'landscape',  # Wide composition with space on right
        'copy-space-with-cute-hearts.jpg': 'both',  # Hearts pattern - works for both
        'flat-lay-small-cute-hearts.jpg': 'both',  # Flat lay hearts - works for both
    }

    # Get database session
    db = next(get_db())

    try:
        # Get all existing backgrounds
        backgrounds = db.query(AdminBackground).all()

        print(f"Found {len(backgrounds)} backgrounds to update...")

        for background in backgrounds:
            # Extract filename from file_path
            filename = os.path.basename(background.file_path)

            # Determine orientation
            if filename in background_orientations:
                orientation = background_orientations[filename]
            else:
                # Try to analyze the image file if it exists
                full_path = os.path.join('backgrounds', filename)
                if os.path.exists(full_path):
                    orientation = analyze_image_orientation(full_path)
                else:
                    orientation = 'both'  # Default fallback

            # Update the background
            background.orientation = orientation
            print(f"Updated {background.display_name} ({filename}) -> {orientation}")

        # Commit changes
        db.commit()
        print(f"\nSuccessfully updated orientations for {len(backgrounds)} backgrounds!")

    except Exception as e:
        print(f"Error updating backgrounds: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding background orientations...")
    seed_background_orientations()
    print("Done!")
