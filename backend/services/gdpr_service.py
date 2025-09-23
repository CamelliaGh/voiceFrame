"""
GDPR Data Subject Rights Service

Implements GDPR data subject rights including:
- Right to Access (data portability)
- Right to Erasure (right to be forgotten)
- Right to Rectification (data correction)
- Right to Data Portability (export user data)
"""

import json
import logging
import zipfile
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models import SessionModel, Order, EmailSubscriber
from ..config import settings
from .consent_manager import consent_manager, ConsentType

logger = logging.getLogger(__name__)


class GDPRService:
    """Handles GDPR data subject rights requests"""

    def __init__(self):
        self.data_retention_days = settings.data_retention_days
        self.export_format = "json"  # Could be extended to support other formats

    def get_user_data(self, user_identifier: str, db: Session) -> Dict[str, Any]:
        """
        Right to Access - Get all personal data for a user

        Args:
            user_identifier: User identifier (email, session_token, etc.)
            db: Database session

        Returns:
            Dict containing all user data
        """
        try:
            user_data = {
                "user_identifier": user_identifier,
                "data_categories": {},
                "export_timestamp": datetime.utcnow().isoformat(),
                "data_controller": settings.company_name,
                "legal_basis": "consent",
                "retention_period": f"{self.data_retention_days} days"
            }

            # Get session data
            sessions = db.query(SessionModel).filter(
                or_(
                    SessionModel.session_token == user_identifier,
                    SessionModel.email == user_identifier
                )
            ).all()

            if sessions:
                user_data["data_categories"]["sessions"] = []
                for session in sessions:
                    session_data = {
                        "session_id": str(session.id),
                        "session_token": session.session_token,
                        "email": session.email,
                        "photo_s3_key": session.photo_s3_key,
                        "audio_s3_key": session.audio_s3_key,
                        "waveform_s3_key": session.waveform_s3_key,
                        "custom_text": session.custom_text,
                        "photo_shape": session.photo_shape,
                        "pdf_size": session.pdf_size,
                        "template_id": session.template_id,
                        "background_id": session.background_id,
                        "font_id": session.font_id,
                        "audio_duration": session.audio_duration,
                        "created_at": session.created_at.isoformat() if session.created_at else None,
                        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                        "unsubscribed": session.unsubscribed,
                        "unsubscribed_at": session.unsubscribed_at.isoformat() if session.unsubscribed_at else None,
                        "data_processing_consent": session.data_processing_consent,
                        "marketing_consent": session.marketing_consent,
                        "analytics_consent": session.analytics_consent,
                        "cookie_consent": session.cookie_consent,
                        "consent_updated_at": session.consent_updated_at.isoformat() if session.consent_updated_at else None
                    }

                    # Include consent data if available
                    if session.consent_data:
                        try:
                            session_data["consent_data"] = json.loads(session.consent_data)
                        except json.JSONDecodeError:
                            session_data["consent_data"] = session.consent_data

                    user_data["data_categories"]["sessions"].append(session_data)

            # Get order data
            orders = db.query(Order).filter(
                or_(
                    Order.email == user_identifier,
                    Order.session_token == user_identifier
                )
            ).all()

            if orders:
                user_data["data_categories"]["orders"] = []
                for order in orders:
                    order_data = {
                        "order_id": str(order.id),
                        "email": order.email,
                        "amount_cents": order.amount_cents,
                        "stripe_payment_intent_id": order.stripe_payment_intent_id,
                        "status": order.status,
                        "download_token": order.download_token,
                        "download_expires_at": order.download_expires_at.isoformat() if order.download_expires_at else None,
                        "pdf_s3_key": order.pdf_s3_key,
                        "permanent_photo_s3_key": order.permanent_photo_s3_key,
                        "permanent_audio_s3_key": order.permanent_audio_s3_key,
                        "permanent_waveform_s3_key": order.permanent_waveform_s3_key,
                        "permanent_pdf_s3_key": order.permanent_pdf_s3_key,
                        "migration_status": order.migration_status,
                        "migration_completed_at": order.migration_completed_at.isoformat() if order.migration_completed_at else None,
                        "migration_error": order.migration_error,
                        "session_token": order.session_token,
                        "audio_secure_hash": order.audio_secure_hash,
                        "created_at": order.created_at.isoformat() if order.created_at else None,
                        "updated_at": order.updated_at.isoformat() if order.updated_at else None
                    }
                    user_data["data_categories"]["orders"].append(order_data)

            # Get email subscriber data
            email_subscribers = db.query(EmailSubscriber).filter(
                EmailSubscriber.email == user_identifier
            ).all()

            if email_subscribers:
                user_data["data_categories"]["email_subscribers"] = []
                for subscriber in email_subscribers:
                    subscriber_data = {
                        "subscriber_id": str(subscriber.id),
                        "email": subscriber.email,
                        "subscribed": subscriber.subscribed,
                        "source": subscriber.source,
                        "first_purchase_date": subscriber.first_purchase_date.isoformat() if subscriber.first_purchase_date else None,
                        "total_purchases": subscriber.total_purchases,
                        "total_spent_cents": subscriber.total_spent_cents,
                        "last_campaign_sent_at": subscriber.last_campaign_sent_at.isoformat() if subscriber.last_campaign_sent_at else None,
                        "created_at": subscriber.created_at.isoformat() if subscriber.created_at else None
                    }
                    user_data["data_categories"]["email_subscribers"].append(subscriber_data)

            # Get consent data
            consent_data = consent_manager.get_all_consents(user_identifier, db)
            if consent_data.get("consents"):
                user_data["data_categories"]["consent_records"] = consent_data["consents"]

            # Add data processing information
            user_data["data_processing_info"] = {
                "purposes": [
                    "Service delivery and functionality",
                    "Payment processing",
                    "Email communications",
                    "Analytics and improvement",
                    "Legal compliance"
                ],
                "data_categories": [
                    "Identity data (email, session tokens)",
                    "Contact data (email addresses)",
                    "Financial data (payment information)",
                    "Technical data (IP addresses, user agents)",
                    "Usage data (file uploads, preferences)",
                    "Marketing data (communication preferences)"
                ],
                "third_parties": [
                    "Stripe (payment processing)",
                    "AWS S3 (file storage)",
                    "SendGrid (email delivery)"
                ],
                "retention_periods": {
                    "session_data": f"{self.data_retention_days} days",
                    "order_data": "7 years (legal requirement)",
                    "consent_records": "7 years (legal requirement)",
                    "email_subscriber_data": "Until unsubscribed + 30 days"
                }
            }

            logger.info(f"Data access request completed for {user_identifier}")
            return user_data

        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return {
                "error": str(e),
                "message": "Error retrieving user data"
            }

    def export_user_data(self, user_identifier: str, db: Session) -> Dict[str, Any]:
        """
        Right to Data Portability - Export user data in portable format

        Args:
            user_identifier: User identifier
            db: Database session

        Returns:
            Dict containing export data and metadata
        """
        try:
            user_data = self.get_user_data(user_identifier, db)

            if "error" in user_data:
                return user_data

            # Create export package
            export_package = {
                "export_metadata": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "data_controller": settings.company_name,
                    "data_subject": user_identifier,
                    "format_version": "1.0",
                    "gdpr_article": "Article 20 - Right to data portability",
                    "legal_basis": "consent",
                    "retention_period": f"{self.data_retention_days} days"
                },
                "personal_data": user_data,
                "data_categories_summary": {
                    "sessions": len(user_data.get("data_categories", {}).get("sessions", [])),
                    "orders": len(user_data.get("data_categories", {}).get("orders", [])),
                    "email_subscribers": len(user_data.get("data_categories", {}).get("email_subscribers", [])),
                    "consent_records": len(user_data.get("data_categories", {}).get("consent_records", {}))
                }
            }

            # Create JSON export
            json_export = json.dumps(export_package, indent=2, default=str)

            # Create ZIP file for larger exports
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f"gdpr_export_{user_identifier}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json", json_export)

                # Add individual data category files
                for category, data in user_data.get("data_categories", {}).items():
                    if data:
                        zip_file.writestr(f"{category}.json", json.dumps(data, indent=2, default=str))

                # Add metadata file
                zip_file.writestr("export_metadata.json", json.dumps(export_package["export_metadata"], indent=2))

            zip_buffer.seek(0)

            return {
                "success": True,
                "export_data": export_package,
                "json_export": json_export,
                "zip_export": zip_buffer.getvalue(),
                "export_size_bytes": len(json_export),
                "zip_size_bytes": len(zip_buffer.getvalue()),
                "message": "Data export completed successfully"
            }

        except Exception as e:
            logger.error(f"Error exporting user data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error exporting user data"
            }

    def erase_user_data(self, user_identifier: str, db: Session) -> Dict[str, Any]:
        """
        Right to Erasure - Delete all personal data for a user

        Args:
            user_identifier: User identifier
            db: Database session

        Returns:
            Dict containing erasure status and details
        """
        try:
            erasure_log = {
                "user_identifier": user_identifier,
                "erasure_timestamp": datetime.utcnow().isoformat(),
                "erased_categories": [],
                "retained_data": [],
                "legal_basis_for_retention": []
            }

            deleted_count = 0

            # Delete session data
            sessions = db.query(SessionModel).filter(
                or_(
                    SessionModel.session_token == user_identifier,
                    SessionModel.email == user_identifier
                )
            ).all()

            for session in sessions:
                # Check if we need to retain any data for legal reasons
                orders = db.query(Order).filter(Order.session_token == session.session_token).all()

                if orders:
                    # Retain session token for order reference (legal requirement)
                    erasure_log["retained_data"].append({
                        "category": "session_token",
                        "reason": "Required for order reference and legal compliance",
                        "retention_period": "7 years"
                    })
                else:
                    # Safe to delete session
                    db.delete(session)
                    deleted_count += 1
                    erasure_log["erased_categories"].append("session_data")

            # Delete order data (but check legal requirements)
            orders = db.query(Order).filter(
                or_(
                    Order.email == user_identifier,
                    Order.session_token == user_identifier
                )
            ).all()

            for order in orders:
                # Check if order is recent (within legal retention period)
                if order.created_at and (datetime.utcnow() - order.created_at).days < 2555:  # 7 years
                    erasure_log["retained_data"].append({
                        "category": "order_data",
                        "reason": "Legal requirement for financial records",
                        "retention_period": "7 years",
                        "order_id": str(order.id)
                    })
                    erasure_log["legal_basis_for_retention"].append("Legal obligation for financial record keeping")
                else:
                    # Safe to delete old orders
                    db.delete(order)
                    deleted_count += 1
                    erasure_log["erased_categories"].append("order_data")

            # Delete email subscriber data
            email_subscribers = db.query(EmailSubscriber).filter(
                EmailSubscriber.email == user_identifier
            ).all()

            for subscriber in email_subscribers:
                db.delete(subscriber)
                deleted_count += 1
                erasure_log["erased_categories"].append("email_subscriber_data")

            # Withdraw all consents
            consent_types = [ConsentType.DATA_PROCESSING, ConsentType.EMAIL_MARKETING,
                           ConsentType.ANALYTICS, ConsentType.COOKIES, ConsentType.FILE_STORAGE]

            for consent_type in consent_types:
                withdrawal_result = consent_manager.withdraw_consent(
                    user_identifier,
                    consent_type,
                    "Data erasure request",
                    db
                )
                if withdrawal_result.get("success"):
                    erasure_log["erased_categories"].append(f"consent_{consent_type.value}")

            db.commit()

            logger.info(f"Data erasure completed for {user_identifier}: {deleted_count} records deleted")

            return {
                "success": True,
                "erasure_log": erasure_log,
                "deleted_records": deleted_count,
                "message": "Data erasure completed successfully"
            }

        except Exception as e:
            logger.error(f"Error erasing user data: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Error erasing user data"
            }

    def rectify_user_data(self, user_identifier: str, corrections: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Right to Rectification - Correct inaccurate personal data

        Args:
            user_identifier: User identifier
            corrections: Dict of field corrections
            db: Database session

        Returns:
            Dict containing rectification status
        """
        try:
            rectification_log = {
                "user_identifier": user_identifier,
                "rectification_timestamp": datetime.utcnow().isoformat(),
                "corrections_applied": [],
                "corrections_failed": []
            }

            # Apply corrections to sessions
            sessions = db.query(SessionModel).filter(
                or_(
                    SessionModel.session_token == user_identifier,
                    SessionModel.email == user_identifier
                )
            ).all()

            for session in sessions:
                for field, new_value in corrections.items():
                    if hasattr(session, field):
                        old_value = getattr(session, field)
                        setattr(session, field, new_value)
                        rectification_log["corrections_applied"].append({
                            "field": field,
                            "old_value": str(old_value),
                            "new_value": str(new_value),
                            "table": "sessions",
                            "record_id": str(session.id)
                        })
                    else:
                        rectification_log["corrections_failed"].append({
                            "field": field,
                            "reason": "Field not found in sessions table",
                            "table": "sessions"
                        })

            # Apply corrections to orders
            orders = db.query(Order).filter(
                or_(
                    Order.email == user_identifier,
                    Order.session_token == user_identifier
                )
            ).all()

            for order in orders:
                for field, new_value in corrections.items():
                    if hasattr(order, field):
                        old_value = getattr(order, field)
                        setattr(order, field, new_value)
                        rectification_log["corrections_applied"].append({
                            "field": field,
                            "old_value": str(old_value),
                            "new_value": str(new_value),
                            "table": "orders",
                            "record_id": str(order.id)
                        })
                    else:
                        rectification_log["corrections_failed"].append({
                            "field": field,
                            "reason": "Field not found in orders table",
                            "table": "orders"
                        })

            # Apply corrections to email subscribers
            email_subscribers = db.query(EmailSubscriber).filter(
                EmailSubscriber.email == user_identifier
            ).all()

            for subscriber in email_subscribers:
                for field, new_value in corrections.items():
                    if hasattr(subscriber, field):
                        old_value = getattr(subscriber, field)
                        setattr(subscriber, field, new_value)
                        rectification_log["corrections_applied"].append({
                            "field": field,
                            "old_value": str(old_value),
                            "new_value": str(new_value),
                            "table": "email_subscribers",
                            "record_id": str(subscriber.id)
                        })
                    else:
                        rectification_log["corrections_failed"].append({
                            "field": field,
                            "reason": "Field not found in email_subscribers table",
                            "table": "email_subscribers"
                        })

            db.commit()

            logger.info(f"Data rectification completed for {user_identifier}")

            return {
                "success": True,
                "rectification_log": rectification_log,
                "corrections_applied": len(rectification_log["corrections_applied"]),
                "corrections_failed": len(rectification_log["corrections_failed"]),
                "message": "Data rectification completed successfully"
            }

        except Exception as e:
            logger.error(f"Error rectifying user data: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Error rectifying user data"
            }

    def get_data_processing_info(self) -> Dict[str, Any]:
        """
        Get information about data processing activities

        Returns:
            Dict containing data processing information
        """
        return {
            "data_controller": settings.company_name,
            "data_controller_address": settings.company_address,
            "data_protection_officer": "privacy@audioposter.com",
            "legal_basis": {
                "data_processing": "consent",
                "email_marketing": "consent",
                "analytics": "legitimate_interest",
                "payment_processing": "contract",
                "legal_compliance": "legal_obligation"
            },
            "data_categories": [
                "Identity data (email, session tokens)",
                "Contact data (email addresses)",
                "Financial data (payment information)",
                "Technical data (IP addresses, user agents)",
                "Usage data (file uploads, preferences)",
                "Marketing data (communication preferences)"
            ],
            "purposes": [
                "Service delivery and functionality",
                "Payment processing",
                "Email communications",
                "Analytics and improvement",
                "Legal compliance"
            ],
            "retention_periods": {
                "session_data": f"{self.data_retention_days} days",
                "order_data": "7 years (legal requirement)",
                "consent_records": "7 years (legal requirement)",
                "email_subscriber_data": "Until unsubscribed + 30 days"
            },
            "third_parties": [
                {
                    "name": "Stripe",
                    "purpose": "Payment processing",
                    "data_shared": ["payment information", "order details"],
                    "legal_basis": "contract"
                },
                {
                    "name": "AWS S3",
                    "purpose": "File storage",
                    "data_shared": ["uploaded files", "generated content"],
                    "legal_basis": "contract"
                },
                {
                    "name": "SendGrid",
                    "purpose": "Email delivery",
                    "data_shared": ["email addresses", "email content"],
                    "legal_basis": "contract"
                }
            ],
            "data_subject_rights": [
                "Right to access (Article 15)",
                "Right to rectification (Article 16)",
                "Right to erasure (Article 17)",
                "Right to restrict processing (Article 18)",
                "Right to data portability (Article 20)",
                "Right to object (Article 21)"
            ],
            "contact_information": {
                "privacy_email": "privacy@audioposter.com",
                "dpo_email": "dpo@audioposter.com",
                "privacy_policy": settings.privacy_policy_url,
                "unsubscribe_url": settings.unsubscribe_url
            }
        }


# Global GDPR service instance
gdpr_service = GDPRService()
