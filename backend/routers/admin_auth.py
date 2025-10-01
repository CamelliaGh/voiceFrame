"""
Admin Authentication Routes

Provides login/logout functionality for admin users with multiple authentication methods.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminUserResponse,
    AdminUserCreate,
    AdminUserUpdate,
)
from ..services.admin_auth import AdminAuthService

# Initialize admin auth service
admin_auth = AdminAuthService()

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with username and password to get JWT token
    """
    user = admin_auth.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )

    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = admin_auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes in seconds
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser
        }
    )


@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_user(
    current_user: AdminUser = admin_auth.get_jwt_dependency()
):
    """
    Get current admin user information
    """
    return AdminUserResponse.model_validate(current_user)


@router.post("/users", response_model=AdminUserResponse)
async def create_admin_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = admin_auth.get_jwt_dependency()
):
    """
    Create a new admin user (superuser only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create admin users"
        )

    # Check if username already exists
    existing_user = db.query(AdminUser).filter(AdminUser.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(AdminUser).filter(AdminUser.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Create new user
    hashed_password = admin_auth.get_password_hash(user_data.password)
    new_user = AdminUser(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_superuser=user_data.is_superuser
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AdminUserResponse.model_validate(new_user)


@router.get("/users", response_model=list[AdminUserResponse])
async def list_admin_users(
    db: Session = Depends(get_db),
    current_user: AdminUser = admin_auth.get_jwt_dependency()
):
    """
    List all admin users (superuser only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can list admin users"
        )

    users = db.query(AdminUser).all()
    return [AdminUserResponse.model_validate(user) for user in users]


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: str,
    user_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = admin_auth.get_jwt_dependency()
):
    """
    Update an admin user (superuser only, or users can update themselves)
    """
    target_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    if not current_user.is_superuser and current_user.id != target_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own account"
        )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)

    # Handle password update
    if "password" in update_data:
        update_data["hashed_password"] = admin_auth.get_password_hash(update_data.pop("password"))

    # Superuser restrictions
    if not current_user.is_superuser:
        # Non-superusers can't change superuser status
        update_data.pop("is_superuser", None)

    for field, value in update_data.items():
        setattr(target_user, field, value)

    db.commit()
    db.refresh(target_user)

    return AdminUserResponse.model_validate(target_user)


@router.delete("/users/{user_id}")
async def delete_admin_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = admin_auth.get_jwt_dependency()
):
    """
    Delete an admin user (superuser only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete admin users"
        )

    target_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deleting yourself
    if current_user.id == target_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    db.delete(target_user)
    db.commit()

    return {"message": "User deleted successfully"}
