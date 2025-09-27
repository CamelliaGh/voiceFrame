from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SessionResponse(BaseModel):
    session_token: str
    expires_at: str
    custom_text: Optional[str] = None
    photo_shape: Optional[Literal["square", "circle"]] = "square"
    pdf_size: Optional[
        Literal[
            "A4", "A4_Landscape", "Letter", "Letter_Landscape", "A3", "A3_Landscape"
        ]
    ] = "A4"
    template_id: Optional[str] = "framed_a4_portrait"
    background_id: Optional[str] = "none"
    font_id: Optional[str] = "script"
    photo_url: Optional[str] = None
    waveform_url: Optional[str] = None
    audio_duration: Optional[float] = None


class SessionUpdate(BaseModel):
    custom_text: Optional[str] = Field(
        None, max_length=200, description="Custom text for the poster"
    )
    photo_shape: Optional[Literal["square", "circle"]] = Field(
        None, description="Photo shape preference"
    )
    pdf_size: Optional[
        Literal[
            "A4", "A4_Landscape", "Letter", "Letter_Landscape", "A3", "A3_Landscape"
        ]
    ] = Field(None, description="PDF page size")
    template_id: Optional[str] = Field(None, description="Template identifier")
    background_id: Optional[str] = Field(None, description="Background identifier")
    font_id: Optional[str] = Field(None, description="Font identifier")

    @field_validator("custom_text")
    @classmethod
    def validate_custom_text(cls, v):
        if v is not None:
            # Remove leading/trailing whitespace
            v = v.strip()
            if len(v) > 200:
                raise ValueError("Custom text too long (max 200 characters)")
            # Check for only whitespace (but allow empty string for initial state)
            if v and v.isspace():
                raise ValueError("Custom text cannot be only whitespace")
        return v

    @field_validator("template_id")
    @classmethod
    def validate_template_id(cls, v):
        if v is not None:
            valid_templates = [
                "classic",
                "elegant",
                "vintage",
                "modern",
                "framed",
                "framed_a4_landscape",
                "framed_a4_portrait",
                "framed_letter_landscape",
                "framed_letter_portrait",
                "framed_a3_landscape",
                "framed_a3_portrait",
            ]
            if v not in valid_templates:
                raise ValueError(
                    f'Invalid template. Must be one of: {", ".join(valid_templates)}'
                )
        return v

    @field_validator("background_id")
    @classmethod
    def validate_background_id(cls, v):
        if v is not None:
            valid_backgrounds = [
                "none",
                "abstract-blurred",
                "roses-wooden",
                "cute-hearts",
                "flat-lay-hearts",
            ]
            if v not in valid_backgrounds:
                raise ValueError(
                    f'Invalid background. Must be one of: {", ".join(valid_backgrounds)}'
                )
        return v

    @field_validator("font_id")
    @classmethod
    def validate_font_id(cls, v):
        if v is not None:
            valid_fonts = ["script", "elegant", "modern", "vintage", "classic"]
            if v not in valid_fonts:
                raise ValueError(
                    f'Invalid font. Must be one of: {", ".join(valid_fonts)}'
                )
        return v

    @field_validator("photo_shape")
    @classmethod
    def validate_photo_shape(cls, v):
        if v is not None and v not in ["square", "circle"]:
            raise ValueError('Photo shape must be either "square" or "circle"')
        return v

    @field_validator("pdf_size")
    @classmethod
    def validate_pdf_size(cls, v):
        if v is not None and v not in [
            "A4",
            "A4_Landscape",
            "Letter",
            "Letter_Landscape",
            "A3",
            "A3_Landscape",
        ]:
            raise ValueError(
                f"Invalid PDF size: {v}. Must be one of: A4, A4_Landscape, Letter, Letter_Landscape, A3, A3_Landscape"
            )
        return v


class UploadResponse(BaseModel):
    status: Literal["success", "error"]
    message: Optional[str] = None
    photo_url: Optional[str] = None
    duration: Optional[float] = None
    waveform_processing: Optional[Literal["started", "completed"]] = None


class ProcessingStatus(BaseModel):
    photo_ready: bool
    audio_ready: bool
    waveform_ready: bool
    preview_ready: bool


class PaymentIntentRequest(BaseModel):
    email: EmailStr
    tier: Literal["download"] = "download"


class PaymentIntentResponse(BaseModel):
    client_secret: str
    amount: int
    order_id: str


class CompleteOrderRequest(BaseModel):
    payment_intent_id: str
    session_token: str  # Required for payment-session binding validation


class DownloadResponse(BaseModel):
    download_url: str
    expires_at: str
    email_sent: bool


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# Admin Dashboard Schemas
class AdminFontCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_premium: bool = False


class AdminFontUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None


class AdminFontResponse(BaseModel):
    id: str
    name: str
    display_name: str
    file_path: str
    file_size: Optional[int]
    is_active: bool
    is_premium: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminSuggestedTextCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    is_premium: bool = False


class AdminSuggestedTextUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None


class AdminSuggestedTextResponse(BaseModel):
    id: str
    text: str
    category: Optional[str]
    is_active: bool
    is_premium: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminBackgroundCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    is_premium: bool = False


class AdminBackgroundUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None


class AdminBackgroundResponse(BaseModel):
    id: str
    name: str
    display_name: str
    file_path: str
    file_size: Optional[int]
    is_active: bool
    is_premium: bool
    description: Optional[str]
    category: Optional[str]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminResourceListResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    total_pages: int
