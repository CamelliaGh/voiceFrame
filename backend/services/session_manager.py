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
        for key, value in data.items():
            if hasattr(session, key):
                setattr(session, key, value)

        db.commit()
        db.refresh(session)
        return session

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
