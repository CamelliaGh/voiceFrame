import asyncio
import os
from datetime import datetime

from celery import Celery
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models import Order, SessionModel
from .services.audio_processor import AudioProcessor
from .services.email_service import EmailService
from .services.file_uploader import FileUploader
from .services.pdf_generator import PDFGenerator

# Configure Celery
celery_app = Celery(
    "audioposter",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # task_routes={
    #     'backend.tasks.process_audio_task': {'queue': 'audio'},
    #     'backend.tasks.generate_pdf_task': {'queue': 'pdf'},
    #     'backend.tasks.send_email_task': {'queue': 'email'},
    # },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Initialize services
audio_processor = AudioProcessor()
pdf_generator = PDFGenerator()
email_service = EmailService()


def get_db():
    """Get database session for tasks"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, close in task


@celery_app.task(bind=True, max_retries=3)
def process_audio_task(self, session_token: str, audio_s3_key: str):
    """
    Background task to process uploaded audio file and generate waveform

    Args:
        session_token: Session identifier
        audio_s3_key: S3 key for the uploaded audio file
    """
    db = get_db()
    try:
        # Get session from database
        session = (
            db.query(SessionModel)
            .filter(SessionModel.session_token == session_token)
            .first()
        )

        if not session:
            raise Exception(f"Session {session_token} not found")

        # Process audio and generate waveform
        result = asyncio.run(
            audio_processor.process_audio_file(audio_s3_key, session_token)
        )

        # Update session with processing results
        session.waveform_s3_key = result["waveform_s3_key"]
        session.audio_duration = result["duration"]
        db.commit()

        return {
            "status": "completed",
            "session_token": session_token,
            "duration": result["duration"],
            "waveform_s3_key": result["waveform_s3_key"],
        }

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"Audio processing task error: {error_trace}")
        db.rollback()

        # Retry logic
        if self.request.retries < self.max_retries:
            # Exponential backoff: 1min, 2min, 4min
            countdown = 60 * (2**self.request.retries)
            print(f"Retrying audio processing task in {countdown} seconds...")
            raise self.retry(countdown=countdown, exc=e)
        else:
            # Mark session as failed after max retries
            session = (
                db.query(SessionModel)
                .filter(SessionModel.session_token == session_token)
                .first()
            )
            if session:
                session.processing_status = "failed"
                db.commit()

            print(f"Audio processing failed permanently: {str(e)}")
            raise Exception(
                f"Audio processing failed after {self.max_retries} retries: {str(e)}"
            )

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def generate_pdf_task(
    self, session_token: str, order_id: str, watermarked: bool = False
):
    """
    Background task to generate PDF poster

    Args:
        session_token: Session identifier
        order_id: Order identifier
        watermarked: Whether to add watermark (for preview)
    """
    db = get_db()
    try:
        # Get session and order from database
        session = (
            db.query(SessionModel)
            .filter(SessionModel.session_token == session_token)
            .first()
        )

        order = db.query(Order).filter(Order.id == order_id).first()

        if not session:
            raise Exception(f"Session {session_token} not found")

        if not order:
            raise Exception(f"Order {order_id} not found")

        # Verify session has required data
        if not session.photo_s3_key or not session.waveform_s3_key:
            raise Exception("Session missing required files for PDF generation")

        # Generate PDF
        if watermarked:
            pdf_url = asyncio.run(pdf_generator.generate_preview_pdf(session))
        else:
            pdf_url = asyncio.run(pdf_generator.generate_final_pdf(session, order))

            # Update order with PDF location
            order.pdf_s3_key = pdf_url
            order.status = "completed"
            db.commit()

            # Schedule email sending
            send_email_task.delay(
                order.email, pdf_url, order.download_expires_at.isoformat(), order_id
            )

        return {
            "status": "completed",
            "order_id": order_id,
            "pdf_url": pdf_url,
            "watermarked": watermarked,
        }

    except Exception as e:
        db.rollback()

        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 60 * (2**self.request.retries)
            raise self.retry(countdown=countdown, exc=e)
        else:
            # Mark order as failed after max retries
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = "failed"
                db.commit()

            raise Exception(
                f"PDF generation failed after {self.max_retries} retries: {str(e)}"
            )

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_email_task(
    self, email: str, download_url: str, expires_at_iso: str, order_id: str = None
):
    """
    Background task to send download email

    Args:
        email: Recipient email
        download_url: PDF download URL
        expires_at_iso: Expiration datetime in ISO format
        order_id: Order identifier
    """
    try:
        # Parse expiration datetime
        expires_at = datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))

        # Send email
        success = asyncio.run(
            email_service.send_download_email(email, download_url, expires_at, order_id)
        )

        if not success:
            raise Exception("Email sending failed")

        return {"status": "completed", "email": email, "order_id": order_id}

    except Exception as e:
        # Retry logic
        if self.request.retries < self.max_retries:
            countdown = 300 * (2**self.request.retries)  # 5min, 10min, 20min
            raise self.retry(countdown=countdown, exc=e)
        else:
            # Log failure but don't crash - email is not critical
            print(f"Email sending failed after {self.max_retries} retries: {str(e)}")
            return {"status": "failed", "email": email, "error": str(e)}


@celery_app.task
def cleanup_expired_sessions():
    """
    Manual task to clean up expired session database records only
    Files are cleaned up separately by the 7-day cleanup task
    This task only removes database records for expired sessions
    """
    db = get_db()
    try:
        # Find expired sessions (with 1 day buffer for safety)
        expired_sessions = (
            db.query(SessionModel)
            .filter(SessionModel.expires_at <= datetime.utcnow())
            .all()
        )

        cleanup_count = 0

        for session in expired_sessions:
            try:
                # Check if this session has been converted to a paid order
                has_paid_order = (
                    db.query(Order)
                    .filter(
                        Order.session_token == session.session_token,
                        Order.status == "completed",
                    )
                    .first()
                )

                if has_paid_order:
                    print(
                        f"Keeping session record for paid order: {session.session_token}"
                    )
                    continue

                # Only delete session database record - files cleaned up separately
                db.delete(session)
                cleanup_count += 1
                print(f"Deleted expired session record: {session.session_token}")

            except Exception as e:
                print(f"Error cleaning up session {session.session_token}: {e}")
                continue

        db.commit()

        return {
            "status": "completed",
            "sessions_cleaned": cleanup_count,
            "note": "Only database records cleaned - files handled by 7-day cleanup task",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        db.rollback()
        raise Exception(f"Session cleanup failed: {str(e)}")

    finally:
        db.close()


@celery_app.task
def cleanup_orphaned_audio_files():
    """
    Manual cleanup task for orphaned temporary audio files only
    Only deletes files older than 7 days to prevent accidental deletion
    Permanent files are never automatically deleted
    """
    db = get_db()
    try:
        from .services.file_uploader import FileUploader

        file_uploader = FileUploader()
        orphaned_count = 0

        # Clean up orphaned temporary audio files older than 7 days
        try:
            temp_audio_files = file_uploader.list_files_with_prefix("temp_audio/")

            for file_key in temp_audio_files:
                # Check if any session references this file
                session_exists = (
                    db.query(SessionModel)
                    .filter(SessionModel.audio_s3_key == file_key)
                    .first()
                )

                if not session_exists:
                    # Check if this file was moved to permanent storage
                    file_name = file_key.split("/")[-1].replace(".mp3", "")

                    # Try to find if this was converted to permanent storage
                    permanent_exists = (
                        db.query(Order)
                        .filter(Order.permanent_audio_s3_key.contains(file_name))
                        .first()
                    )

                    if not permanent_exists:
                        # Check file age - only delete if older than 7 days
                        file_creation_time = file_uploader.get_file_creation_time(
                            file_key
                        )
                        if file_creation_time:
                            days_old = (datetime.utcnow() - file_creation_time).days
                            if days_old >= 7:
                                # Safe to delete - it's truly orphaned and old enough
                                file_uploader.delete_file(file_key)
                                orphaned_count += 1
                                print(
                                    f"Deleted orphaned audio file (age: {days_old} days): {file_key}"
                                )
                            else:
                                print(
                                    f"Keeping orphaned file (too recent, age: {days_old} days): {file_key}"
                                )
                        else:
                            print(
                                f"Could not determine age of orphaned file, keeping: {file_key}"
                            )
                    else:
                        print(
                            f"Keeping file that was moved to permanent storage: {file_key}"
                        )

        except Exception as e:
            print(f"Error during orphaned file cleanup: {e}")

        return {
            "status": "completed",
            "orphaned_files_deleted": orphaned_count,
            "note": "Only temporary files older than 7 days are deleted",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise Exception(f"Audio cleanup failed: {str(e)}")

    finally:
        db.close()


@celery_app.task
def cleanup_expired_orders():
    """
    Periodic task to clean up expired order download links
    Schedule this to run daily
    """
    db = get_db()
    try:
        # Find orders with expired download links
        expired_orders = (
            db.query(Order)
            .filter(
                Order.download_expires_at <= datetime.utcnow(),
                Order.status == "completed",
            )
            .all()
        )

        cleanup_count = 0
        for order in expired_orders:
            try:
                # Delete PDF file from storage (but KEEP permanent audio for QR codes)
                if order.pdf_s3_key:
                    from .services.file_uploader import FileUploader

                    file_uploader = FileUploader()
                    file_uploader.delete_file(order.pdf_s3_key)

                # Update order status but keep record and permanent audio for analytics and QR codes
                order.status = "expired"
                order.pdf_s3_key = None
                # DO NOT delete permanent_audio_s3_key - needed for QR codes forever
                cleanup_count += 1

            except Exception as e:
                print(f"Error cleaning up order {order.id}: {e}")
                continue

        db.commit()

        return {
            "status": "completed",
            "cleaned_up": cleanup_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        db.rollback()
        raise Exception(f"Order cleanup failed: {str(e)}")

    finally:
        db.close()


@celery_app.task
def send_marketing_email_batch(
    email_list: list, subject: str, html_content: str, text_content: str
):
    """
    Background task to send marketing emails to a batch of subscribers

    Args:
        email_list: List of email addresses
        subject: Email subject
        html_content: HTML email content
        text_content: Plain text email content
    """
    try:
        sent_count = asyncio.run(
            email_service.send_marketing_email(
                email_list, subject, html_content, text_content
            )
        )

        return {
            "status": "completed",
            "total_emails": len(email_list),
            "sent_successfully": sent_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise Exception(f"Marketing email batch failed: {str(e)}")


# Periodic task schedule - DISABLED FOR DEVELOPMENT
# Uncomment these when deploying to production
# celery_app.conf.beat_schedule = {
#     'cleanup-expired-sessions': {
#         'task': 'backend.tasks.cleanup_expired_sessions',
#         'schedule': 86400.0,  # Run daily (24 hours)
#     },
#     'cleanup-orphaned-audio-files': {
#         'task': 'backend.tasks.cleanup_orphaned_audio_files',
#         'schedule': 86400.0,  # Run daily (24 hours)
#     },
#     'cleanup-expired-orders': {
#         'task': 'backend.tasks.cleanup_expired_orders',
#         'schedule': 86400.0,  # Run daily (24 hours)
#     },
# }
