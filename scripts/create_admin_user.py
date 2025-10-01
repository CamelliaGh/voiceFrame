#!/usr/bin/env python3
"""
Create Admin User Script

Creates an initial admin user for the admin panel.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import SessionLocal
from models import AdminUser
from services.admin_auth import AdminAuthService


def create_admin_user(username: str, email: str, password: str, is_superuser: bool = True):
    """Create an admin user"""
    db = SessionLocal()
    admin_auth = AdminAuthService()

    try:
        # Check if user already exists
        existing_user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists")
            return False

        # Check if email already exists
        existing_email = db.query(AdminUser).filter(AdminUser.email == email).first()
        if existing_email:
            print(f"❌ Email '{email}' already exists")
            return False

        # Create new user
        hashed_password = admin_auth.get_password_hash(password)
        new_user = AdminUser(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_superuser=is_superuser,
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Superuser: {is_superuser}")
        print(f"   User ID: {new_user.id}")

        return True

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main function to create admin user"""
    print("🔐 Creating admin user...")

    # Get user input
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username is required")
        return

    email = input("Enter email: ").strip()
    if not email:
        print("❌ Email is required")
        return

    password = input("Enter password: ").strip()
    if not password:
        print("❌ Password is required")
        return

    is_superuser_input = input("Is superuser? (y/N): ").strip().lower()
    is_superuser = is_superuser_input in ['y', 'yes', 'true', '1']

    # Create the user
    success = create_admin_user(username, email, password, is_superuser)

    if success:
        print("\n🎉 Admin user setup complete!")
        print("\nYou can now login to the admin panel using:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("\nAPI endpoint: POST /admin/auth/login")
    else:
        print("\n❌ Failed to create admin user")


if __name__ == "__main__":
    main()
