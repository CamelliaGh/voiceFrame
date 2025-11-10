"""
File Access Validation Service

Validates that file access requests are authorized and secure.
Prevents unauthorized access to files from other users' sessions.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from ..config import settings
from ..models import SessionModel, Order
from ..services.session_manager import SessionManager


class FileAccessValidator:
    """Validates file access permissions for security"""

    def __init__(self):
        self.session_manager = SessionManager()

    def validate_session_file_access(self, db: Session, token: str, file_type: str) -> Optional[SessionModel]:
        """
        Validate that a session has access to its own files

        Args:
            db: Database session
            token: Session token
            file_type: Type of file being accessed (photo, audio, waveform)

        Returns:
            SessionModel if access is valid, None otherwise

        Raises:
            HTTPException: If access is denied
        """
        from fastapi import HTTPException

        # Validate session exists and is not expired
        session = self.session_manager.get_session(db, token)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired"
            )

        # Validate session owns the requested file type
        file_field_map = {
            "photo": session.photo_s3_key,
            "audio": session.audio_s3_key,
            "waveform": session.waveform_s3_key,
        }

        if file_type not in file_field_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file_type}"
            )

        if not file_field_map[file_type]:
            raise HTTPException(
                status_code=404,
                detail=f"{file_type.title()} file not found for this session"
            )

        return session

    def validate_order_file_access(self, db: Session, order_id: str, file_type: str) -> Optional[Order]:
        """
        Validate that an order has access to its files

        Args:
            db: Database session
            order_id: Order ID
            file_type: Type of file being accessed (audio, pdf, etc.)

        Returns:
            Order if access is valid, None otherwise

        Raises:
            HTTPException: If access is denied
        """
        from fastapi import HTTPException

        # Validate order exists and is completed
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.status == "completed"
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found or not completed"
            )

        # Validate order has the requested file type
        file_field_map = {
            "audio": order.permanent_audio_s3_key,
            "pdf": order.permanent_pdf_s3_key,
            "photo": order.permanent_photo_s3_key,
            "waveform": order.permanent_waveform_s3_key,
        }

        if file_type not in file_field_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file_type}"
            )

        if not file_field_map[file_type]:
            raise HTTPException(
                status_code=404,
                detail=f"{file_type.title()} file not found for this order"
            )

        return order

    def validate_download_token_access(self, db: Session, download_token: str) -> Optional[Order]:
        """
        Validate download token access

        Args:
            db: Database session
            download_token: Download token

        Returns:
            Order if access is valid, None otherwise

        Raises:
            HTTPException: If access is denied
        """
        from fastapi import HTTPException
        from datetime import datetime

        order = db.query(Order).filter(Order.download_token == download_token).first()
        if not order:
            raise HTTPException(
                status_code=404,
                detail="Download link not found"
            )

        if order.download_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=410,
                detail="Download link has expired"
            )

        if order.status != "completed":
            raise HTTPException(
                status_code=403,
                detail="Download not available - order not completed"
            )

        return order

    def validate_audio_playback_access(self, db: Session, identifier: str) -> dict:
        """
        Validate audio playback access for QR codes

        Args:
            db: Database session
            identifier: Either order ID or session token

        Returns:
            Dict with access info: {'type': 'order'|'session', 'object': Order|SessionModel, 'audio_key': str}

        Raises:
            HTTPException: If access is denied
        """
        from fastapi import HTTPException
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"🔍 validate_audio_playback_access called with identifier: {identifier}")

        # First try as order ID (paid posters) - only if identifier looks like a UUID
        import uuid
        order = None
        try:
            # Validate that identifier is a valid UUID before querying
            uuid.UUID(identifier)
            order = db.query(Order).filter(
                Order.id == identifier,
                Order.status == "completed"
            ).first()
            logger.info(f"🔍 Order lookup (UUID): {'Found' if order else 'Not found'}")
        except ValueError:
            # Not a valid UUID, skip order lookup
            logger.info(f"🔍 Not a valid UUID, skipping order lookup")
            pass

        if order and order.permanent_audio_s3_key:
            logger.info(f"✅ Found paid order with permanent audio")
            return {
                'type': 'order',
                'object': order,
                'audio_key': order.permanent_audio_s3_key,
                'title': 'Your AudioPoster Memory'
            }

        # Try as session token (preview posters)
        logger.info(f"🔍 Trying session_manager.get_session (checks expires_at > now)")
        session = self.session_manager.get_session(db, identifier)
        logger.info(f"🔍 session_manager.get_session result: {'Found' if session else 'Not found'}")
        if session:
            logger.info(f"🔍 Session audio_s3_key: {session.audio_s3_key}")
            logger.info(f"🔍 Session expires_at: {session.expires_at}")

        if session and session.audio_s3_key:
            logger.info(f"✅ Found active session with audio")
            return {
                'type': 'session',
                'object': session,
                'audio_key': session.audio_s3_key,
                'title': 'AudioPoster Preview'
            }

        # Fallback: allow recently expired sessions within preview window
        logger.info(f"🔍 Fallback: looking for ANY session with this token (ignoring expires_at)")
        session = db.query(SessionModel).filter(SessionModel.session_token == identifier).first()
        logger.info(f"🔍 Direct session lookup result: {'Found' if session else 'Not found'}")

        if session:
            logger.info(f"🔍 Session details:")
            logger.info(f"  - audio_s3_key: {session.audio_s3_key}")
            logger.info(f"  - created_at: {session.created_at}")
            logger.info(f"  - expires_at: {session.expires_at}")

        if session and session.audio_s3_key:
            now = datetime.utcnow()
            preview_expires_at = (session.created_at or now) + timedelta(
                seconds=settings.qr_code_preview_expiration
            )

            logger.info(f"🔍 Time check:")
            logger.info(f"  - now: {now}")
            logger.info(f"  - preview_expires_at: {preview_expires_at}")
            logger.info(f"  - within preview window: {now <= preview_expires_at}")

            if now > preview_expires_at:
                logger.error(f"❌ Session beyond preview window")
                raise HTTPException(
                    status_code=410,
                    detail="Preview session has expired"
                )

            if session.expires_at is None or session.expires_at < preview_expires_at:
                logger.info(f"🔧 Extending session expires_at to preview window")
                session_model = session.__class__
                db.query(session_model).filter(
                    session_model.session_token == identifier
                ).update(
                    {"expires_at": preview_expires_at},
                    synchronize_session=False
                )
                db.commit()
                session = db.query(session_model).filter(
                    session_model.session_token == identifier
                ).first()
                logger.info(f"✅ Extended session expires_at to: {session.expires_at}")

            logger.info(f"✅ Returning session within preview window")
            return {
                'type': 'session',
                'object': session,
                'audio_key': session.audio_s3_key,
                'title': 'AudioPoster Preview'
            }

        # No valid access found
        logger.error(f"❌ No valid session or order found for identifier: {identifier}")
        logger.error(f"   - Order check: {'passed' if order else 'failed'}")
        logger.error(f"   - Active session check: {'passed' if self.session_manager.get_session(db, identifier) else 'failed'}")
        logger.error(f"   - Any session check: {'passed' if db.query(SessionModel).filter(SessionModel.session_token == identifier).first() else 'failed'}")

        raise HTTPException(
            status_code=404,
            detail="Audio not found or access denied"
        )
