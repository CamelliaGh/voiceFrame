#!/usr/bin/env python3
"""
Seed Admin Data Script

Populates the admin tables with existing fonts and backgrounds from the filesystem.
This script reads the existing fonts and backgrounds directories and creates
corresponding entries in the admin database tables.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import SessionLocal
from models import AdminFont, AdminBackground, AdminSuggestedText
from sqlalchemy.orm import Session


def seed_fonts(db: Session):
    """Seed fonts from the fonts directory"""
    fonts_dir = Path("fonts")

    if not fonts_dir.exists():
        print("❌ Fonts directory not found")
        return

    font_files = list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf"))

    if not font_files:
        print("❌ No font files found in fonts directory")
        return

    # Font metadata
    font_metadata = {
        "classic.ttf": {
            "display_name": "Classic Serif",
            "description": "Lora font for elegant serif with excellent readability"
        },
        "elegant.ttf": {
            "display_name": "Elegant Display",
            "description": "Playfair Display for sophisticated designs"
        },
        "modern.ttf": {
            "display_name": "Modern Sans",
            "description": "Open Sans for clean, modern sans-serif"
        },
        "vintage.ttf": {
            "display_name": "Vintage Classic",
            "description": "Cinzel for classic serif with vintage feel"
        },
        "script.ttf": {
            "display_name": "Script Handwriting",
            "description": "Script/handwriting style font for decorative text"
        }
    }

    seeded_count = 0
    for font_file in font_files:
        font_name = font_file.name
        file_path = str(font_file.absolute())
        file_size = font_file.stat().st_size

        # Check if font already exists
        existing_font = db.query(AdminFont).filter(AdminFont.name == font_name).first()
        if existing_font:
            print(f"⚠️  Font '{font_name}' already exists, skipping")
            continue

        # Get metadata
        metadata = font_metadata.get(font_name, {
            "display_name": font_name.replace('.ttf', '').replace('.otf', '').title(),
            "description": f"Custom font: {font_name}"
        })

        # Create font entry
        font = AdminFont(
            name=font_name,
            display_name=metadata["display_name"],
            file_path=file_path,
            file_size=file_size,
            description=metadata["description"],
            is_active=True,
            is_premium=False
        )

        db.add(font)
        seeded_count += 1
        print(f"✅ Added font: {font_name}")

    db.commit()
    print(f"🎉 Seeded {seeded_count} fonts")


def seed_backgrounds(db: Session):
    """Seed backgrounds from the backgrounds directory"""
    backgrounds_dir = Path("backgrounds")

    if not backgrounds_dir.exists():
        print("❌ Backgrounds directory not found")
        return

    background_files = list(backgrounds_dir.glob("*.jpg")) + list(backgrounds_dir.glob("*.png")) + list(backgrounds_dir.glob("*.jpeg"))

    if not background_files:
        print("❌ No background files found in backgrounds directory")
        return

    # Background metadata
    background_metadata = {
        "237.jpg": {
            "display_name": "Abstract Blurred",
            "description": "Abstract blurred background for modern designs",
            "category": "abstract"
        },
        "beautiful-roses-great-white-wooden-background-with-space-right.jpg": {
            "display_name": "Roses on Wood",
            "description": "Beautiful roses on white wooden background",
            "category": "romantic"
        },
        "copy-space-with-cute-hearts.jpg": {
            "display_name": "Cute Hearts",
            "description": "Copy space with cute hearts design",
            "category": "romantic"
        },
        "flat-lay-small-cute-hearts.jpg": {
            "display_name": "Flat Lay Hearts",
            "description": "Flat lay design with small cute hearts",
            "category": "romantic"
        }
    }

    seeded_count = 0
    for bg_file in background_files:
        bg_name = bg_file.name
        file_path = str(bg_file.absolute())
        file_size = bg_file.stat().st_size

        # Check if background already exists
        existing_bg = db.query(AdminBackground).filter(AdminBackground.name == bg_name).first()
        if existing_bg:
            print(f"⚠️  Background '{bg_name}' already exists, skipping")
            continue

        # Get metadata
        metadata = background_metadata.get(bg_name, {
            "display_name": bg_name.replace('.jpg', '').replace('.png', '').replace('.jpeg', '').replace('-', ' ').title(),
            "description": f"Background image: {bg_name}",
            "category": "general"
        })

        # Create background entry
        background = AdminBackground(
            name=bg_name,
            display_name=metadata["display_name"],
            file_path=file_path,
            file_size=file_size,
            description=metadata["description"],
            category=metadata["category"],
            is_active=True,
            is_premium=False,
            usage_count=0
        )

        db.add(background)
        seeded_count += 1
        print(f"✅ Added background: {bg_name}")

    db.commit()
    print(f"🎉 Seeded {seeded_count} backgrounds")


def seed_suggested_texts(db: Session):
    """Seed suggested texts with common messages"""
    suggested_texts = [
        # Romantic messages
        {"text": "Happy Anniversary, my love! 💕", "category": "romantic", "is_premium": False},
        {"text": "You make my heart skip a beat ❤️", "category": "romantic", "is_premium": False},
        {"text": "Forever and always together 💖", "category": "romantic", "is_premium": False},
        {"text": "My love for you grows stronger every day", "category": "romantic", "is_premium": False},

        # Birthday messages
        {"text": "Happy Birthday! 🎉", "category": "birthday", "is_premium": False},
        {"text": "Wishing you the best year yet! 🎂", "category": "birthday", "is_premium": False},
        {"text": "Another year older, wiser, and more amazing! ✨", "category": "birthday", "is_premium": False},

        # Anniversary messages
        {"text": "Happy Anniversary! 🎊", "category": "anniversary", "is_premium": False},
        {"text": "Celebrating another year of love and happiness", "category": "anniversary", "is_premium": False},
        {"text": "Together through thick and thin 💕", "category": "anniversary", "is_premium": False},

        # Holiday messages
        {"text": "Merry Christmas! 🎄", "category": "holiday", "is_premium": False},
        {"text": "Happy New Year! 🎊", "category": "holiday", "is_premium": False},
        {"text": "Happy Valentine's Day! 💘", "category": "holiday", "is_premium": False},

        # Generic messages
        {"text": "Thank you for being amazing! 🙏", "category": "general", "is_premium": False},
        {"text": "You're the best! ⭐", "category": "general", "is_premium": False},
        {"text": "Sending love and good vibes! ✨", "category": "general", "is_premium": False},

        # Premium messages (examples)
        {"text": "You are my sunshine on the darkest days ☀️", "category": "romantic", "is_premium": True},
        {"text": "Every moment with you is a treasure 💎", "category": "romantic", "is_premium": True},
        {"text": "Your smile lights up my world 🌟", "category": "romantic", "is_premium": True},
    ]

    seeded_count = 0
    for text_data in suggested_texts:
        # Check if text already exists
        existing_text = db.query(AdminSuggestedText).filter(
            AdminSuggestedText.text == text_data["text"]
        ).first()

        if existing_text:
            print(f"⚠️  Suggested text already exists, skipping")
            continue

        # Create suggested text entry
        suggested_text = AdminSuggestedText(
            text=text_data["text"],
            category=text_data["category"],
            is_premium=text_data["is_premium"],
            is_active=True,
            usage_count=0
        )

        db.add(suggested_text)
        seeded_count += 1
        print(f"✅ Added suggested text: {text_data['text'][:50]}...")

    db.commit()
    print(f"🎉 Seeded {seeded_count} suggested texts")


def main():
    """Main function to seed all admin data"""
    print("🌱 Starting admin data seeding...")

    # Create database session
    db = SessionLocal()

    try:
        print("\n📝 Seeding fonts...")
        seed_fonts(db)

        print("\n🖼️  Seeding backgrounds...")
        seed_backgrounds(db)

        print("\n💬 Seeding suggested texts...")
        seed_suggested_texts(db)

        print("\n✅ Admin data seeding completed successfully!")

        # Show summary
        font_count = db.query(AdminFont).count()
        bg_count = db.query(AdminBackground).count()
        text_count = db.query(AdminSuggestedText).count()

        print(f"\n📊 Summary:")
        print(f"   Fonts: {font_count}")
        print(f"   Backgrounds: {bg_count}")
        print(f"   Suggested Texts: {text_count}")

    except Exception as e:
        print(f"❌ Error seeding admin data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
