#!/usr/bin/env python3
"""
Migrate existing hardcoded backgrounds to admin panel database

This script adds the existing background images from the backgrounds/ directory
to the admin panel database, making them manageable through the UI.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from backend.database import SessionLocal
from backend.models import AdminBackground
import uuid


def migrate_backgrounds():
    """Migrate hardcoded backgrounds to admin panel database"""
    db = SessionLocal()

    # Define existing backgrounds with their original IDs
    backgrounds = [
        {
            'name': 'abstract-blurred',
            'display_name': 'Abstract Blurred',
            'description': 'Soft abstract background',
            'category': 'Abstract',
            'file_path': 'backgrounds/237.jpg',
            'orientation': 'both'
        },
        {
            'name': 'roses-wooden',
            'display_name': 'Roses & Wood',
            'description': 'Beautiful roses on wooden background',
            'category': 'Romantic',
            'file_path': 'backgrounds/beautiful-roses-great-white-wooden-background-with-space-right.jpg',
            'orientation': 'both'
        },
        {
            'name': 'cute-hearts',
            'display_name': 'Cute Hearts',
            'description': 'Romantic hearts background',
            'category': 'Romantic',
            'file_path': 'backgrounds/copy-space-with-cute-hearts.jpg',
            'orientation': 'both'
        },
        {
            'name': 'flat-lay-hearts',
            'display_name': 'Flat Lay Hearts',
            'description': 'Elegant flat lay hearts',
            'category': 'Romantic',
            'file_path': 'backgrounds/flat-lay-small-cute-hearts.jpg',
            'orientation': 'both'
        }
    ]

    print("Starting background migration...")
    print(f"Found {len(backgrounds)} backgrounds to migrate\n")

    migrated_count = 0
    skipped_count = 0

    for bg_data in backgrounds:
        # Check if already exists
        existing = db.query(AdminBackground).filter(
            AdminBackground.name == bg_data['name']
        ).first()

        if existing:
            print(f"⏭️  Background '{bg_data['name']}' already exists, skipping...")
            skipped_count += 1
            continue

        # Check if file exists
        if not os.path.exists(bg_data['file_path']):
            print(f"⚠️  Warning: File not found for '{bg_data['name']}': {bg_data['file_path']}")
            print(f"   Skipping this background...")
            skipped_count += 1
            continue

        # Get file size
        file_size = os.path.getsize(bg_data['file_path'])

        # Create new background entry
        background = AdminBackground(
            id=str(uuid.uuid4()),
            name=bg_data['name'],
            display_name=bg_data['display_name'],
            description=bg_data['description'],
            category=bg_data['category'],
            file_path=bg_data['file_path'],
            file_size=file_size,
            orientation=bg_data['orientation'],
            is_premium=False,
            is_active=True,
            usage_count=0
        )

        db.add(background)
        print(f"✅ Added background: '{bg_data['name']}' ({bg_data['display_name']})")
        print(f"   File: {bg_data['file_path']} ({file_size} bytes)")
        print(f"   Category: {bg_data['category']}, Orientation: {bg_data['orientation']}\n")
        migrated_count += 1

    # Commit all changes
    try:
        db.commit()
        print("\n" + "="*60)
        print("Migration complete!")
        print(f"✅ Migrated: {migrated_count} backgrounds")
        print(f"⏭️  Skipped: {skipped_count} backgrounds")
        print("="*60)

        if migrated_count > 0:
            print("\n📝 Next steps:")
            print("1. Restart your backend server to pick up the changes")
            print("2. Go to /admin to verify backgrounds appear correctly")
            print("3. Test background selection in the customization panel")
            print("4. Generate a preview PDF to ensure backgrounds render properly")
    except Exception as e:
        print(f"\n❌ Error committing changes: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    return migrated_count > 0


if __name__ == '__main__':
    print("🎨 Background Migration Tool")
    print("="*60)
    print("This script migrates existing hardcoded backgrounds")
    print("to the admin panel database for dynamic management.")
    print("="*60 + "\n")

    # Verify we're in the project root
    if not os.path.exists('backgrounds'):
        print("❌ Error: backgrounds/ directory not found")
        print("Please run this script from the project root directory")
        sys.exit(1)

    if not os.path.exists('backend'):
        print("❌ Error: backend/ directory not found")
        print("Please run this script from the project root directory")
        sys.exit(1)

    try:
        success = migrate_backgrounds()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
