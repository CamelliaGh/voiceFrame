"""
Consent Management Service for GDPR Compliance

Handles user consent collection, tracking, and management for GDPR compliance.
Provides comprehensive consent audit trails and withdrawal mechanisms.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models import SessionModel, Order, EmailSubscriber
from ..config import settings

logger = logging.getLogger(__name__)


class ConsentType(Enum):
    """Types of consent that can be collected"""
    DATA_PROCESSING = "data_processing"
    EMAIL_MARKETING = "email_marketing"
    ANALYTICS = "analytics"
    COOKIES = "cookies"
    FILE_STORAGE = "file_storage"
    THIRD_PARTY_SHARING = "third_party_sharing"


class ConsentStatus(Enum):
    """Status of consent"""
    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class ConsentManager:
    """Manages user consent for GDPR compliance"""

    def __init__(self):
        self.consent_retention_days = 7 * 365  # 7 years as required by GDPR
        self.consent_audit_retention_days = 7 * 365  # 7 years for audit trail

    def _get_consent_key(self, user_identifier: str, consent_type: ConsentType) -> str:
        """Generate a unique key for consent storage"""
        return f"consent:{user_identifier}:{consent_type.value}"

    def _get_audit_key(self, user_identifier: str, consent_type: ConsentType) -> str:
        """Generate a unique key for consent audit trail"""
        return f"consent_audit:{user_identifier}:{consent_type.value}"

    def collect_consent(
        self,
        user_identifier: str,
        consent_type: ConsentType,
        consent_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Collect and record user consent

        Args:
            user_identifier: Unique identifier for the user (email, session_token, etc.)
            consent_type: Type of consent being collected
            consent_data: Additional consent information
            db: Database session

        Returns:
            Dict containing consent record and status
        """
        try:
            consent_record = {
                "user_identifier": user_identifier,
                "consent_type": consent_type.value,
                "status": ConsentStatus.GIVEN.value,
                "given_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=self.consent_retention_days)).isoformat(),
                "consent_data": consent_data,
                "ip_address": consent_data.get("ip_address"),
                "user_agent": consent_data.get("user_agent"),
                "consent_version": consent_data.get("consent_version", "1.0"),
                "legal_basis": consent_data.get("legal_basis", "consent"),
                "purpose": consent_data.get("purpose", ""),
                "data_categories": consent_data.get("data_categories", []),
                "retention_period": consent_data.get("retention_period", "7 years"),
                "third_parties": consent_data.get("third_parties", []),
                "withdrawal_method": consent_data.get("withdrawal_method", "email"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store consent in session data (in production, use dedicated consent table)
            session = db.query(SessionModel).filter(
                SessionModel.session_token == user_identifier
            ).first()

            if session:
                # Store consent data in session
                if not hasattr(session, 'consent_data') or session.consent_data is None:
                    session.consent_data = json.dumps({})

                consent_storage = json.loads(session.consent_data)
                consent_storage[consent_type.value] = consent_record
                session.consent_data = json.dumps(consent_storage)
                session.consent_updated_at = datetime.utcnow()

                db.commit()

            # Log consent collection for audit trail
            self._log_consent_action(
                user_identifier,
                consent_type,
                "consent_given",
                consent_record,
                db
            )

            logger.info(f"Consent collected for {user_identifier}: {consent_type.value}")

            return {
                "success": True,
                "consent_id": f"{user_identifier}_{consent_type.value}_{int(datetime.utcnow().timestamp())}",
                "consent_record": consent_record,
                "message": "Consent successfully recorded"
            }

        except Exception as e:
            logger.error(f"Error collecting consent: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to record consent"
            }

    def withdraw_consent(
        self,
        user_identifier: str,
        consent_type: ConsentType,
        withdrawal_reason: str = "",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Withdraw user consent

        Args:
            user_identifier: Unique identifier for the user
            consent_type: Type of consent to withdraw
            withdrawal_reason: Reason for withdrawal
            db: Database session

        Returns:
            Dict containing withdrawal status
        """
        try:
            if db is None:
                db = next(get_db())

            # Find and update consent record
            session = db.query(SessionModel).filter(
                SessionModel.session_token == user_identifier
            ).first()

            if not session or not session.consent_data:
                return {
                    "success": False,
                    "error": "No consent found for user",
                    "message": "No consent record found to withdraw"
                }

            consent_storage = json.loads(session.consent_data)

            if consent_type.value not in consent_storage:
                return {
                    "success": False,
                    "error": "Consent type not found",
                    "message": f"No {consent_type.value} consent found to withdraw"
                }

            consent_record = consent_storage[consent_type.value]

            # Update consent status
            consent_record["status"] = ConsentStatus.WITHDRAWN.value
            consent_record["withdrawn_at"] = datetime.utcnow().isoformat()
            consent_record["withdrawal_reason"] = withdrawal_reason
            consent_record["updated_at"] = datetime.utcnow().isoformat()

            # Store updated consent
            consent_storage[consent_type.value] = consent_record
            session.consent_data = json.dumps(consent_storage)
            session.consent_updated_at = datetime.utcnow()

            db.commit()

            # Log consent withdrawal for audit trail
            self._log_consent_action(
                user_identifier,
                consent_type,
                "consent_withdrawn",
                {
                    "withdrawal_reason": withdrawal_reason,
                    "withdrawn_at": datetime.utcnow().isoformat()
                },
                db
            )

            logger.info(f"Consent withdrawn for {user_identifier}: {consent_type.value}")

            return {
                "success": True,
                "consent_record": consent_record,
                "message": "Consent successfully withdrawn"
            }

        except Exception as e:
            logger.error(f"Error withdrawing consent: {str(e)}")
            if db:
                db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to withdraw consent"
            }

    def get_consent_status(
        self,
        user_identifier: str,
        consent_type: ConsentType,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get current consent status for a user

        Args:
            user_identifier: Unique identifier for the user
            consent_type: Type of consent to check
            db: Database session

        Returns:
            Dict containing consent status and details
        """
        try:
            session = db.query(SessionModel).filter(
                SessionModel.session_token == user_identifier
            ).first()

            if not session or not session.consent_data:
                return {
                    "has_consent": False,
                    "status": ConsentStatus.PENDING.value,
                    "message": "No consent record found"
                }

            consent_storage = json.loads(session.consent_data)

            if consent_type.value not in consent_storage:
                return {
                    "has_consent": False,
                    "status": ConsentStatus.PENDING.value,
                    "message": f"No {consent_type.value} consent found"
                }

            consent_record = consent_storage[consent_type.value]

            # Check if consent has expired
            expires_at = datetime.fromisoformat(consent_record["expires_at"])
            if datetime.utcnow() > expires_at:
                consent_record["status"] = ConsentStatus.EXPIRED.value
                consent_record["updated_at"] = datetime.utcnow().isoformat()

                # Update stored consent
                consent_storage[consent_type.value] = consent_record
                session.consent_data = json.dumps(consent_storage)
                db.commit()

            return {
                "has_consent": consent_record["status"] == ConsentStatus.GIVEN.value,
                "status": consent_record["status"],
                "consent_record": consent_record,
                "message": f"Consent status: {consent_record['status']}"
            }

        except Exception as e:
            logger.error(f"Error getting consent status: {str(e)}")
            return {
                "has_consent": False,
                "status": ConsentStatus.PENDING.value,
                "error": str(e),
                "message": "Error retrieving consent status"
            }

    def get_all_consents(self, user_identifier: str, db: Session) -> Dict[str, Any]:
        """
        Get all consent records for a user

        Args:
            user_identifier: Unique identifier for the user
            db: Database session

        Returns:
            Dict containing all consent records
        """
        try:
            session = db.query(SessionModel).filter(
                SessionModel.session_token == user_identifier
            ).first()

            if not session or not session.consent_data:
                return {
                    "consents": {},
                    "message": "No consent records found"
                }

            consent_storage = json.loads(session.consent_data)

            return {
                "consents": consent_storage,
                "total_consents": len(consent_storage),
                "message": f"Found {len(consent_storage)} consent records"
            }

        except Exception as e:
            logger.error(f"Error getting all consents: {str(e)}")
            return {
                "consents": {},
                "error": str(e),
                "message": "Error retrieving consent records"
            }

    def _log_consent_action(
        self,
        user_identifier: str,
        consent_type: ConsentType,
        action: str,
        action_data: Dict[str, Any],
        db: Session
    ):
        """Log consent actions for audit trail"""
        try:
            audit_record = {
                "user_identifier": user_identifier,
                "consent_type": consent_type.value,
                "action": action,
                "action_data": action_data,
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": action_data.get("ip_address"),
                "user_agent": action_data.get("user_agent")
            }

            # In production, store in dedicated audit table
            # For now, we'll log to application logs
            logger.info(f"Consent audit: {json.dumps(audit_record)}")

        except Exception as e:
            logger.error(f"Error logging consent action: {str(e)}")

    def cleanup_expired_consents(self, db: Session) -> int:
        """
        Clean up expired consent records

        Args:
            db: Database session

        Returns:
            Number of expired consents cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.consent_retention_days)
            cleaned_count = 0

            # Find sessions with expired consents
            sessions = db.query(SessionModel).filter(
                SessionModel.consent_data.isnot(None)
            ).all()

            for session in sessions:
                if not session.consent_data:
                    continue

                consent_storage = json.loads(session.consent_data)
                updated = False

                for consent_type, consent_record in consent_storage.items():
                    expires_at = datetime.fromisoformat(consent_record["expires_at"])

                    if datetime.utcnow() > expires_at:
                        consent_record["status"] = ConsentStatus.EXPIRED.value
                        consent_record["updated_at"] = datetime.utcnow().isoformat()
                        updated = True
                        cleaned_count += 1

                if updated:
                    session.consent_data = json.dumps(consent_storage)
                    session.consent_updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"Cleaned up {cleaned_count} expired consent records")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up expired consents: {str(e)}")
            db.rollback()
            return 0

    def get_consent_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get consent statistics for monitoring

        Args:
            db: Database session

        Returns:
            Dict containing consent statistics
        """
        try:
            total_sessions = db.query(SessionModel).count()
            sessions_with_consent = db.query(SessionModel).filter(
                SessionModel.consent_data.isnot(None)
            ).count()

            consent_types = {}
            consent_statuses = {}

            sessions = db.query(SessionModel).filter(
                SessionModel.consent_data.isnot(None)
            ).all()

            for session in sessions:
                if not session.consent_data:
                    continue

                consent_storage = json.loads(session.consent_data)

                for consent_type, consent_record in consent_storage.items():
                    # Count by type
                    consent_types[consent_type] = consent_types.get(consent_type, 0) + 1

                    # Count by status
                    status = consent_record.get("status", "unknown")
                    consent_statuses[status] = consent_statuses.get(status, 0) + 1

            return {
                "total_sessions": total_sessions,
                "sessions_with_consent": sessions_with_consent,
                "consent_coverage": (sessions_with_consent / total_sessions * 100) if total_sessions > 0 else 0,
                "consent_types": consent_types,
                "consent_statuses": consent_statuses,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting consent statistics: {str(e)}")
            return {
                "error": str(e),
                "message": "Error retrieving consent statistics"
            }


# Global consent manager instance
consent_manager = ConsentManager()
