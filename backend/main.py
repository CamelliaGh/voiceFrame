import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

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
from .services.email_service import EmailService
from .services.privacy_service import PrivacyService
from .services.file_uploader import FileUploader
from .services.image_processor import ImageProcessor
from .services.pdf_generator import PDFGenerator
from .services.permanent_audio_service import PermanentAudioService
from .services.session_manager import SessionManager
from .services.storage_manager import StorageManager
from .services.stripe_service import StripeService
from .services.visual_template_service import VisualTemplateService

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

# Initialize services
session_manager = SessionManager()
file_uploader = FileUploader()
audio_processor = AudioProcessor()
image_processor = ImageProcessor()
pdf_generator = PDFGenerator()
stripe_service = StripeService()
email_service = EmailService()
privacy_service = PrivacyService()
permanent_audio_service = PermanentAudioService()
template_service = VisualTemplateService()


@app.get("/")
async def root():
    return {"message": "AudioPoster API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Session Management
@app.post("/api/session", response_model=SessionResponse)
async def create_session(db: Session = Depends(get_db)):
    """Create a new session for file uploads and customization"""
    try:
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)

        session = SessionModel(session_token=session_token, expires_at=expires_at)
        db.add(session)
        db.commit()
        db.refresh(session)

        return SessionResponse(
            session_token=session_token, expires_at=expires_at.isoformat()
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

    return SessionResponse(
        session_token=session.session_token,
        expires_at=session.expires_at.isoformat(),
        custom_text=session.custom_text,
        photo_shape=session.photo_shape,
        pdf_size=session.pdf_size,
        template_id=session.template_id,
        photo_url=session.photo_s3_key,
        waveform_url=session.waveform_s3_key,
        audio_duration=session.audio_duration,
    )


@app.put("/api/session/{token}")
async def update_session(
    token: str, data: SessionUpdate, db: Session = Depends(get_db)
):
    """Update session customization data"""
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

    # Validate that audio processing is complete
    if not session.waveform_s3_key:
        raise HTTPException(
            status_code=400,
            detail="Audio processing not complete. Please wait and try again.",
        )

    try:
        update_data = data.model_dump(exclude_unset=True)
        print(f"DEBUG: Update data after exclude_unset: {update_data}")
        print(
            f"DEBUG: Session before update - custom_text: '{session.custom_text}', font_id: '{session.font_id}'"
        )
        session_manager.update_session(db, session, update_data)
        print(
            f"DEBUG: Session after update - custom_text: '{session.custom_text}', font_id: '{session.font_id}'"
        )
        return {"status": "updated"}
    except ValueError as e:
        print(f"DEBUG: ValueError in update_session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG: Unexpected error in update_session: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
    token: str, photo: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload and process photo for the session"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate file
    if not photo.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if photo.size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="File must be an image (JPEG, PNG, etc.)"
        )

    if photo.size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

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

        # Update session with temporary key
        session.photo_s3_key = temp_photo_key
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
    token: str, audio: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Upload and process audio for the session"""
    session = session_manager.get_session(db, token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate file
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file selected")

    if audio.size == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400, detail="File must be an audio file (MP3, WAV, etc.)"
        )

    if audio.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=400, detail="Audio file too large (max 100MB)")

    # Validate file extension
    allowed_extensions = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
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

        # Update session with temporary key
        session.audio_s3_key = temp_audio_key
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
    session = session_manager.get_session(db, token)
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
        print(f"DEBUG: Calling pdf_generator.generate_preview_pdf")
        print(f"DEBUG: Session template_id: {session.template_id}")
        pdf_url = await pdf_generator.generate_preview_pdf(session)
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
        # Create order record with fixed price
        order_id = str(uuid.uuid4())
        amount = 299  # Fixed price: $2.99

        order = Order(
            id=order_id,
            email=request.email,
            amount_cents=amount,
            status="pending",
            download_token=str(uuid.uuid4()),
            download_expires_at=datetime.utcnow()
            + timedelta(days=7),  # 7 days for all users
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

    try:
        # Verify payment with Stripe
        payment_intent = stripe_service.verify_payment(request.payment_intent_id)

        if payment_intent["status"] != "succeeded":
            raise HTTPException(status_code=400, detail="Payment not completed")

        # Update order status
        order.status = "completed"
        db.commit()

        # Generate final PDF without watermark
        session = session_manager.get_session_by_order(db, order_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found for order")

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

        pdf_url = await pdf_generator.generate_final_pdf(session, order)

        # Add email to subscribers if not exists
        subscriber = (
            db.query(EmailSubscriber)
            .filter(EmailSubscriber.email == order.email)
            .first()
        )
        if not subscriber:
            subscriber = EmailSubscriber(
                email=order.email,
                first_purchase_date=datetime.utcnow(),
                total_purchases=1,
                total_spent_cents=order.amount_cents,
            )
            db.add(subscriber)
        else:
            subscriber.total_purchases += 1
            subscriber.total_spent_cents += order.amount_cents

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


@app.get("/api/download/{download_token}")
async def download_pdf(download_token: str, db: Session = Depends(get_db)):
    """Download PDF using secure token"""
    order = db.query(Order).filter(Order.download_token == download_token).first()
    if not order:
        raise HTTPException(status_code=404, detail="Download not found")

    if order.download_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Download link expired")

    # Return the PDF file
    # This would typically redirect to S3 or serve the file directly
    return {"message": "PDF download would be served here"}


# Permanent Audio Playback for QR Codes
@app.get("/listen/{identifier}", response_class=HTMLResponse)
async def listen_to_audio(identifier: str, db: Session = Depends(get_db)):
    """Permanent audio playback for QR codes - works forever"""

    try:
        # First try to find by order ID (paid posters)
        order = (
            db.query(Order)
            .filter(Order.id == identifier, Order.status == "completed")
            .first()
        )

        if order and order.permanent_audio_s3_key:
            # Paid poster - use permanent audio
            audio_url = permanent_audio_service.get_permanent_audio_url(
                order, expiration=3600
            )
            title = "Your AudioPoster Memory"
        else:
            # Try as session token (preview)
            session = session_manager.get_session(db, identifier)
            if session and session.audio_s3_key:
                # Preview poster - use session audio (may expire)
                audio_url = file_uploader.generate_presigned_url(
                    session.audio_s3_key, expiration=3600
                )
                title = "AudioPoster Preview"
            else:
                raise HTTPException(status_code=404, detail="Audio not found")

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
            <title>AudioPoster Memory</title>
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
                    <a href="https://audioposter.com" class="brand">AudioPoster</a>
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
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.status == "completed")
            .first()
        )

        if not order or not order.permanent_audio_s3_key:
            raise HTTPException(status_code=404, detail="Audio not found")

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
        <title>Unsubscribe - AudioPoster</title>
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
            <h1>Unsubscribe from AudioPoster</h1>
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
async def cleanup_expired_data(db: Session = Depends(get_db)):
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


# Removed audio-not-found and audio-error endpoints
# These were causing wrong fallback URLs in QR codes
# Now the system properly validates files and throws errors instead

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
