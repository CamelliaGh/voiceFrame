#!/usr/bin/env python3
"""
Local Background Issue Diagnostic Script

This script helps diagnose background issues without requiring database access.
It checks file system structure and provides Docker commands to run the full diagnostic.

Usage:
    python3 scripts/diagnose_background_local.py
"""

import os
import sys
import json
from pathlib import Path


def check_local_directory_structure():
    """Check the local directory structure"""
    print("📂 Checking local directory structure...")

    directories_to_check = [
        "backgrounds",
        "backgrounds/admin",
        "fonts",
        "fonts/admin",
    ]

    for directory in directories_to_check:
        if os.path.exists(directory):
            try:
                files = os.listdir(directory)
                print(f"✅ {directory}: {len(files)} files")
                if files:
                    for file in files[:5]:  # Show first 5 files
                        file_path = os.path.join(directory, file)
                        size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                        print(f"    - {file} ({size} bytes)")
                    if len(files) > 5:
                        print(f"    ... and {len(files) - 5} more")
            except PermissionError:
                print(f"❌ {directory}: Permission denied")
        else:
            print(f"❌ {directory}: Does not exist")

    print(f"\n📍 Current working directory: {os.getcwd()}")


def check_docker_compose_config():
    """Check Docker Compose configuration for volume mounts"""
    print("🐳 Checking Docker Compose configuration...")

    compose_files = [
        "docker-compose.yml",
        "docker-compose.prod.yml",
        "docker-compose.mvp.yml"
    ]

    for compose_file in compose_files:
        if os.path.exists(compose_file):
            print(f"✅ Found {compose_file}")
            try:
                with open(compose_file, 'r') as f:
                    content = f.read()
                    if './backgrounds:/app/backgrounds' in content:
                        print(f"  ✅ Background volume mount found")
                    else:
                        print(f"  ❌ Background volume mount NOT found")

                    if './fonts:/app/fonts' in content:
                        print(f"  ✅ Font volume mount found")
                    else:
                        print(f"  ❌ Font volume mount NOT found")
            except Exception as e:
                print(f"  ❌ Error reading {compose_file}: {e}")
        else:
            print(f"❌ {compose_file} not found")


def provide_docker_commands():
    """Provide Docker commands to run the full diagnostic"""
    print("🔧 Docker Commands for Full Diagnosis")
    print("=" * 50)

    print("To run the full diagnostic script inside the Docker container:")
    print()

    # Check if we're likely in production or development
    if os.path.exists("docker-compose.prod.yml"):
        print("For PRODUCTION environment:")
        print("  docker-compose -f docker-compose.prod.yml exec api python3 scripts/diagnose_background_issue.py")
        print()

    if os.path.exists("docker-compose.yml"):
        print("For DEVELOPMENT environment:")
        print("  docker-compose exec api python3 scripts/diagnose_background_issue.py")
        print()

    print("Other useful Docker commands:")
    print()
    print("1. Check if containers are running:")
    print("   docker-compose ps")
    print()
    print("2. Check background files in API container:")
    print("   docker-compose exec api ls -la /app/backgrounds/admin/")
    print()
    print("3. Check background files in Nginx container:")
    print("   docker-compose exec nginx ls -la /var/www/backgrounds/admin/")
    print()
    print("4. Check database backgrounds:")
    print("   docker-compose exec db psql -U audioposter -d audioposter -c \"SELECT name, display_name, file_path, is_active FROM admin_backgrounds;\"")
    print()
    print("5. Test the API endpoint:")
    print("   curl http://localhost:8000/api/resources/backgrounds")
    print()
    print("6. Check API container logs:")
    print("   docker-compose logs api | grep -i background")


def check_git_status():
    """Check if the latest changes are committed"""
    print("📝 Checking Git status...")

    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️  Uncommitted changes found:")
                for line in result.stdout.strip().split('\n'):
                    print(f"    {line}")
                print("  Consider committing changes before deploying to production")
            else:
                print("✅ Working directory is clean")
        else:
            print("❌ Error checking git status")
    except FileNotFoundError:
        print("❌ Git not found")
    except Exception as e:
        print(f"❌ Error checking git status: {e}")


def main():
    print("🔍 Local Background Issue Diagnostic Tool")
    print("=" * 50)

    # Check current environment
    print(f"🐍 Python version: {sys.version}")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🔧 Script location: {__file__}")
    print()

    # Run local checks
    check_local_directory_structure()
    print()

    check_docker_compose_config()
    print()

    check_git_status()
    print()

    provide_docker_commands()
    print()

    # Summary and next steps
    print("🎯 NEXT STEPS")
    print("=" * 50)
    print("1. Use the Docker commands above to run the full diagnostic")
    print("2. If you're on production, make sure to pull the latest changes first:")
    print("   git pull origin main")
    print("3. Restart the API container after pulling changes:")
    print("   docker-compose -f docker-compose.prod.yml restart api")
    print("4. Run the full diagnostic to verify the fix")
    print("5. Test the admin panel in your browser")


if __name__ == "__main__":
    main()
