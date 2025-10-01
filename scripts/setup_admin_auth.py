#!/usr/bin/env python3
"""
Admin Authentication Setup Script

This script helps you set up admin authentication for the VoiceFrame admin panel.
It provides multiple authentication options to choose from.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def show_authentication_options():
    """Display available authentication options"""
    print("🔐 VoiceFrame Admin Authentication Setup")
    print("=" * 50)
    print()
    print("Choose your preferred authentication method:")
    print()
    print("1. 🎯 SIMPLE PASSWORD (Recommended for Development)")
    print("   - Single password for all admin access")
    print("   - Easy to set up and use")
    print("   - Perfect for development and testing")
    print()
    print("2. 🔑 API KEY (Current Method)")
    print("   - Single API key for all admin access")
    print("   - Good for API-only access")
    print("   - Already configured")
    print()
    print("3. 👤 USERNAME/PASSWORD with JWT (Production Ready)")
    print("   - Multiple admin users with individual accounts")
    print("   - JWT token-based authentication")
    print("   - User management capabilities")
    print("   - Best for production environments")
    print()
    print("4. 🔧 CUSTOM SETUP")
    print("   - Configure your own authentication method")
    print()

def setup_simple_password():
    """Set up simple password authentication"""
    print("🎯 Setting up Simple Password Authentication")
    print("-" * 40)

    password = input("Enter admin password (default: admin123): ").strip()
    if not password:
        password = "admin123"

    # Add to .env file
    env_file = Path(".env")
    env_content = ""

    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()

    # Check if ADMIN_PASSWORD already exists
    if "ADMIN_PASSWORD=" in env_content:
        print("⚠️  ADMIN_PASSWORD already exists in .env file")
        replace = input("Replace existing password? (y/N): ").strip().lower()
        if replace in ['y', 'yes']:
            # Replace existing line
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith("ADMIN_PASSWORD="):
                    new_lines.append(f"ADMIN_PASSWORD={password}")
                else:
                    new_lines.append(line)
            env_content = '\n'.join(new_lines)
        else:
            print("❌ Setup cancelled")
            return
    else:
        # Add new line
        if env_content and not env_content.endswith('\n'):
            env_content += '\n'
        env_content += f"ADMIN_PASSWORD={password}\n"

    # Write back to .env file
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"✅ Simple password authentication configured!")
    print(f"   Password: {password}")
    print()
    print("📖 How to use:")
    print("   1. Start your backend server")
    print("   2. Make requests with Authorization header:")
    print(f"      Authorization: Bearer {password}")
    print("   3. Test endpoint: GET /admin/simple/test")
    print()

def setup_api_key():
    """Set up API key authentication"""
    print("🔑 Setting up API Key Authentication")
    print("-" * 40)

    api_key = input("Enter admin API key (press Enter for auto-generated): ").strip()
    if not api_key:
        import secrets
        api_key = secrets.token_urlsafe(32)
        print(f"Generated API key: {api_key}")

    # Add to .env file
    env_file = Path(".env")
    env_content = ""

    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()

    # Check if ADMIN_API_KEY already exists
    if "ADMIN_API_KEY=" in env_content:
        print("⚠️  ADMIN_API_KEY already exists in .env file")
        replace = input("Replace existing API key? (y/N): ").strip().lower()
        if replace in ['y', 'yes']:
            # Replace existing line
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith("ADMIN_API_KEY="):
                    new_lines.append(f"ADMIN_API_KEY={api_key}")
                else:
                    new_lines.append(line)
            env_content = '\n'.join(new_lines)
        else:
            print("❌ Setup cancelled")
            return
    else:
        # Add new line
        if env_content and not env_content.endswith('\n'):
            env_content += '\n'
        env_content += f"ADMIN_API_KEY={api_key}\n"

    # Write back to .env file
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"✅ API key authentication configured!")
    print(f"   API Key: {api_key}")
    print()
    print("📖 How to use:")
    print("   1. Start your backend server")
    print("   2. Make requests with Authorization header:")
    print(f"      Authorization: Bearer {api_key}")
    print("   3. Test endpoint: GET /admin/stats")
    print()

def setup_jwt_auth():
    """Set up JWT-based authentication"""
    print("👤 Setting up JWT Authentication")
    print("-" * 40)
    print("This requires database setup and user creation.")
    print()

    try:
        from database import SessionLocal
        from models import AdminUser
        from services.admin_auth import AdminAuthService

        print("✅ Database models are available")
        print()
        print("To complete JWT setup:")
        print("1. Run database migrations to create admin_users table")
        print("2. Create an admin user using:")
        print("   python3 scripts/create_admin_user.py")
        print()
        print("📖 How to use JWT authentication:")
        print("   1. Login: POST /admin/auth/login")
        print("   2. Use token: Authorization: Bearer <jwt_token>")
        print("   3. Test endpoint: GET /admin/auth/me")
        print()

    except ImportError as e:
        print(f"❌ Database setup required: {e}")
        print("Please ensure your backend dependencies are installed")

def main():
    """Main setup function"""
    show_authentication_options()

    while True:
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            setup_simple_password()
            break
        elif choice == "2":
            setup_api_key()
            break
        elif choice == "3":
            setup_jwt_auth()
            break
        elif choice == "4":
            print("🔧 Custom Setup")
            print("You can modify the authentication system by editing:")
            print("- backend/services/admin_auth.py")
            print("- backend/routers/admin_auth.py")
            print("- backend/routers/simple_admin.py")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
