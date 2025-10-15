import resend
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from fastapi import HTTPException

from ..config import settings
from .privacy_service import PrivacyService

logger = logging.getLogger(__name__)

class EmailService:
    """Handles email delivery for downloads and marketing using Resend"""

    def __init__(self):
        if settings.resend_api_key:
            resend.api_key = settings.resend_api_key
            self.resend_configured = True
        else:
            self.resend_configured = False
            print("Warning: Resend API key not configured - emails will be logged only")

        self.privacy_service = PrivacyService()

    async def send_download_email(self, email: str, download_url: str,
                                 expires_at: datetime, order_id: str = None) -> bool:
        """
        Send download email with PDF link

        Args:
            email: Customer email
            download_url: Presigned URL for PDF download
            expires_at: When the download link expires
            order_id: Order ID for reference

        Returns:
            True if email sent successfully
        """
        try:
            subject = "Your VocaFrame is Ready! 🎵"

            # Format expiration time
            expires_str = expires_at.strftime("%B %d, %Y at %I:%M %p UTC")

            # Generate unsubscribe URL for this email
            unsubscribe_url = self.privacy_service.create_unsubscribe_url(email)

            html_content = self._create_download_email_html(
                download_url, expires_str, order_id, unsubscribe_url
            )

            text_content = self._create_download_email_text(
                download_url, expires_str, order_id, unsubscribe_url
            )

            return await self._send_email(email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send download email to {email}: {str(e)}")
            return False

    async def send_welcome_email(self, email: str, first_name: str = None) -> bool:
        """
        Send welcome email to new subscribers

        Args:
            email: Subscriber email
            first_name: Optional first name

        Returns:
            True if email sent successfully
        """
        try:
            subject = "Welcome to VocaFrame! 🎨"

            # Generate unsubscribe URL for this email
            unsubscribe_url = self.privacy_service.create_unsubscribe_url(email)

            html_content = self._create_welcome_email_html(first_name, unsubscribe_url)
            text_content = self._create_welcome_email_text(first_name, unsubscribe_url)

            return await self._send_email(email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            return False

    async def send_marketing_email(self, emails: List[str], subject: str,
                                  html_content: str, text_content: str) -> int:
        """
        Send marketing email to multiple recipients

        Args:
            emails: List of recipient emails
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content

        Returns:
            Number of emails sent successfully
        """
        sent_count = 0

        for email in emails:
            try:
                if await self._send_email(email, subject, html_content, text_content):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send marketing email to {email}: {str(e)}")
                continue

        return sent_count

    async def _send_email(self, to_email: str, subject: str,
                         html_content: str, text_content: str) -> bool:
        """
        Core email sending function using Resend

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content

        Returns:
            True if sent successfully
        """
        if not self.resend_configured:
            # Log email for development
            logger.info(f"EMAIL (not sent - no API key):")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content: {text_content[:200]}...")
            return True

        try:
            params = {
                "from": f"VoiceFrame <{settings.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            }

            response = resend.Emails.send(params)

            # Resend returns email ID on success
            if response and "id" in response:
                logger.info(f"Email sent successfully to {to_email} (ID: {response['id']})")
                return True
            else:
                logger.error(f"Email send failed - no ID returned")
                return False

        except Exception as e:
            logger.error(f"Resend error: {str(e)}")
            return False

    def _create_download_email_html(self, download_url: str, expires_str: str,
                                   order_id: str = None, unsubscribe_url: str = None) -> str:
        """Create HTML content for download email"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your VocaFrame is Ready!</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
                .download-btn {{ background: #8b5cf6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; margin: 20px 0; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; border-radius: 0 0 10px 10px; }}
                .warning {{ background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎵 Your AudioPoster is Ready!</h1>
                    <p>Your beautiful audio memory poster has been generated</p>
                </div>

                <div class="content">
                    <p>Thank you for using AudioPoster! Your custom poster combining your photo, audio waveform, and personal message is now ready for download.</p>

                    <div style="text-align: center;">
                        <a href="{download_url}" class="download-btn">Download Your Poster</a>
                    </div>

                    <div class="warning">
                        <strong>⏰ Important:</strong> This download link expires on <strong>{expires_str}</strong>.
                        Make sure to download your poster before then!
                    </div>

                    <h3>What you'll get:</h3>
                    <ul>
                        <li>High-resolution PDF (300 DPI) perfect for printing</li>
                        <li>Your photo with custom audio waveform visualization</li>
                        <li>QR code linking to your audio playback</li>
                        <li>Professional poster layout ready to frame</li>
                    </ul>

                    <h3>Printing Tips:</h3>
                    <ul>
                        <li>Print on high-quality photo paper or cardstock</li>
                        <li>Use color printing for best results</li>
                        <li>Consider professional printing services for premium quality</li>
                    </ul>

                    {f'<p><small>Order ID: {order_id}</small></p>' if order_id else ''}
                </div>

                <div class="footer">
                    <p>Love your AudioPoster? Share it with friends and family!</p>
                    <p>Visit <a href="{settings.base_url}">AudioPoster.com</a> to create more beautiful memory posters.</p>
                    <p><small>If you have any questions, reply to this email and we'll help you out.</small></p>
                </div>

                {self.privacy_service.generate_privacy_footer_html(unsubscribe_url)}
            </div>
        </body>
        </html>
        """

    def _create_download_email_text(self, download_url: str, expires_str: str,
                                   order_id: str = None, unsubscribe_url: str = None) -> str:
        """Create plain text content for download email"""
        return f"""
Your AudioPoster is Ready! 🎵

Thank you for using AudioPoster! Your custom poster combining your photo, audio waveform, and personal message is now ready for download.

Download Your Poster: {download_url}

⏰ IMPORTANT: This download link expires on {expires_str}. Make sure to download your poster before then!

What you'll get:
- High-resolution PDF (300 DPI) perfect for printing
- Your photo with custom audio waveform visualization
- QR code linking to your audio playback
- Professional poster layout ready to frame

Printing Tips:
- Print on high-quality photo paper or cardstock
- Use color printing for best results
- Consider professional printing services for premium quality

{f'Order ID: {order_id}' if order_id else ''}

Love your AudioPoster? Share it with friends and family!
Visit {settings.base_url} to create more beautiful memory posters.

If you have any questions, reply to this email and we'll help you out.
{self.privacy_service.generate_privacy_footer_text(unsubscribe_url)}
        """

    def _create_welcome_email_html(self, first_name: str = None, unsubscribe_url: str = None) -> str:
        """Create HTML content for welcome email"""
        name = first_name if first_name else "there"

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to AudioPoster!</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
                .cta-btn {{ background: #8b5cf6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; margin: 20px 0; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎨 Welcome to AudioPoster!</h1>
                    <p>Transform your memories into beautiful art</p>
                </div>

                <div class="content">
                    <p>Hi {name}!</p>

                    <p>Welcome to the AudioPoster community! We're excited to help you create beautiful, personalized posters that combine your favorite photos with audio memories.</p>

                    <h3>What makes AudioPoster special:</h3>
                    <ul>
                        <li>🎵 <strong>Audio Waveform Art:</strong> Turn any audio into beautiful visualizations</li>
                        <li>📷 <strong>Photo Integration:</strong> Combine your images with audio memories</li>
                        <li>✨ <strong>Custom Text:</strong> Add personal messages and dedications</li>
                        <li>🎁 <strong>Perfect Gifts:</strong> Create unique presents for loved ones</li>
                        <li>🖼️ <strong>Print-Ready:</strong> High-quality PDFs ready for framing</li>
                    </ul>

                    <div style="text-align: center;">
                        <a href="{settings.base_url}" class="cta-btn">Create Your First Poster</a>
                    </div>

                    <h3>Popular uses:</h3>
                    <ul>
                        <li>Anniversary songs and voice messages</li>
                        <li>Baby's first words and lullabies</li>
                        <li>Wedding vows and speeches</li>
                        <li>Favorite song lyrics and melodies</li>
                        <li>Graduation speeches and memories</li>
                    </ul>
                </div>

                <div class="footer">
                    <p>Questions? Tips? We'd love to hear from you!</p>
                    <p>Reply to this email anytime - we read every message.</p>
                    <p><small>Follow us for inspiration and new features!</small></p>
                </div>

                {self.privacy_service.generate_privacy_footer_html(unsubscribe_url)}
            </div>
        </body>
        </html>
        """

    def _create_welcome_email_text(self, first_name: str = None, unsubscribe_url: str = None) -> str:
        """Create plain text content for welcome email"""
        name = first_name if first_name else "there"

        return f"""
Welcome to AudioPoster! 🎨

Hi {name}!

Welcome to the AudioPoster community! We're excited to help you create beautiful, personalized posters that combine your favorite photos with audio memories.

What makes AudioPoster special:
🎵 Audio Waveform Art: Turn any audio into beautiful visualizations
📷 Photo Integration: Combine your images with audio memories
✨ Custom Text: Add personal messages and dedications
🎁 Perfect Gifts: Create unique presents for loved ones
🖼️ Print-Ready: High-quality PDFs ready for framing

Create Your First Poster: {settings.base_url}

Popular uses:
- Anniversary songs and voice messages
- Baby's first words and lullabies
- Wedding vows and speeches
- Favorite song lyrics and melodies
- Graduation speeches and memories

Questions? Tips? We'd love to hear from you!
Reply to this email anytime - we read every message.
{self.privacy_service.generate_privacy_footer_text(unsubscribe_url)}
        """
