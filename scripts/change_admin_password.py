#!/usr/bin/env python3
"""
Script to change the admin password in the .env file
"""

import os
import sys
from pathlib import Path

def change_admin_password(new_password):
    """Change the admin password in the .env file"""

    # Get the project root directory
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if not env_file.exists():
        print("❌ .env file not found!")
        return False

    # Read the current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()

    # Update the ADMIN_PASSWORD line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('ADMIN_PASSWORD='):
            lines[i] = f'ADMIN_PASSWORD={new_password}\n'
            updated = True
            break

    if not updated:
        # If ADMIN_PASSWORD doesn't exist, add it
        lines.append(f'ADMIN_PASSWORD={new_password}\n')

    # Write the updated .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)

    print(f"✅ Admin password updated to: {new_password}")
    print("🔄 Please restart the API container to apply changes:")
    print("   docker-compose restart api")

    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/change_admin_password.py <new_password>")
        print("Example: python3 scripts/change_admin_password.py mynewpassword123")
        sys.exit(1)

    new_password = sys.argv[1]

    if len(new_password) < 6:
        print("❌ Password should be at least 6 characters long")
        sys.exit(1)

    change_admin_password(new_password)
