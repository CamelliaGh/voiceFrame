"""
Admin Authentication Service

Provides authentication for admin endpoints using API keys.
Protects sensitive administrative operations from unauthorized access.
"""

import os
from typing import Optional
from fastapi import HTTPException, Request


class AdminAuthService:
    """Handles admin authentication for protected endpoints"""

    _instance = None
    _api_key = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdminAuthService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._api_key is None:
            # Get admin API key from environment
            self._api_key = os.getenv("ADMIN_API_KEY")
            if not self._api_key:
                # Generate a default key for development (should be set in production)
                import secrets
                self._api_key = secrets.token_urlsafe(32)
                print(f"⚠️  WARNING: Using auto-generated admin API key: {self._api_key}")
                print("   Set ADMIN_API_KEY environment variable in production!")

        self.admin_api_key = self._api_key

    def validate_admin_access(self, request: Request) -> bool:
        """
        Validate admin access using API key

        Args:
            request: FastAPI request object

        Returns:
            True if access is authorized

        Raises:
            HTTPException: If access is denied
        """
        # Check for API key in Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Admin access requires API key in Authorization header"
            )

        # Extract API key from "Bearer <key>" format
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization format. Use 'Bearer <api_key>'"
            )

        api_key = auth_header[7:]  # Remove "Bearer " prefix

        if api_key != self.admin_api_key:
            raise HTTPException(
                status_code=403,
                detail="Invalid admin API key"
            )

        return True

    def get_admin_dependency(self):
        """
        Get a FastAPI dependency for admin authentication

        Returns:
            FastAPI dependency function
        """
        from fastapi import Depends

        def admin_auth_dependency(request: Request):
            self.validate_admin_access(request)
            return True

        return Depends(admin_auth_dependency)
