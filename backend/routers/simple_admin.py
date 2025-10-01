"""
Simple Admin Authentication Routes

Provides a simple password-based authentication for development/testing.
This is a lightweight alternative to the full JWT system.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.admin_auth import AdminAuthService
from ..config import settings

# Initialize admin auth service
admin_auth = AdminAuthService()

router = APIRouter(prefix="/admin/simple", tags=["admin-simple"])


@router.post("/login")
async def simple_admin_login(
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Simple password-based login for development
    """
    # Get admin password from settings
    admin_password = settings.admin_password

    if password != admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )

    return {
        "message": "Login successful",
        "access_method": "simple_password",
        "note": "Use this password in Authorization header as 'Bearer <password>'"
    }


@router.get("/test")
async def test_simple_auth(
    _: bool = admin_auth.get_simple_password_dependency()
):
    """
    Test endpoint for simple password authentication
    """
    return {
        "message": "Simple authentication successful!",
        "access_method": "simple_password"
    }
