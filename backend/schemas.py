from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime

class SessionResponse(BaseModel):
    session_token: str
    expires_at: str
    custom_text: Optional[str] = None
    photo_shape: Optional[Literal['square', 'circle']] = 'square'
    pdf_size: Optional[Literal['A4', 'Letter', 'A3']] = 'A4'
    template_id: Optional[str] = 'classic'
    photo_url: Optional[str] = None
    waveform_url: Optional[str] = None
    audio_duration: Optional[float] = None

class SessionUpdate(BaseModel):
    custom_text: Optional[str] = None
    photo_shape: Optional[Literal['square', 'circle']] = None
    pdf_size: Optional[Literal['A4', 'Letter', 'A3']] = None
    template_id: Optional[str] = None

class UploadResponse(BaseModel):
    status: Literal['success', 'error']
    message: Optional[str] = None
    photo_url: Optional[str] = None
    duration: Optional[float] = None
    waveform_processing: Optional[Literal['started', 'completed']] = None

class ProcessingStatus(BaseModel):
    photo_ready: bool
    audio_ready: bool
    waveform_ready: bool
    preview_ready: bool

class PaymentIntentRequest(BaseModel):
    email: EmailStr
    tier: Literal['download'] = 'download'

class PaymentIntentResponse(BaseModel):
    client_secret: str
    amount: int
    order_id: str

class CompleteOrderRequest(BaseModel):
    payment_intent_id: str

class DownloadResponse(BaseModel):
    download_url: str
    expires_at: str
    email_sent: bool

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
