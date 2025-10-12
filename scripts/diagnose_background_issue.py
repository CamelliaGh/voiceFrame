#!/usr/bin/env python3
"""
Background Issue Diagnostic Script

This script helps diagnose why backgrounds are not showing in the admin panel
but are visible in the customization panel.

Usage:
    python3 scripts/diagnose_background_issue.py

Or from Docker container:
    docker-compose -f docker-compose.prod.yml exec api python3 scripts/diagnose_background_issue.py
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from database import get_db
    from models import AdminBackground
    from services.admin_resource_service import admin_resource_service
    from sqlalchemy.orm import Session
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root or from within the Docker container")
    sys.exit(1)


def check_database_backgrounds():
    """Check what backgrounds are in the database"""
    print("🔍 Checking database backgrounds...")

    db: Session = next(get_db())
    try:
        backgrounds = db.query(AdminBackground).all()

        if not backgrounds:
            print("❌ No backgrounds found in database")
            return []

        print(f"✅ Found {len(backgrounds)} backgrounds in database:")

        for bg in backgrounds:
            status = "✅ Active" if bg.is_active else "❌ Inactive"
            print(f"  - {bg.name} ({bg.display_name}) - {status}")
            print(f"    File: {bg.file_path}")
            print(f"    Category: {bg.category}, Orientation: {bg.orientation}")
            print()

        return backgrounds

    finally:
        db.close()


def check_file_existence(backgrounds):
    """Check if background files actually exist on disk"""
    print("📁 Checking file existence...")

    existing_files = []
    missing_files = []

    for bg in backgrounds:
        if not bg.file_path:
            print(f"❌ {bg.name}: No file path in database")
            missing_files.append(bg)
            continue

        file_path = bg.file_path
        file_exists = False
        actual_path = None

        # Check multiple possible locations
        possible_paths = [
            file_path,  # As stored in DB
            os.path.join(os.getcwd(), file_path),  # Relative to current working directory
            f"/{file_path}" if not file_path.startswith('/') else file_path,  # Absolute path
        ]

        for path in possible_paths:
            if os.path.exists(path):
                file_exists = True
                actual_path = path
                break

        if file_exists:
            print(f"✅ {bg.name}: Found at {actual_path}")
            existing_files.append((bg, actual_path))
        else:
            print(f"❌ {bg.name}: File not found")
            print(f"    Searched in:")
            for path in possible_paths:
                print(f"      - {path}")
            missing_files.append(bg)

    print(f"\n📊 Summary: {len(existing_files)} files found, {len(missing_files)} missing")
    return existing_files, missing_files


def check_admin_resource_service():
    """Check what the admin resource service returns"""
    print("🔧 Checking admin resource service...")

    db: Session = next(get_db())
    try:
        # Test the service that the customization panel uses
        backgrounds = admin_resource_service.get_active_backgrounds(db)

        print(f"✅ Admin resource service returns {len(backgrounds)} backgrounds:")
        for bg in backgrounds:
            print(f"  - {bg['name']} ({bg['display_name']})")
            print(f"    File: {bg['file_path']}")
            print(f"    Category: {bg['category']}, Orientation: {bg['orientation']}")
            print()

        return backgrounds

    finally:
        db.close()


def check_directory_structure():
    """Check the directory structure"""
    print("📂 Checking directory structure...")

    directories_to_check = [
        "backgrounds",
        "backgrounds/admin",
        "/app/backgrounds",
        "/app/backgrounds/admin",
        "/var/www/backgrounds",
        "/var/www/backgrounds/admin",
    ]

    for directory in directories_to_check:
        if os.path.exists(directory):
            try:
                files = os.listdir(directory)
                print(f"✅ {directory}: {len(files)} files")
                if files:
                    for file in files[:5]:  # Show first 5 files
                        print(f"    - {file}")
                    if len(files) > 5:
                        print(f"    ... and {len(files) - 5} more")
            except PermissionError:
                print(f"❌ {directory}: Permission denied")
        else:
            print(f"❌ {directory}: Does not exist")

    print(f"\n📍 Current working directory: {os.getcwd()}")


def check_api_endpoints():
    """Test the API endpoints"""
    print("🌐 API endpoint information:")
    print("  - Customization panel uses: GET /api/resources/backgrounds")
    print("  - Admin panel uses: GET /admin/backgrounds")
    print("  - The difference is that /api/resources/backgrounds filters by file existence")
    print("  - While /admin/backgrounds returns all database entries regardless of file existence")


def main():
    print("🔍 Background Issue Diagnostic Tool")
    print("=" * 50)

    # Check current environment
    print(f"🐍 Python version: {sys.version}")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🔧 Script location: {__file__}")
    print()

    # Run all checks
    backgrounds = check_database_backgrounds()
    print()

    if backgrounds:
        existing_files, missing_files = check_file_existence(backgrounds)
        print()

        service_backgrounds = check_admin_resource_service()
        print()

        check_directory_structure()
        print()

        check_api_endpoints()
        print()

        # Summary and recommendations
        print("🎯 DIAGNOSIS SUMMARY")
        print("=" * 50)

        if not service_backgrounds:
            print("❌ ISSUE IDENTIFIED: Admin resource service returns no backgrounds")
            print("   This means the file existence check is failing")
            print()
            print("🔧 RECOMMENDED ACTIONS:")
            print("1. Check if background files exist in the correct location")
            print("2. Verify Docker volume mounts are correct")
            print("3. Check file permissions")
            print("4. Restart the API container after fixing file issues")
        elif len(service_backgrounds) < len([bg for bg in backgrounds if bg.is_active]):
            print("⚠️  PARTIAL ISSUE: Some backgrounds are missing")
            print(f"   Database has {len([bg for bg in backgrounds if bg.is_active])} active backgrounds")
            print(f"   Service returns {len(service_backgrounds)} backgrounds")
        else:
            print("✅ No obvious issues found")
            print("   The problem might be in the admin panel frontend or caching")

    else:
        print("❌ No backgrounds in database - admin panel needs to upload some backgrounds first")


if __name__ == "__main__":
    main()
