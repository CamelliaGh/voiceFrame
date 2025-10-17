import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Import security middleware
from .middleware.security_headers import SecurityHeadersMiddleware, RateLimitMiddleware, SecurityLoggingMiddleware

from .config import settings
from .database import engine, get_db
from .models import Base, EmailSubscriber, Order, SessionModel
from .schemas import (
    CompleteOrderRequest,
    DownloadResponse,
    PaymentIntentRequest,
    PaymentIntentResponse,
    ProcessingStatus,
    SessionResponse,
    SessionUpdate,
    UploadResponse,
)
from .services.audio_processor import AudioProcessor
from .services.config_service import config_service
from .services.content_filter import content_filter
from .services.email_service import EmailService
from .services.privacy_service import PrivacyService
from .services.file_uploader import FileUploader
from .services.image_processor import ImageProcessor
from .services.pdf_generator import PDFGenerator
from .services.visual_pdf_generator import VisualPDFGenerator
from .services.permanent_audio_service import PermanentAudioService
from .services.rate_limiter import rate_limiter
from .services.session_manager import SessionManager
from .services.storage_manager import StorageManager
from .services.stripe_service import StripeService
from .services.visual_template_service import VisualTemplateService
from .services.file_access_validator import FileAccessValidator
from .services.admin_auth import AdminAuthService
from .services.consent_manager import consent_manager, ConsentType
from .services.gdpr_service import gdpr_service
from .services.data_minimization_service import data_minimization_service, DataCategory, ProcessingPurpose
from .services.file_audit_logger import file_audit_logger, FileOperationContext, FileOperationType, FileType, FileOperationStatus
from .metrics import get_metrics_response, MetricsMiddleware
from .services.admin_resource_service import admin_resource_service
from .routers import admin, admin_auth, simple_admin

# Configure logging
logger = logging.getLogger(__name__)

# Initialize services
storage_manager = StorageManager()

# Create database tables (skip in test mode)
if not os.getenv("TESTING", False):
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AudioPoster API",
    description="API for creating personalized audio poster PDFs",
    version="1.0.0",
)

# Add security middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    environment=os.getenv("ENVIRONMENT", "development")
)

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.get_rate_limit_requests_per_minute(),
    burst_size=settings.get_rate_limit_burst_size()
)

app.add_middleware(SecurityLoggingMiddleware)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Initialize rate limiter on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    await rate_limiter.initialize()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for serving uploaded files and generated PDFs
static_dir = "/tmp/audioposter"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount admin backgrounds directory FIRST for serving admin-managed background images
# More specific routes must be mounted before general ones in FastAPI
admin_backgrounds_dir = "backgrounds/admin"
os.makedirs(admin_backgrounds_dir, exist_ok=True)
app.mount("/backgrounds/admin", StaticFiles(directory=admin_backgrounds_dir), name="admin_backgrounds")

# Mount backgrounds directory for serving default background images
backgrounds_dir = "backgrounds"
os.makedirs(backgrounds_dir, exist_ok=True)
app.mount("/backgrounds", StaticFiles(directory=backgrounds_dir), name="backgrounds")

# Include routers
app.include_router(admin.router)
app.include_router(admin_auth.router)
app.include_router(simple_admin.router)

# Initialize services
session_manager = SessionManager()
file_uploader = FileUploader()
audio_processor = AudioProcessor()
image_processor = ImageProcessor()
pdf_generator = VisualPDFGenerator()  # Using VisualPDFGenerator for template-based PDFs
stripe_service = StripeService()
email_service = EmailService()
privacy_service = PrivacyService()
permanent_audio_service = PermanentAudioService()
template_service = VisualTemplateService()
file_access_validator = FileAccessValidator()
admin_auth_service = AdminAuthService()


@app.get("/")
async def root():
    return {"message": "AudioPoster API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/test/s3-debug")
async def test_s3_debug(
    admin_auth: bool = Depends(lambda: admin_auth_service.get_admin_dependency())
):
    """Test S3 configuration and presigned URL generation"""
    try:
        file_uploader = FileUploader()

        if not file_uploader.s3_client:
            return {"error": "S3 client not initialized - check AWS credentials"}

        # Test bucket access
        try:
            response = file_uploader.s3_client.head_bucket(Bucket=settings.s3_bucket)
            bucket_status = "accessible"
        except ClientError as e:
            bucket_status = f"error: {e}"

        # Test presigned URL generation
        test_key = "test/debug_file.txt"
        try:
            test_url = file_uploader.generate_presigned_url(test_key, expiration=300)
            url_status = "generated successfully"
        except Exception as e:
            url_status = f"error: {e}"
            test_url = None

        return {
            "s3_configured": file_uploader.s3_client is not None,
            "bucket_name": settings.s3_bucket,
            "region": settings.s3_region,
            "bucket_status": bucket_status,
            "url_generation": url_status,
            "test_url": test_url[:100] + "..." if test_url else None,
            "access_key_prefix": settings.aws_access_key_id[:10] + "..." if settings.aws_access_key_id else None
        }

    except Exception as e:
        return {"error": f"Debug test failed: {str(e)}"}

@app.post("/api/test/resend")
async def test_resend_email(
    test_email: str = Form(...),
    admin_auth: bool = Depends(lambda: admin_auth_service.get_admin_dependency())
):
    """
    Test Resend email configuration by sending a test email

    This endpoint requires admin authentication and sends a test email
    to verify that Resend is properly configured.
    """
    try:
        # Check if Resend is configured
        if not settings.resend_api_key:
            return {
                "status": "error",
                "message": "Resend API key is not configured",
                "configured": False,
                "api_key_set": False
            }

        # Check if API key looks valid (starts with re_)
        api_key_valid = settings.resend_api_key.startswith("re_")

        # Try to send a test email
        try:
            test_subject = "VoiceFrame - Resend Test Email"
            test_html = """
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #8b5cf6;">✅ Resend Test Successful!</h2>
                    <p>This is a test email from your VoiceFrame application.</p>
                    <p>If you're receiving this, your Resend configuration is working correctly!</p>
                    <hr style="margin: 20px 0;">
                    <p style="color: #666; font-size: 14px;">
                        <strong>Configuration Details:</strong><br>
                        From Email: {from_email}<br>
                        Timestamp: {timestamp}
                    </p>
                </body>
            </html>
            """.format(
                from_email=settings.from_email,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            )

            test_text = """
            ✅ Resend Test Successful!

            This is a test email from your VoiceFrame application.
            If you're receiving this, your Resend configuration is working correctly!

            Configuration Details:
            From Email: {from_email}
            Timestamp: {timestamp}
            """.format(
                from_email=settings.from_email,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            )

            # Send the test email
            success = await email_service._send_email(
                test_email,
                test_subject,
                test_html,
                test_text
            )

            if success:
                return {
                    "status": "success",
                    "message": f"Test email sent successfully to {test_email}",
                    "configured": True,
                    "api_key_set": True,
                    "api_key_valid_format": api_key_valid,
                    "from_email": settings.from_email,
                    "test_email": test_email
                }
            else:
                return {
                    "status": "error",
                    "message": "Email service returned False - check logs for details",
                    "configured": True,
                    "api_key_set": True,
                    "api_key_valid_format": api_key_valid
                }

        except Exception as send_error:
            error_message = str(send_error)

            # Check for specific error types
            if "401" in error_message or "Unauthorized" in error_message or "Invalid API" in error_message:
                return {
                    "status": "error",
                    "message": "Resend API key is invalid or unauthorized",
                    "error": error_message,
                    "configured": True,
                    "api_key_set": True,
                    "api_key_valid_format": api_key_valid,
                    "solution": "Please check your RESEND_API_KEY in .env file. Get a valid key from Resend dashboard."
                }
            elif "403" in error_message or "Forbidden" in error_message:
                return {
                    "status": "error",
                    "message": "Resend API key doesn't have required permissions",
                    "error": error_message,
                    "configured": True,
                    "api_key_set": True,
                    "api_key_valid_format": api_key_valid,
                    "solution": "Ensure your Resend API key has proper permissions"
                }
            elif "domain" in error_message.lower() or "sender" in error_message.lower():
                return {
                    "status": "error",
                    "message": "Sender domain is not verified in Resend",
                    "error": error_message,
                    "configured": True,
                    "api_key_set": True,
                    "api_key_valid_format": api_key_valid,
                    "from_email": settings.from_email,
                    "solution": f"Verify the sender domain for '{settings.from_email}' in Resend dashboard"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to send test email",
                    "error": error_message,
                    "configured": True,
                    "api_key_set": True,
                    "api_key_valid_format": api_key_valid
                }

    except Exception as e:
        logger.error(f"Resend test endpoint error: {str(e)}")
        return {
            "status": "error",
            "message": "Unexpected error testing Resend",
            "error": str(e)
        }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics_response()


@app.get("/api/price")
async def get_current_price(db: Session = Depends(get_db)):
    """Get the current price in cents for the audio poster with discount information"""
    try:
        pricing_info = config_service.get_discounted_price_cents(db)

        return {
            "price_cents": pricing_info["discounted_price"],
            "original_price_cents": pricing_info["original_price"],
            "price_dollars": pricing_info["discounted_price"] / 100,
            "original_price_dollars": pricing_info["original_price"] / 100,
            "formatted_price": f"${pricing_info['discounted_price'] / 100:.2f}",
            "formatted_original_price": f"${pricing_info['original_price'] / 100:.2f}",
            "discount_percentage": pricing_info["discount_percentage"],
            "discount_amount": pricing_info["discount_amount"],
            "discount_enabled": pricing_info["discount_enabled"],
            "has_discount": pricing_info["discount_enabled"] and pricing_info["discount_percentage"] > 0
        }
    except Exception as e:
        logger.error(f"Error getting current price: {str(e)}")
        # Return default price if there's an error
        return {
            "price_cents": 299,
            "original_price_cents": 299,
            "price_dollars": 2.99,
            "original_price_dollars": 2.99,
            "formatted_price": "$2.99",
            "formatted_original_price": "$2.99",
            "discount_percentage": 0,
            "discount_amount": 0,
            "discount_enabled": False,
            "has_discount": False
        }


# Session Management
@app.post("/api/session", response_model=SessionResponse)
async def create_session(db: Session = Depends(get_db), request: Request = None):
    """Create a new session for file uploads and customization"""
    # Apply more lenient rate limiting for session creation
    if settings.is_rate_limit_enabled() and request:
        # Use burst rate limiting instead of general API rate limiting
        await rate_limiter.check_burst_rate_limit(request)
        if await rate_limiter.is_banned(request):
            raise HTTPException(status_code=403, detail="Access temporarily restricted")

    try:
        session = session_manager.create_session(db, expires_hours=2)

        return SessionResponse(
            session_token=session.session_token, expires_at=session.expires_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )


@app.get("/api/session/{token}", response_model=SessionResponse)
async def get_session(token: str, db: Session = Depends(get_db)):
    """Get session data"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate presigned URLs for photo and waveform
    photo_url = None
    waveform_url = None

    if session.photo_s3_key:
        photo_url = file_uploader.generate_presigned_url(session.photo_s3_key, expiration=3600)

    if session.waveform_s3_key:
        waveform_url = file_uploader.generate_presigned_url(session.waveform_s3_key, expiration=3600)

    return SessionResponse(
        session_token=session.session_token,
        expires_at=session.expires_at.isoformat(),
        custom_text=session.custom_text,
        photo_shape=session.photo_shape,
        pdf_size=session.pdf_size,
        template_id=session.template_id,
        photo_url=photo_url,
        waveform_url=waveform_url,
        audio_duration=session.audio_duration,
        photo_filename=session.photo_filename,
        photo_size=session.photo_size,
        audio_filename=session.audio_filename,
        audio_size=session.audio_size,
    )


@app.put("/api/session/{token}")
async def update_session(
    token: str, data: SessionUpdate, db: Session = Depends(get_db)
):
    """Update session customization data"""
    print("🚨 PUT REQUEST RECEIVED!")
    print(f"DEBUG: Received data: {data.model_dump()}")

    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate that required files are uploaded
    if not session.photo_s3_key:
        raise HTTPException(
            status_code=400, detail="Photo must be uploaded before customization"
        )

    if not session.audio_s3_key:
        raise HTTPException(
            status_code=400, detail="Audio file must be uploaded before customization"
        )

    # Get update data first to check if it's a photo shape only update
    update_data = data.model_dump(exclude_unset=True)
    print(f"DEBUG: Session update received - token: {token}")
    print(f"DEBUG: Update data after exclude_unset: {update_data}")
    print(f"DEBUG: Current session photo_shape: {session.photo_shape}")

    # Validate that audio processing is complete (except for photo_shape updates)
    is_photo_shape_only_update = len(update_data) == 1 and "photo_shape" in update_data
    print(f"DEBUG: is_photo_shape_only_update: {is_photo_shape_only_update}")

    if not session.waveform_s3_key and not is_photo_shape_only_update:
        print(f"DEBUG: Waveform not ready, rejecting update. waveform_s3_key: {session.waveform_s3_key}")
        raise HTTPException(
            status_code=400,
            detail="Audio processing not complete. Please wait and try again.",
        )

    try:
        print(
            f"DEBUG: Session before update - custom_text: '{session.custom_text}', font_id: '{session.font_id}'"
        )
        session_manager.update_session(db, session, update_data)
        print(
            f"DEBUG: Session after update - custom_text: '{session.custom_text}', font_id: '{session.font_id}'"
        )
        print(f"DEBUG: Session after update - photo_shape: '{session.photo_shape}'")
        return {"status": "updated"}
    except ValueError as e:
        error_msg = str(e)
        print(f"DEBUG: ValueError in update_session: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Unexpected error in update_session: {error_msg}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")


@app.post("/api/session/{token}/validate")
async def validate_session_for_preview(
    token: str, data: SessionUpdate, db: Session = Depends(get_db)
):
    """Validate session data before proceeding to preview"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate that required files are uploaded
    if not session.photo_s3_key:
        raise HTTPException(
            status_code=400, detail="Photo must be uploaded before customization"
        )

    if not session.audio_s3_key:
        raise HTTPException(
            status_code=400, detail="Audio file must be uploaded before customization"
        )

    # Validate that audio processing is complete
    if not session.waveform_s3_key:
        raise HTTPException(
            status_code=400,
            detail="Audio processing not complete. Please wait and try again.",
        )

    # Validate custom text for preview
    if not data.custom_text or data.custom_text.strip() == "":
        raise HTTPException(
            status_code=400, detail="Please enter some text for your poster"
        )

    if data.custom_text and len(data.custom_text.strip()) > 200:
        raise HTTPException(
            status_code=400,
            detail="Text is too long. Please keep it under 200 characters",
        )

    return {"status": "valid", "message": "Session is ready for preview"}


# File Upload Endpoints
@app.post("/api/session/{token}/photo", response_model=UploadResponse)
async def upload_photo(
    token: str, photo: UploadFile = File(...), db: Session = Depends(get_db), request: Request = None
):
    """Upload and process photo for the session"""
    # Rate limiting check
    if settings.is_rate_limit_enabled():
        await rate_limiter.check_upload_rate_limit(token)
        if request:
            await rate_limiter.check_burst_rate_limit(request)
            if await rate_limiter.is_banned(request):
                raise HTTPException(status_code=403, detail="Access temporarily restricted")

    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Basic file validation
    if not photo.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if photo.size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Advanced content filtering
    if settings.content_filter_enabled:
        validation_result = await content_filter.validate_upload(photo, "image")
        if not validation_result["is_valid"]:
            error_msg = "; ".join(validation_result["errors"])
            logger.warning(f"Photo upload blocked: {error_msg}")
            raise HTTPException(status_code=400, detail=f"File validation failed: {error_msg}")

        # Log any warnings
        for warning in validation_result.get("warnings", []):
            logger.info(f"Photo upload warning: {warning}")
    else:
        # Fallback to basic validation if content filtering is disabled
        if not photo.content_type or not photo.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="File must be an image (JPEG, PNG, etc.)"
            )

        if photo.size > settings.max_photo_size:
            raise HTTPException(status_code=400, detail=f"File too large (max {settings.max_photo_size // (1024*1024)}MB)")

        # Validate file extension
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        file_extension = os.path.splitext(photo.filename.lower())[1]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format. Allowed: {', '.join(allowed_extensions)}",
            )

    try:
        # Store photo temporarily for preview generation using FileUploader (S3)
        # Follow PRD naming: temp_photos/{session_token}.jpg
        temp_photo_key = f"temp_photos/{token}.jpg"

        # Upload with specific key name
        await file_uploader.upload_file_with_key(photo, temp_photo_key)

        # Update session with temporary key and file info
        session.photo_s3_key = temp_photo_key
        session.photo_filename = photo.filename
        session.photo_size = photo.size
        db.commit()

        # Get temporary URL for preview
        temp_photo_url = file_uploader.generate_presigned_url(
            temp_photo_key, expiration=3600
        )

        return UploadResponse(status="success", photo_url=temp_photo_url)

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"Photo upload error: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Photo upload failed: {str(e)}")


@app.post("/api/session/{token}/audio", response_model=UploadResponse)
async def upload_audio(
    token: str, audio: UploadFile = File(...), db: Session = Depends(get_db), request: Request = None
):
    """Upload and process audio for the session"""
    # Rate limiting check
    if settings.is_rate_limit_enabled():
        await rate_limiter.check_upload_rate_limit(token)
        if request:
            await rate_limiter.check_burst_rate_limit(request)
            if await rate_limiter.is_banned(request):
                raise HTTPException(status_code=403, detail="Access temporarily restricted")

    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Basic file validation
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file selected")

    if audio.size == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    # Advanced content filtering
    if settings.content_filter_enabled:
        validation_result = await content_filter.validate_upload(audio, "audio")
        if not validation_result["is_valid"]:
            error_msg = "; ".join(validation_result["errors"])
            logger.warning(f"Audio upload blocked: {error_msg}")
            raise HTTPException(status_code=400, detail=f"File validation failed: {error_msg}")

        # Log any warnings
        for warning in validation_result.get("warnings", []):
            logger.info(f"Audio upload warning: {warning}")
    else:
        # Fallback to basic validation if content filtering is disabled
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400, detail="File must be an audio file (MP3, WAV, etc.)"
            )

        if audio.size > settings.max_audio_size:
            raise HTTPException(status_code=400, detail=f"Audio file too large (max {settings.max_audio_size // (1024*1024)}MB)")

        # Validate file extension
        allowed_extensions = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm"}
        file_extension = os.path.splitext(audio.filename.lower())[1]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Allowed: {', '.join(allowed_extensions)}",
            )

        # Check minimum file size (at least 1KB)
        if audio.size < 1024:  # 1KB
            raise HTTPException(
                status_code=400, detail="Audio file too small (minimum 1KB)"
            )

    try:
        # Store audio temporarily for preview generation using FileUploader (S3)
        # Follow PRD naming: temp_audio/{session_token}.{extension}
        file_extension = os.path.splitext(audio.filename.lower())[1]
        temp_audio_key = f"temp_audio/{token}{file_extension}"

        # Upload with specific key name
        await file_uploader.upload_file_with_key(audio, temp_audio_key)

        # Update session with temporary key and file info
        session.audio_s3_key = temp_audio_key
        session.audio_filename = audio.filename
        session.audio_size = audio.size
        db.commit()

        # Start background audio processing with temporary file
        try:
            from .tasks import process_audio_task

            task_result = process_audio_task.delay(token, temp_audio_key)
            print(f"Audio processing task started: {task_result.id}")
        except Exception as task_error:
            print(f"Error starting audio processing task: {task_error}")
            # Continue anyway - the upload was successful

        return UploadResponse(status="success", waveform_processing="started")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")


@app.delete("/api/session/{token}/photo")
async def remove_photo(token: str, db: Session = Depends(get_db)):
    """Remove uploaded photo from session"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.photo_s3_key:
        raise HTTPException(status_code=404, detail="No photo found to remove")

    try:
        # Delete from S3
        file_uploader.delete_file(session.photo_s3_key)

        # Update session to remove photo reference and file info
        session.photo_s3_key = None
        session.photo_filename = None
        session.photo_size = None
        db.commit()

        return {"status": "success", "message": "Photo removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove photo: {str(e)}")


@app.delete("/api/session/{token}/audio")
async def remove_audio(token: str, db: Session = Depends(get_db)):
    """Remove uploaded audio from session"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.audio_s3_key:
        raise HTTPException(status_code=404, detail="No audio found to remove")

    try:
        # Delete audio file from S3
        file_uploader.delete_file(session.audio_s3_key)

        # Delete waveform file from S3 if it exists
        if session.waveform_s3_key:
            file_uploader.delete_file(session.waveform_s3_key)

        # Update session to remove audio and waveform references and file info
        session.audio_s3_key = None
        session.waveform_s3_key = None
        session.audio_duration = None
        session.audio_filename = None
        session.audio_size = None
        db.commit()

        return {"status": "success", "message": "Audio removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove audio: {str(e)}")


@app.get("/api/session/{token}/status", response_model=ProcessingStatus)
async def get_processing_status(token: str, db: Session = Depends(get_db)):
    """Check processing status for uploads"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return ProcessingStatus(
        photo_ready=session.photo_s3_key is not None,
        audio_ready=session.audio_s3_key is not None,
        waveform_ready=session.waveform_s3_key is not None,
        preview_ready=session.photo_s3_key is not None
        and session.waveform_s3_key is not None,
    )


# Preview Generation
@app.get("/api/session/{token}/preview")
async def get_preview(token: str, db: Session = Depends(get_db)):
    """Generate watermarked preview PDF"""
    print("=" * 100)
    print("🚨🚨🚨 PREVIEW REQUEST RECEIVED! 🚨🚨🚨")
    print(f"Token: {token}")
    print("=" * 100)
    session = session_manager.get_session(db, token)
    print(f"Session retrieved: {session is not None}")
    print(f"Session photo_shape: {session.photo_shape if session else 'N/A'}")
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Refresh session to ensure we have the latest data from database
    # This is important because Celery workers might have updated the session
    print(
        f"DEBUG: Session before refresh - custom_text: '{session.custom_text}', font_id: '{session.font_id}'"
    )
    db.refresh(session)
    print(
        f"DEBUG: Session after refresh - custom_text: '{session.custom_text}', font_id: '{session.font_id}'"
    )

    # Check detailed status with specific error messages
    if not session.photo_s3_key:
        raise HTTPException(
            status_code=400,
            detail="Please upload a photo first",
            headers={"X-Missing-Component": "photo"},
        )

    if not session.audio_s3_key:
        raise HTTPException(
            status_code=400,
            detail="Please upload audio first",
            headers={"X-Missing-Component": "audio"},
        )

    if not session.waveform_s3_key:
        # Audio is uploaded but waveform is still processing
        raise HTTPException(
            status_code=202,  # Accepted - processing
            detail="Audio waveform is still being generated. Please wait a moment and try again.",
            headers={
                "X-Processing-Status": "waveform_generating",
                "X-Retry-After": "5",  # Suggest retry in 5 seconds
            },
        )

    # Validate that files actually exist in S3 (all files now stored in S3)
    from .services.file_uploader import FileUploader

    file_uploader = FileUploader()

    # Check photo file existence in S3
    if not file_uploader.file_exists(session.photo_s3_key):
        raise HTTPException(
            status_code=400,
            detail="Photo file is missing. Please upload a new photo.",
            headers={"X-Missing-Component": "photo_file"},
        )

    # Check audio file existence in S3
    if not file_uploader.file_exists(session.audio_s3_key):
        raise HTTPException(
            status_code=400,
            detail="Audio file is missing. Please upload a new audio file.",
            headers={"X-Missing-Component": "audio_file"},
        )

    # Check waveform file existence (waveforms are always in S3)
    if not file_uploader.file_exists(session.waveform_s3_key):
        raise HTTPException(
            status_code=400,
            detail="Waveform file is missing. Please wait for audio processing to complete.",
            headers={"X-Missing-Component": "waveform_file"},
        )

    try:
        print(f"DEBUG: Starting preview generation for session {token}")
        print(
            f"DEBUG: Session data after refresh - photo_s3_key: {session.photo_s3_key}, audio_s3_key: {session.audio_s3_key}, waveform_s3_key: {session.waveform_s3_key}"
        )

        # Generate preview PDF with watermark
        print(f"DEBUG: Calling pdf_generator.generate_pdf with watermark")
        print(f"DEBUG: Session template_id: {session.template_id}")
        print(f"DEBUG: Session photo_shape: {session.photo_shape}")
        pdf_url = await pdf_generator.generate_pdf(session, add_watermark=True)
        print(f"DEBUG: PDF generation successful, URL: {pdf_url}")

        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        return {"preview_url": pdf_url, "expires_at": expires_at}

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"Preview generation error for session {token}: {error_trace}")
        print(
            f"Session state at error - photo_s3_key: {session.photo_s3_key}, audio_s3_key: {session.audio_s3_key}, waveform_s3_key: {session.waveform_s3_key}"
        )
        raise HTTPException(
            status_code=500, detail=f"Preview generation failed: {str(e)}"
        )


@app.get("/api/session/{token}/preview/image")
async def get_preview_image(token: str, db: Session = Depends(get_db)):
    """Generate watermarked preview as image for mobile devices"""
    print("=" * 100)
    print("🚨🚨🚨 MOBILE PREVIEW IMAGE REQUEST RECEIVED! 🚨🚨🚨")
    print("🚨🚨🚨 THIS IS STEP 2 - CUSTOMIZATION PREVIEW! 🚨🚨🚨")
    print(f"Token: {token}")
    print("=" * 100)

    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Refresh session to ensure we have the latest data from database
    db.refresh(session)

    # Validate that required files are uploaded
    if not session.photo_s3_key:
        raise HTTPException(
            status_code=400,
            detail="Photo file is missing. Please upload a photo first.",
            headers={"X-Missing-Component": "photo_file"},
        )

    if not session.audio_s3_key:
        raise HTTPException(
            status_code=400,
            detail="Audio file is missing. Please upload an audio file first.",
            headers={"X-Missing-Component": "audio_file"},
        )

    # Check waveform file existence (waveforms are always in S3)
    file_uploader = FileUploader()
    if not file_uploader.file_exists(session.waveform_s3_key):
        raise HTTPException(
            status_code=400,
            detail="Waveform file is missing. Please wait for audio processing to complete.",
            headers={"X-Missing-Component": "waveform_file"},
        )

    try:
        print(f"DEBUG: Starting mobile preview image generation for session {token}")
        print(f"DEBUG: Session keys - photo: {session.photo_s3_key}, audio: {session.audio_s3_key}, waveform: {session.waveform_s3_key}")

        # Generate preview PDF with watermark first
        print(f"DEBUG: Calling pdf_generator.generate_pdf with watermark")
        pdf_url = await pdf_generator.generate_pdf(session, add_watermark=True)
        print(f"DEBUG: PDF generation successful, URL: {pdf_url}")

        # Convert PDF to image for mobile preview
        print(f"DEBUG: Converting PDF to image")
        image_url = await pdf_generator.convert_pdf_to_image(pdf_url, session.session_token)
        print(f"DEBUG: Image conversion successful, URL: {image_url}")
        print(f"DEBUG: URL type check - contains presigned params: {'X-Amz-' in image_url}")
        print(f"DEBUG: URL type check - is public URL: {image_url.startswith('https://audioposter-bucket.s3.amazonaws.com/') and 'X-Amz-' not in image_url}")

        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        return {"preview_url": image_url, "expires_at": expires_at, "type": "image"}

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"❌ Mobile preview image generation error for session {token}:")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error message: {str(e)}")
        print(f"❌ Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=500, detail=f"Mobile preview generation failed: {str(e)}"
        )


# Payment & Orders
@app.post("/api/session/{token}/payment", response_model=PaymentIntentResponse)
async def create_payment_intent(
    token: str, request: PaymentIntentRequest, db: Session = Depends(get_db)
):
    """Create Stripe payment intent for poster purchase"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Create order record with configurable price (including discount)
        order_id = str(uuid.uuid4())
        pricing_info = config_service.get_discounted_price_cents(db)
        amount = pricing_info["discounted_price"]  # Use discounted price

        order = Order(
            id=order_id,
            email=request.email,
            amount_cents=amount,
            status="pending",
            download_token=str(uuid.uuid4()),
            download_expires_at=datetime.utcnow()
            + timedelta(days=7),  # 7 days for all users
            session_token=session.session_token,  # Bind order to session
        )
        db.add(order)
        db.commit()

        # Create Stripe payment intent
        payment_intent = stripe_service.create_payment_intent(
            amount=amount, email=request.email, order_id=order_id
        )

        # Update order with Stripe payment intent ID
        order.stripe_payment_intent_id = payment_intent["id"]
        db.commit()

        return PaymentIntentResponse(
            client_secret=payment_intent["client_secret"],
            amount=amount,
            order_id=order_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Payment creation failed: {str(e)}"
        )


@app.post("/api/orders/{order_id}/complete", response_model=DownloadResponse)
async def complete_order(
    order_id: str, request: CompleteOrderRequest, db: Session = Depends(get_db)
):
    """Complete order after successful payment"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate session ownership - ensure the session token matches the order
    if not order.session_token or order.session_token != request.session_token:
        raise HTTPException(
            status_code=403,
            detail="Session token does not match order. Unauthorized access attempt."
        )

    # Validate session is still valid
    session = session_manager.get_session(db, request.session_token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        # Verify payment with Stripe
        payment_intent = stripe_service.verify_payment(request.payment_intent_id)

        if payment_intent["status"] != "succeeded":
            raise HTTPException(status_code=400, detail="Payment not completed")

        # Update order status
        order.status = "completed"
        db.commit()

        # Generate final PDF without watermark
        # Note: session is already validated above

        # Validate that required files exist in S3 before generating final PDF
        from .services.file_uploader import FileUploader

        file_uploader = FileUploader()

        # Check photo file existence in S3
        if not session.photo_s3_key or not file_uploader.file_exists(
            session.photo_s3_key
        ):
            raise HTTPException(
                status_code=400,
                detail="Photo file is missing. Cannot generate final PDF.",
                headers={"X-Missing-Component": "photo_file"},
            )

        # Check audio file existence in S3
        if not session.audio_s3_key or not file_uploader.file_exists(
            session.audio_s3_key
        ):
            raise HTTPException(
                status_code=400,
                detail="Audio file is missing. Cannot generate final PDF.",
                headers={"X-Missing-Component": "audio_file"},
            )

        # Check waveform file existence in S3
        if not session.waveform_s3_key or not file_uploader.file_exists(
            session.waveform_s3_key
        ):
            raise HTTPException(
                status_code=400,
                detail="Waveform file is missing. Cannot generate final PDF.",
                headers={"X-Missing-Component": "waveform_file"},
            )

        # Migrate all temporary files to permanent storage
        try:
            print(f"Starting file migration for order {order_id}")
            permanent_keys = await storage_manager.migrate_all_session_files(
                session.session_token, order_id
            )

            # Update order with permanent file keys
            order.permanent_photo_s3_key = permanent_keys.get("permanent_photo_s3_key")
            order.permanent_audio_s3_key = permanent_keys.get("permanent_audio_s3_key")
            order.permanent_waveform_s3_key = permanent_keys.get(
                "permanent_waveform_s3_key"
            )
            order.session_token = session.session_token
            order.migration_status = "completed"
            order.migration_completed_at = datetime.utcnow()

            # Verify migration success
            permanent_file_keys = [
                order.permanent_photo_s3_key,
                order.permanent_audio_s3_key,
                order.permanent_waveform_s3_key,
            ]

            if not storage_manager.verify_migration_success(permanent_file_keys):
                raise Exception(
                    "Migration verification failed - not all files were successfully migrated"
                )

            db.commit()
            print(f"File migration completed successfully for order {order_id}")

        except Exception as e:
            error_msg = f"File migration failed for order {order_id}: {str(e)}"
            print(error_msg)

            # Update order with migration failure
            order.migration_status = "failed"
            order.migration_error = error_msg
            db.commit()

            # Rollback any partially migrated files
            try:
                permanent_file_keys = [
                    order.permanent_photo_s3_key,
                    order.permanent_audio_s3_key,
                    order.permanent_waveform_s3_key,
                ]
                await storage_manager.rollback_migration(permanent_file_keys)
            except Exception as rollback_error:
                print(f"Rollback failed for order {order_id}: {rollback_error}")

            # Don't continue with PDF generation if migration fails
            raise HTTPException(
                status_code=500,
                detail="File migration failed. Please try again or contact support.",
                headers={"X-Migration-Error": "true"},
            )

        pdf_url = await pdf_generator.generate_pdf(session, add_watermark=False, order=order)

        # Add email to subscribers if not exists
        subscriber = (
            db.query(EmailSubscriber)
            .filter(EmailSubscriber.email == order.email)
            .first()
        )
        if not subscriber:
            subscriber = EmailSubscriber(
                email=order.email,
                source="checkout",  # Track where the email came from
                data_processing_consent=True,  # Implicit consent through purchase
            )
            db.add(subscriber)

        db.commit()

        # Send download email
        await email_service.send_download_email(
            order.email, pdf_url, order.download_expires_at
        )

        return DownloadResponse(
            download_url=pdf_url,
            expires_at=order.download_expires_at.isoformat(),
            email_sent=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Order completion failed: {str(e)}"
        )


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events for payment processing

    This endpoint receives notifications from Stripe about payment events
    and updates order status accordingly. Must be configured in Stripe Dashboard.

    Webhook URL: https://vocaframe.com/api/stripe/webhook
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.error("Stripe webhook: Missing stripe-signature header")
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        # Verify webhook signature and construct event
        event = stripe_service.handle_webhook(payload, sig_header)

        logger.info(f"Stripe webhook received: {event['type']} - ID: {event['id']}")

        # Handle different event types
        event_type = event["type"]
        event_data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            # Payment was successful
            payment_intent_id = event_data["id"]
            logger.info(f"Payment succeeded: {payment_intent_id}")

            # Find and update the order
            order = db.query(Order).filter(
                Order.stripe_payment_intent_id == payment_intent_id
            ).first()

            if order:
                # Only update if not already completed (idempotency)
                if order.status != "completed":
                    order.status = "completed"
                    order.updated_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Order {order.id} marked as completed via webhook")

                    # Optional: Send confirmation email (if not already sent)
                    try:
                        if order.email and order.download_token:
                            session = db.query(SessionModel).filter(
                                SessionModel.session_token == order.session_token
                            ).first()

                            if session and order.pdf_s3_key:
                                download_url = f"{request.url_for('download_pdf', download_token=order.download_token)}"
                                email_service.send_download_email(
                                    order.email,
                                    download_url,
                                    order.download_expires_at
                                )
                                logger.info(f"Sent download email to {order.email}")
                    except Exception as email_error:
                        # Don't fail webhook if email fails
                        logger.error(f"Failed to send email in webhook: {email_error}")
                else:
                    logger.info(f"Order {order.id} already completed, skipping update")
            else:
                logger.warning(f"No order found for payment_intent: {payment_intent_id}")

        elif event_type == "payment_intent.payment_failed":
            # Payment failed
            payment_intent_id = event_data["id"]
            failure_message = event_data.get("last_payment_error", {}).get("message", "Unknown error")
            logger.warning(f"Payment failed: {payment_intent_id} - {failure_message}")

            # Find and update the order
            order = db.query(Order).filter(
                Order.stripe_payment_intent_id == payment_intent_id
            ).first()

            if order and order.status != "failed":
                order.status = "failed"
                order.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Order {order.id} marked as failed via webhook")

        elif event_type == "charge.refunded":
            # Payment was refunded
            charge = event_data
            payment_intent_id = charge.get("payment_intent")
            logger.info(f"Charge refunded for payment_intent: {payment_intent_id}")

            if payment_intent_id:
                order = db.query(Order).filter(
                    Order.stripe_payment_intent_id == payment_intent_id
                ).first()

                if order:
                    order.status = "refunded"
                    order.updated_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Order {order.id} marked as refunded via webhook")

        elif event_type == "payment_intent.canceled":
            # Payment was canceled
            payment_intent_id = event_data["id"]
            logger.info(f"Payment canceled: {payment_intent_id}")

            order = db.query(Order).filter(
                Order.stripe_payment_intent_id == payment_intent_id
            ).first()

            if order and order.status == "pending":
                order.status = "canceled"
                order.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Order {order.id} marked as canceled via webhook")

        elif event_type in [
            "payment_intent.created",
            "payment_intent.processing",
            "charge.succeeded",
            "payment_method.attached"
        ]:
            # Informational events - log but don't act on
            logger.info(f"Informational event: {event_type}")

        else:
            # Unknown/unhandled event type
            logger.info(f"Unhandled webhook event type: {event_type}")

        # Return success response to Stripe
        return {"status": "success", "event_type": event_type}

    except HTTPException:
        # Re-raise HTTP exceptions (signature verification failures)
        raise
    except Exception as e:
        # Log error but return 200 to prevent Stripe from retrying
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        # Return 200 to acknowledge receipt (prevents Stripe retry storms)
        return {"status": "error", "message": str(e)}


@app.get("/api/download/{download_token}")
async def download_pdf(download_token: str, db: Session = Depends(get_db)):
    """Download PDF using secure token"""
    # Validate download token access using file access validator
    order = file_access_validator.validate_download_token_access(db, download_token)

    # Return the PDF file
    # This would typically redirect to S3 or serve the file directly
    return {"message": "PDF download would be served here"}


# Permanent Audio Playback for QR Codes
@app.get("/listen/{identifier}", response_class=HTMLResponse)
async def listen_to_audio(identifier: str, db: Session = Depends(get_db)):
    """Permanent audio playback for QR codes - works forever"""
    print("🎵🎵🎵 LISTEN ENDPOINT CALLED! 🎵🎵🎵")
    print(f"🎵 Identifier: {identifier}")
    print("🎵🎵🎵 LISTEN ENDPOINT CALLED! 🎵🎵🎵")

    try:
        # Validate audio access using file access validator
        access_info = file_access_validator.validate_audio_playback_access(db, identifier)

        if access_info['type'] == 'order':
            # Paid poster - use permanent audio
            audio_url = permanent_audio_service.get_permanent_audio_url(
                access_info['object'], expiration=3600
            )
        else:
            # Preview poster - use session audio (may expire)
            audio_url = file_uploader.generate_presigned_url(
                access_info['audio_key'], expiration=3600
            )

        title = access_info['title']

        if not audio_url:
            raise HTTPException(status_code=404, detail="Audio file not accessible")

        # Return beautiful HTML audio player
        return HTMLResponse(
            f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>VocaFrame</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 1rem;
                }}

                .player-container {{
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 3rem 2rem;
                    max-width: 500px;
                    width: 100%;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                    text-align: center;
                    animation: fadeIn 0.8s ease-out;
                }}

                @keyframes fadeIn {{
                    from {{
                        opacity: 0;
                        transform: translateY(20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateY(0);
                    }}
                }}

                .logo {{
                    font-size: 3rem;
                    margin-bottom: 1rem;
                    animation: pulse 2s infinite;
                }}

                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.1); }}
                }}

                h1 {{
                    color: #333;
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                    font-weight: 600;
                }}

                .subtitle {{
                    color: #666;
                    font-size: 1.1rem;
                    margin-bottom: 2rem;
                }}

                audio {{
                    width: 100%;
                    margin: 2rem 0;
                    border-radius: 25px;
                    outline: none;
                }}

                .footer {{
                    color: #999;
                    font-size: 0.9rem;
                    margin-top: 2rem;
                    line-height: 1.4;
                }}

                .brand {{
                    color: #667eea;
                    font-weight: bold;
                    text-decoration: none;
                }}

                .brand:hover {{
                    color: #764ba2;
                }}

                @media (max-width: 600px) {{
                    .player-container {{
                        padding: 2rem 1.5rem;
                        margin: 1rem;
                    }}

                    h1 {{
                        font-size: 1.5rem;
                    }}

                    .logo {{
                        font-size: 2.5rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="player-container">
                <div class="logo">🎵</div>
                <h1>{title}</h1>
                <p class="subtitle">A special moment preserved forever</p>

                <audio controls autoplay preload="auto">
                    <source src="{audio_url}" type="audio/mpeg">
                    <source src="{audio_url}" type="audio/wav">
                    <source src="{audio_url}" type="audio/ogg">
                    Your browser does not support the audio element.
                </audio>

                <div class="footer">
                    <p>This memory was preserved for you by</p>
                    <a href="https://vocaframe.com" class="brand">VocaFrame</a>
                    <p style="margin-top: 1rem; font-size: 0.8rem;">
                        💡 Tip: Bookmark this page to keep this memory accessible
                    </p>
                </div>
            </div>

            <script>
                // Auto-retry audio loading if it fails
                const audio = document.querySelector('audio');
                audio.addEventListener('error', function() {{
                    console.log('Audio failed to load, retrying...');
                    setTimeout(() => {{
                        audio.load();
                    }}, 1000);
                }});

                // Track plays for analytics (optional)
                audio.addEventListener('play', function() {{
                    console.log('Audio started playing');
                }});
            </script>
        </body>
        </html>
        """
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio playback failed: {str(e)}")


@app.get("/api/audio/{order_id}")
async def get_audio_file(order_id: str, db: Session = Depends(get_db)):
    """Direct audio file access with presigned URL redirect"""

    try:
        # Validate order file access using file access validator
        order = file_access_validator.validate_order_file_access(db, order_id, "audio")

        # Generate fresh presigned URL
        audio_url = permanent_audio_service.get_permanent_audio_url(
            order, expiration=3600
        )

        if not audio_url:
            raise HTTPException(status_code=404, detail="Audio file not accessible")

        # Redirect to presigned URL
        return RedirectResponse(url=audio_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio access failed: {str(e)}")


# Template Management
@app.get("/api/templates")
async def get_templates():
    """Get all available templates"""
    try:
        templates = template_service.get_all_templates()
        return {
            "templates": templates,
            "available_ids": template_service.list_available_templates(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get templates: {str(e)}"
        )


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get specific template configuration"""
    try:
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@app.put("/api/session/{token}/template")
async def update_session_template(
    token: str, template_id: str, db: Session = Depends(get_db)
):
    """Update session template ID"""
    try:
        session = session_manager.get_session(db, token)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify template exists
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=400, detail=f"Template '{template_id}' not found"
            )

        # Update template ID
        session.template_id = template_id
        db.commit()

        return {
            "message": f"Template updated to {template_id}",
            "template_id": template_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update template: {str(e)}"
        )


# Privacy Compliance Endpoints
@app.get("/api/unsubscribe")
async def unsubscribe_page():
    """Serve unsubscribe page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Unsubscribe - VocaFrame</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .container { background: #f9fafb; padding: 30px; border-radius: 10px; }
            .success { color: #059669; }
            .error { color: #dc2626; }
            .btn { background: #8b5cf6; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Unsubscribe from VocaFrame</h1>
            <div id="content">
                <p>We're sorry to see you go! You can unsubscribe from our emails below.</p>
                <form id="unsubscribeForm">
                    <label for="email">Email Address:</label><br>
                    <input type="email" id="email" name="email" required style="width: 100%; padding: 10px; margin: 10px 0;"><br>
                    <button type="submit" class="btn">Unsubscribe</button>
                </form>
            </div>
        </div>
        <script>
            document.getElementById('unsubscribeForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const urlParams = new URLSearchParams(window.location.search);
                const token = urlParams.get('token');

                try {
                    const response = await fetch('/api/unsubscribe/confirm', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: email, token: token})
                    });

                    const result = await response.json();
                    document.getElementById('content').innerHTML =
                        '<p class="success">' + result.message + '</p>';
                } catch (error) {
                    document.getElementById('content').innerHTML =
                        '<p class="error">An error occurred. Please try again.</p>';
                }
            });
        </script>
    </body>
    </html>
    """)


@app.post("/api/unsubscribe/confirm")
async def confirm_unsubscribe(request: dict, db: Session = Depends(get_db)):
    """Confirm unsubscribe request"""
    try:
        email = request.get("email")
        token = request.get("token")

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Verify token if provided
        if token and not privacy_service.verify_unsubscribe_token(email, token):
            raise HTTPException(status_code=400, detail="Invalid unsubscribe token")

        # Unsubscribe the email
        success = privacy_service.unsubscribe_email(email, db)

        if success:
            return {"message": f"Successfully unsubscribed {email} from AudioPoster emails."}
        else:
            raise HTTPException(status_code=500, detail="Failed to unsubscribe email")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unsubscribe failed: {str(e)}")


@app.post("/api/privacy/data-cleanup")
async def cleanup_expired_data(
    db: Session = Depends(get_db),
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Clean up expired session data (admin endpoint)"""
    try:
        deleted_count = privacy_service.cleanup_expired_data(db)
        return {
            "message": f"Successfully cleaned up {deleted_count} expired sessions",
            "deleted_sessions": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data cleanup failed: {str(e)}")


@app.get("/api/privacy/data-retention")
async def get_data_retention_info():
    """Get information about data retention policies"""
    try:
        return privacy_service.get_data_retention_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get retention info: {str(e)}")


# Security and Monitoring Endpoints
@app.get("/api/security/rate-limit-status")
async def get_rate_limit_status(request: Request):
    """Get current rate limit status for monitoring"""
    try:
        return await rate_limiter.get_rate_limit_status(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit status: {str(e)}")


@app.get("/api/security/content-filter-status")
async def get_content_filter_status():
    """Get current content filter status for monitoring"""
    try:
        return await content_filter.get_filter_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content filter status: {str(e)}")


@app.post("/api/security/cleanup-rate-limits")
async def cleanup_rate_limits(
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Clean up expired rate limit entries (admin endpoint)"""
    try:
        await rate_limiter.cleanup_expired_entries()
        return {"message": "Rate limit cleanup completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rate limit cleanup failed: {str(e)}")


# GDPR Compliance Endpoints

@app.post("/api/gdpr/consent")
async def collect_consent(
    user_identifier: str = Form(...),
    consent_type: str = Form(...),
    consent_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """Collect user consent for GDPR compliance"""
    try:
        # Parse consent data
        consent_info = json.loads(consent_data)

        # Validate consent type
        try:
            consent_type_enum = ConsentType(consent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid consent type: {consent_type}")

        # Collect consent
        result = consent_manager.collect_consent(
            user_identifier,
            consent_type_enum,
            consent_info,
            db
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid consent data format")
    except Exception as e:
        logger.error(f"Error collecting consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to collect consent: {str(e)}")


@app.delete("/api/gdpr/consent")
async def withdraw_consent(
    user_identifier: str = Form(...),
    consent_type: str = Form(...),
    withdrawal_reason: str = Form(""),
    db: Session = Depends(get_db)
):
    """Withdraw user consent for GDPR compliance"""
    try:
        # Validate consent type
        try:
            consent_type_enum = ConsentType(consent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid consent type: {consent_type}")

        # Withdraw consent
        result = consent_manager.withdraw_consent(
            user_identifier,
            consent_type_enum,
            withdrawal_reason,
            db
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])

    except Exception as e:
        logger.error(f"Error withdrawing consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to withdraw consent: {str(e)}")


@app.get("/api/gdpr/consent/{user_identifier}")
async def get_consent_status(
    user_identifier: str,
    consent_type: str = None,
    db: Session = Depends(get_db)
):
    """Get consent status for a user"""
    try:
        if consent_type:
            # Get specific consent type
            try:
                consent_type_enum = ConsentType(consent_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid consent type: {consent_type}")

            result = consent_manager.get_consent_status(user_identifier, consent_type_enum, db)
        else:
            # Get all consents
            result = consent_manager.get_all_consents(user_identifier, db)

        return result

    except Exception as e:
        logger.error(f"Error getting consent status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get consent status: {str(e)}")


@app.get("/api/gdpr/data/{user_identifier}")
async def get_user_data(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """Right to Access - Get all personal data for a user"""
    try:
        result = gdpr_service.get_user_data(user_identifier, db)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user data: {str(e)}")


@app.get("/api/gdpr/export/{user_identifier}")
async def export_user_data(
    user_identifier: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Right to Data Portability - Export user data in portable format"""
    try:
        result = gdpr_service.export_user_data(user_identifier, db)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])

        if format == "zip":
            from fastapi.responses import Response
            return Response(
                content=result["zip_export"],
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=gdpr_export_{user_identifier}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
                }
            )
        else:
            return result["export_data"]

    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export user data: {str(e)}")


@app.delete("/api/gdpr/data/{user_identifier}")
async def erase_user_data(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """Right to Erasure - Delete all personal data for a user"""
    try:
        result = gdpr_service.erase_user_data(user_identifier, db)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Error erasing user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to erase user data: {str(e)}")


@app.put("/api/gdpr/data/{user_identifier}")
async def rectify_user_data(
    user_identifier: str,
    corrections: dict,
    db: Session = Depends(get_db)
):
    """Right to Rectification - Correct inaccurate personal data"""
    try:
        result = gdpr_service.rectify_user_data(user_identifier, corrections, db)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except Exception as e:
        logger.error(f"Error rectifying user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rectify user data: {str(e)}")


@app.get("/api/gdpr/processing-info")
async def get_data_processing_info():
    """Get information about data processing activities"""
    try:
        return gdpr_service.get_data_processing_info()
    except Exception as e:
        logger.error(f"Error getting data processing info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get data processing info: {str(e)}")


@app.get("/api/gdpr/consent-statistics")
async def get_consent_statistics(
    db: Session = Depends(get_db),
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Get consent statistics for monitoring (admin endpoint)"""
    try:
        return consent_manager.get_consent_statistics(db)
    except Exception as e:
        logger.error(f"Error getting consent statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get consent statistics: {str(e)}")


@app.post("/api/gdpr/cleanup-consents")
async def cleanup_expired_consents(
    db: Session = Depends(get_db),
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Clean up expired consent records (admin endpoint)"""
    try:
        cleaned_count = consent_manager.cleanup_expired_consents(db)
        return {
            "message": f"Cleaned up {cleaned_count} expired consent records",
            "cleaned_count": cleaned_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up expired consents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired consents: {str(e)}")

# Data Minimization Endpoints

@app.post("/api/gdpr/data-minimization/validate")
async def validate_data_minimization(
    session_data: dict,
    processing_purposes: list[str],
    db: Session = Depends(get_db)
):
    """Validate data collection against minimization principles"""
    try:
        # Convert string purposes to enums
        purposes = [ProcessingPurpose(p) for p in processing_purposes]

        # Identify data categories
        data_categories = data_minimization_service._identify_data_categories(session_data)

        # Validate data collection
        validation_result = data_minimization_service.validate_data_collection(
            data_categories, purposes
        )

        return {
            "is_valid": validation_result.is_valid,
            "compliance_score": validation_result.score,
            "violations": validation_result.violations,
            "recommendations": validation_result.recommendations,
            "data_categories": [c.value for c in data_categories],
            "processing_purposes": [p.value for p in purposes]
        }
    except Exception as e:
        logger.error(f"Error validating data minimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate data minimization: {str(e)}")

@app.get("/api/gdpr/data-minimization/audit/{user_identifier}")
async def audit_data_minimization(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """Audit data processing for minimization compliance"""
    try:
        # Get user data
        user_data = gdpr_service.get_user_data(user_identifier, db)

        # Define processing purposes
        purposes = [
            ProcessingPurpose.SERVICE_DELIVERY,
            ProcessingPurpose.EMAIL_COMMUNICATIONS,
            ProcessingPurpose.ANALYTICS
        ]

        # Audit data processing
        audit_results = data_minimization_service.audit_data_processing(
            user_data, purposes
        )

        return audit_results
    except Exception as e:
        logger.error(f"Error auditing data minimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to audit data minimization: {str(e)}")

@app.get("/api/gdpr/data-minimization/recommendations")
async def get_minimization_recommendations():
    """Get general data minimization recommendations"""
    try:
        return {
            "recommendations": [
                "Only collect data that is necessary for service delivery",
                "Implement data retention policies with automatic cleanup",
                "Anonymize or pseudonymize data where possible",
                "Provide users with granular consent options",
                "Regularly audit data collection practices",
                "Use data minimization by design principles",
                "Implement purpose limitation for data processing",
                "Provide clear data processing information to users"
            ],
            "best_practices": [
                "Collect data only when explicitly needed",
                "Use the least invasive data collection methods",
                "Implement automatic data deletion after retention periods",
                "Provide users with data control options",
                "Regularly review and update data collection practices",
                "Document the legal basis for all data processing",
                "Implement privacy by design principles",
                "Conduct regular privacy impact assessments"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting minimization recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

# File Audit Logging Endpoints

@app.get("/api/audit/file-operations")
async def get_file_audit_logs(
    user_identifier: str = None,
    session_token: str = None,
    operation_type: str = None,
    file_type: str = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Get file operation audit logs (admin endpoint)"""
    try:
        # Parse dates
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Convert string enums to enum objects
        operation_type_enum = None
        if operation_type:
            try:
                operation_type_enum = FileOperationType(operation_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid operation type: {operation_type}")

        file_type_enum = None
        if file_type:
            try:
                file_type_enum = FileType(file_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")

        status_enum = None
        if status:
            try:
                status_enum = FileOperationStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        logs = file_audit_logger.get_audit_logs(
            db=db,
            user_identifier=user_identifier,
            session_token=session_token,
            operation_type=operation_type_enum,
            file_type=file_type_enum,
            status=status_enum,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=limit,
            offset=offset
        )

        return {
            "logs": logs,
            "count": len(logs),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error getting file audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@app.get("/api/audit/file-operations/statistics")
async def get_file_audit_statistics(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Get file operation audit statistics (admin endpoint)"""
    try:
        # Parse dates
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        statistics = file_audit_logger.get_audit_statistics(
            db=db,
            start_date=start_datetime,
            end_date=end_datetime
        )

        return statistics

    except Exception as e:
        logger.error(f"Error getting file audit statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit statistics: {str(e)}")

@app.post("/api/audit/file-operations/cleanup")
async def cleanup_old_audit_logs(
    db: Session = Depends(get_db),
    admin_auth: bool = admin_auth_service.get_admin_dependency()
):
    """Clean up old audit logs (admin endpoint)"""
    try:
        cleaned_count = file_audit_logger.cleanup_old_logs(db)

        return {
            "message": f"Cleaned up {cleaned_count} old audit logs",
            "cleaned_count": cleaned_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup audit logs: {str(e)}")


# Public API endpoints for accessing admin-managed resources
@app.get("/api/resources/fonts")
async def get_available_fonts(db: Session = Depends(get_db)):
    """Get all active fonts available for use"""
    try:
        fonts = admin_resource_service.get_active_fonts(db)
        return {"fonts": fonts}
    except Exception as e:
        logger.error(f"Error getting fonts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get fonts")


@app.get("/api/resources/fonts/{font_id}/file")
async def get_font_file(font_id: str, db: Session = Depends(get_db)):
    """Serve font file for dynamic loading"""
    try:
        # Get font file path from admin resource service
        font_file_path = admin_resource_service.get_font_file_path(db, font_id)

        if not font_file_path or not os.path.exists(font_file_path):
            raise HTTPException(status_code=404, detail="Font file not found")

        # Return the font file
        return FileResponse(
            font_file_path,
            media_type="font/ttf",
            filename=f"{font_id}.ttf",
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "Access-Control-Allow-Origin": "*"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving font file {font_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve font file")


@app.get("/api/resources/suggested-texts")
async def get_suggested_texts(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get suggested texts, optionally filtered by category"""
    try:
        texts = admin_resource_service.get_active_suggested_texts(db, category)
        return {"suggested_texts": texts}
    except Exception as e:
        logger.error(f"Error getting suggested texts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get suggested texts")


@app.get("/api/resources/backgrounds")
async def get_backgrounds(
    category: Optional[str] = None,
    orientation: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get backgrounds, optionally filtered by category and orientation"""
    try:
        backgrounds = admin_resource_service.get_active_backgrounds(db, category, orientation)
        return {"backgrounds": backgrounds}
    except Exception as e:
        logger.error(f"Error getting backgrounds: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get backgrounds")


@app.get("/api/resources/categories")
async def get_resource_categories(
    resource_type: str,
    db: Session = Depends(get_db)
):
    """Get all categories for a resource type"""
    try:
        categories = admin_resource_service.get_categories(db, resource_type)
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get categories")


# Removed audio-not-found and audio-error endpoints
# These were causing wrong fallback URLs in QR codes
# Now the system properly validates files and throws errors instead

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
