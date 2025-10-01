"""
Admin Authentication Service

Provides multiple authentication methods for admin endpoints:
1. Username/Password with JWT tokens (recommended)
2. API key authentication (fallback)
3. Simple password authentication (development only)
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import AdminUser

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer()


class AdminAuthService:
    """Handles admin authentication with multiple methods"""

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
                self._api_key = secrets.token_urlsafe(32)
                print(f"⚠️  WARNING: Using auto-generated admin API key: {self._api_key}")
                print("   Set ADMIN_API_KEY environment variable in production!")

        self.admin_api_key = self._api_key

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate a user with username and password"""
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def get_user_by_token(self, db: Session, token: str) -> Optional[AdminUser]:
        """Get user from JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
        except JWTError:
            return None

        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        return user

    def validate_admin_access(self, request: Request) -> bool:
        """
        Validate admin access using API key (legacy method)
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

    def validate_jwt_access(self, credentials: HTTPAuthorizationCredentials, db: Session = Depends(get_db)) -> AdminUser:
        """
        Validate admin access using JWT token
        """
        token = credentials.credentials
        user = self.get_user_by_token(db, token)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        return user

    def get_admin_dependency(self):
        """
        Get a FastAPI dependency for admin authentication (API key method)
        """
        def admin_auth_dependency(request: Request):
            self.validate_admin_access(request)
            return True

        return Depends(admin_auth_dependency)

    def get_jwt_dependency(self):
        """
        Get a FastAPI dependency for JWT-based admin authentication
        """
        def jwt_auth_dependency(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> AdminUser:
            return self.validate_jwt_access(credentials, db)

        return Depends(jwt_auth_dependency)

    def get_simple_password_dependency(self):
        """
        Get a FastAPI dependency for simple password authentication (development only)
        """
        def simple_auth_dependency(request: Request):
            # Check for simple password in Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401,
                    detail="Admin access requires password in Authorization header"
                )

            # Extract password from "Bearer <password>" format
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authorization format. Use 'Bearer <password>'"
                )

            password = auth_header[7:]  # Remove "Bearer " prefix

            # Simple password check (development only)
            admin_password = settings.admin_password
            if password != admin_password:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid admin password"
                )

            return True

        return Depends(simple_auth_dependency)
