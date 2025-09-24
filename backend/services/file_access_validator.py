"""
File Access Validation Service

Validates that file access requests are authorized and secure.
Prevents unauthorized access to files from other users' sessions.
"""

from typing import Optional
from sqlalchemy.orm import Session
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

        # First try as order ID (paid posters)
        order = db.query(Order).filter(
            Order.id == identifier,
            Order.status == "completed"
        ).first()

        if order and order.permanent_audio_s3_key:
            return {
                'type': 'order',
                'object': order,
                'audio_key': order.permanent_audio_s3_key,
                'title': 'Your AudioPoster Memory'
            }

        # Try as session token (preview posters)
        session = self.session_manager.get_session(db, identifier)
        if session and session.audio_s3_key:
            # Additional validation: ensure session is not expired
            from datetime import datetime
            if session.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=410,
                    detail="Preview session has expired"
                )

            return {
                'type': 'session',
                'object': session,
                'audio_key': session.audio_s3_key,
                'title': 'AudioPoster Preview'
            }

        # No valid access found
        raise HTTPException(
            status_code=404,
            detail="Audio not found or access denied"
        )
