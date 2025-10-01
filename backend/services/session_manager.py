import secrets
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..models import SessionModel

class SessionManager:
    """Manages user sessions for file uploads and customization"""

    def create_session(self, db: Session, expires_hours: int = 2) -> SessionModel:
        """Create a new session with cryptographically secure token"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        session = SessionModel(session_token=session_token, expires_at=expires_at)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(self, db: Session, token: str) -> Optional[SessionModel]:
        """Get session by token if not expired"""
        session = db.query(SessionModel).filter(
            SessionModel.session_token == token,
            SessionModel.expires_at > datetime.utcnow()
        ).first()
        return session

    def get_session_by_order(self, db: Session, order_id: str) -> Optional[SessionModel]:
        """Get session associated with an order (for PDF generation)"""
        from ..models import Order

        # Get the order first
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.session_token:
            return None

        # Get the session using the session_token from the order
        return self.get_session(db, order.session_token)

    def update_session(self, db: Session, session: SessionModel, data: Dict[str, Any]) -> SessionModel:
        """Update session with new data"""
        # Validate background_id and font_id against admin resources
        if 'background_id' in data and data['background_id'] is not None:
            self._validate_background_id(db, data['background_id'])

        if 'font_id' in data and data['font_id'] is not None:
            self._validate_font_id(db, data['font_id'])

        for key, value in data.items():
            if hasattr(session, key):
                setattr(session, key, value)

        db.commit()
        db.refresh(session)
        return session

    def _validate_background_id(self, db: Session, background_id: str):
        """Validate that background_id exists in admin resources or is a default"""
        from .admin_resource_service import admin_resource_service

        # Check if it's a default background
        default_backgrounds = [
            "none",
            "abstract-blurred",
            "roses-wooden",
            "cute-hearts",
            "flat-lay-hearts",
        ]

        if background_id in default_backgrounds:
            return

        # Check if it exists in admin-managed backgrounds
        background = admin_resource_service.get_background_by_name(db, background_id)
        if not background:
            raise ValueError(f"Invalid background ID: {background_id}")

    def _validate_font_id(self, db: Session, font_id: str):
        """Validate that font_id exists in admin resources or is a default"""
        from .admin_resource_service import admin_resource_service

        # Check if it's a default font
        default_fonts = ["script", "elegant", "modern", "vintage", "classic"]

        if font_id in default_fonts:
            return

        # Check if it exists in admin-managed fonts
        font = admin_resource_service.get_font_by_name(db, font_id)
        if not font:
            raise ValueError(f"Invalid font ID: {font_id}")

    def cleanup_expired_sessions(self, db: Session) -> int:
        """Remove expired sessions and their associated files"""
        expired_sessions = db.query(SessionModel).filter(
            SessionModel.expires_at <= datetime.utcnow()
        ).all()

        count = len(expired_sessions)

        # TODO: Delete associated S3 files before deleting sessions
        for session in expired_sessions:
            db.delete(session)

        db.commit()
        return count
