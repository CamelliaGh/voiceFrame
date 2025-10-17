import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models import SessionModel, Order
from ..config import settings


class PrivacyService:
    """Handles privacy compliance features including unsubscribe management"""

    def __init__(self):
        self.unsubscribe_salt = "audioposter_unsubscribe_2024"  # In production, use a secure random salt

    def generate_unsubscribe_token(self, email: str) -> str:
        """Generate a secure unsubscribe token for an email address"""
        # Create a hash of email + salt + timestamp for security
        timestamp = str(int(datetime.utcnow().timestamp()))
        data = f"{email}:{self.unsubscribe_salt}:{timestamp}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return token

    def verify_unsubscribe_token(self, email: str, token: str) -> bool:
        """Verify if an unsubscribe token is valid for an email"""
        # For simplicity, we'll accept tokens within the last 30 days
        current_time = int(datetime.utcnow().timestamp())

        for days_back in range(30):
            timestamp = str(current_time - (days_back * 24 * 60 * 60))
            data = f"{email}:{self.unsubscribe_salt}:{timestamp}"
            expected_token = hashlib.sha256(data.encode()).hexdigest()

            if token == expected_token:
                return True

        return False

    def create_unsubscribe_url(self, email: str) -> str:
        """Create a complete unsubscribe URL for an email"""
        token = self.generate_unsubscribe_token(email)
        return f"{settings.unsubscribe_url}?email={email}&token={token}"

    def get_privacy_footer_links(self) -> dict:
        """Get privacy-related footer links for emails"""
        return {
            "privacy_policy": settings.privacy_policy_url,
            "unsubscribe": settings.unsubscribe_url,
            "company_name": settings.company_name,
            "company_address": settings.company_address
        }

    def is_email_unsubscribed(self, email: str, db: Session) -> bool:
        """Check if an email address is in the unsubscribe list"""
        # For now, we'll store unsubscribe status in session data
        # In production, you'd want a separate unsubscribe table
        session = db.query(SessionModel).filter(
            SessionModel.email == email,
            SessionModel.unsubscribed == True
        ).first()

        return session is not None

    def unsubscribe_email(self, email: str, db: Session) -> bool:
        """Add an email to the unsubscribe list"""
        try:
            # Update all sessions with this email to mark as unsubscribed
            sessions = db.query(SessionModel).filter(SessionModel.email == email).all()

            for session in sessions:
                session.unsubscribed = True
                session.unsubscribed_at = datetime.utcnow()

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"Error unsubscribing email {email}: {str(e)}")
            return False

    def resubscribe_email(self, email: str, db: Session) -> bool:
        """Remove an email from the unsubscribe list"""
        try:
            # Update all sessions with this email to mark as resubscribed
            sessions = db.query(SessionModel).filter(SessionModel.email == email).all()

            for session in sessions:
                session.unsubscribed = False
                session.unsubscribed_at = None

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"Error resubscribing email {email}: {str(e)}")
            return False

    def cleanup_expired_data(self, db: Session) -> int:
        """Clean up expired session data based on retention policy"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.data_retention_days)

            # Find expired sessions
            expired_sessions = db.query(SessionModel).filter(
                SessionModel.created_at < cutoff_date
            ).all()

            deleted_count = 0

            for session in expired_sessions:
                # Delete associated orders
                orders = db.query(Order).filter(Order.session_token == session.session_token).all()
                for order in orders:
                    db.delete(order)

                # Delete the session
                db.delete(session)
                deleted_count += 1

            db.commit()
            return deleted_count

        except Exception as e:
            db.rollback()
            print(f"Error cleaning up expired data: {str(e)}")
            return 0

    def get_data_retention_info(self) -> dict:
        """Get information about data retention policies"""
        return {
            "retention_days": settings.data_retention_days,
            "cutoff_date": datetime.utcnow() - timedelta(days=settings.data_retention_days),
            "policy_description": f"Sessions and associated data are automatically deleted after {settings.data_retention_days} days of inactivity"
        }

    def generate_privacy_footer_html(self, unsubscribe_url: str = None) -> str:
        """Generate HTML footer with privacy compliance links"""
        links = self.get_privacy_footer_links()

        # Only include company address if it's provided
        address_section = ""
        if links['company_address'] and links['company_address'].strip():
            address_section = f"""
            <p style="margin: 5px 0; font-size: 12px;">
                {links['company_address']}
            </p>"""

        footer = f"""
        <div style="background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; border-radius: 0 0 10px 10px; margin-top: 30px;">
            <p style="margin: 5px 0; font-size: 12px;">
                © 2024 {links['company_name']}. All rights reserved.
            </p>{address_section}
            <p style="margin: 10px 0; font-size: 12px;">
                <a href="{links['privacy_policy']}" style="color: #8b5cf6; text-decoration: none;">Privacy Policy</a> |
                <a href="{unsubscribe_url or links['unsubscribe']}" style="color: #8b5cf6; text-decoration: none;">Unsubscribe</a> |
                <a href="https://vocaframe.com/do-not-sell" style="color: #8b5cf6; text-decoration: none;">Do Not Sell My Personal Information</a>
            </p>
            <p style="margin: 5px 0; font-size: 11px; color: #9ca3af;">
                You received this email because you created an AudioPoster.
                If you no longer wish to receive emails, please <a href="{unsubscribe_url or links['unsubscribe']}" style="color: #8b5cf6;">unsubscribe here</a>.
            </p>
        </div>
        """

        return footer

    def generate_privacy_footer_text(self, unsubscribe_url: str = None) -> str:
        """Generate plain text footer with privacy compliance information"""
        links = self.get_privacy_footer_links()

        # Only include company address if it's provided
        address_line = ""
        if links['company_address'] and links['company_address'].strip():
            address_line = f"{links['company_address']}\n"

        footer = f"""

© 2024 {links['company_name']}. All rights reserved.
{address_line}Privacy Policy: {links['privacy_policy']}
Unsubscribe: {unsubscribe_url or links['unsubscribe']}
Do Not Sell My Personal Information: https://vocaframe.com/do-not-sell

You received this email because you created an AudioPoster.
If you no longer wish to receive emails, please unsubscribe here: {unsubscribe_url or links['unsubscribe']}
        """

        return footer
