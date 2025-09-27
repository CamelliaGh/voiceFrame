"""
Admin Dashboard API Routes

Provides CRUD operations for managing fonts, suggested texts, and backgrounds.
Protected by admin authentication.
"""

import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import AdminFont, AdminSuggestedText, AdminBackground
from ..schemas import (
    AdminFontCreate,
    AdminFontUpdate,
    AdminFontResponse,
    AdminSuggestedTextCreate,
    AdminSuggestedTextUpdate,
    AdminSuggestedTextResponse,
    AdminBackgroundCreate,
    AdminBackgroundUpdate,
    AdminBackgroundResponse,
    AdminResourceListResponse,
)
from ..services.admin_auth import AdminAuthService

# Initialize admin auth service
admin_auth = AdminAuthService()

router = APIRouter(prefix="/admin", tags=["admin"])

# Font Management Endpoints
@router.get("/fonts", response_model=AdminResourceListResponse)
async def list_fonts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_premium: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """List all fonts with pagination and filtering"""
    query = db.query(AdminFont)

    if search:
        query = query.filter(
            AdminFont.name.ilike(f"%{search}%") |
            AdminFont.display_name.ilike(f"%{search}%")
        )

    if is_active is not None:
        query = query.filter(AdminFont.is_active == is_active)

    if is_premium is not None:
        query = query.filter(AdminFont.is_premium == is_premium)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return AdminResourceListResponse(
        items=[AdminFontResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


@router.post("/fonts", response_model=AdminFontResponse)
async def create_font(
    font_data: AdminFontCreate,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Create a new font entry"""
    # Check if font name already exists
    existing_font = db.query(AdminFont).filter(AdminFont.name == font_data.name).first()
    if existing_font:
        raise HTTPException(status_code=400, detail="Font name already exists")

    font = AdminFont(
        name=font_data.name,
        display_name=font_data.display_name,
        description=font_data.description,
        is_premium=font_data.is_premium,
        file_path="",  # Will be set when file is uploaded
    )

    db.add(font)
    db.commit()
    db.refresh(font)

    return AdminFontResponse.model_validate(font)


@router.post("/fonts/{font_id}/upload")
async def upload_font_file(
    font_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Upload font file for a font entry"""
    # Validate font exists
    font = db.query(AdminFont).filter(AdminFont.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")

    # Validate file type
    if not file.filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only TTF, OTF, WOFF, and WOFF2 files are allowed")

    # Create fonts directory if it doesn't exist
    fonts_dir = "fonts/admin"
    os.makedirs(fonts_dir, exist_ok=True)

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{font.name}_{uuid.uuid4().hex[:8]}{file_extension}"
    file_path = os.path.join(fonts_dir, filename)

    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Update font record
    font.file_path = file_path
    font.file_size = len(content)
    db.commit()

    return {"message": "Font file uploaded successfully", "file_path": file_path}


@router.get("/fonts/{font_id}", response_model=AdminFontResponse)
async def get_font(
    font_id: str,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Get a specific font by ID"""
    font = db.query(AdminFont).filter(AdminFont.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")

    return AdminFontResponse.model_validate(font)


@router.put("/fonts/{font_id}", response_model=AdminFontResponse)
async def update_font(
    font_id: str,
    font_data: AdminFontUpdate,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Update a font entry"""
    font = db.query(AdminFont).filter(AdminFont.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")

    # Update fields
    for field, value in font_data.model_dump(exclude_unset=True).items():
        setattr(font, field, value)

    db.commit()
    db.refresh(font)

    return AdminFontResponse.model_validate(font)


@router.delete("/fonts/{font_id}")
async def delete_font(
    font_id: str,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Delete a font entry and its file"""
    font = db.query(AdminFont).filter(AdminFont.id == font_id).first()
    if not font:
        raise HTTPException(status_code=404, detail="Font not found")

    # Delete file if it exists
    if font.file_path and os.path.exists(font.file_path):
        os.remove(font.file_path)

    db.delete(font)
    db.commit()

    return {"message": "Font deleted successfully"}


# Suggested Text Management Endpoints
@router.get("/suggested-texts", response_model=AdminResourceListResponse)
async def list_suggested_texts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_premium: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """List all suggested texts with pagination and filtering"""
    query = db.query(AdminSuggestedText)

    if search:
        query = query.filter(AdminSuggestedText.text.ilike(f"%{search}%"))

    if category:
        query = query.filter(AdminSuggestedText.category == category)

    if is_active is not None:
        query = query.filter(AdminSuggestedText.is_active == is_active)

    if is_premium is not None:
        query = query.filter(AdminSuggestedText.is_premium == is_premium)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return AdminResourceListResponse(
        items=[AdminSuggestedTextResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


@router.post("/suggested-texts", response_model=AdminSuggestedTextResponse)
async def create_suggested_text(
    text_data: AdminSuggestedTextCreate,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Create a new suggested text entry"""
    suggested_text = AdminSuggestedText(
        text=text_data.text,
        category=text_data.category,
        is_premium=text_data.is_premium,
    )

    db.add(suggested_text)
    db.commit()
    db.refresh(suggested_text)

    return AdminSuggestedTextResponse.model_validate(suggested_text)


@router.get("/suggested-texts/{text_id}", response_model=AdminSuggestedTextResponse)
async def get_suggested_text(
    text_id: str,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Get a specific suggested text by ID"""
    suggested_text = db.query(AdminSuggestedText).filter(AdminSuggestedText.id == text_id).first()
    if not suggested_text:
        raise HTTPException(status_code=404, detail="Suggested text not found")

    return AdminSuggestedTextResponse.model_validate(suggested_text)


@router.put("/suggested-texts/{text_id}", response_model=AdminSuggestedTextResponse)
async def update_suggested_text(
    text_id: str,
    text_data: AdminSuggestedTextUpdate,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Update a suggested text entry"""
    suggested_text = db.query(AdminSuggestedText).filter(AdminSuggestedText.id == text_id).first()
    if not suggested_text:
        raise HTTPException(status_code=404, detail="Suggested text not found")

    # Update fields
    for field, value in text_data.model_dump(exclude_unset=True).items():
        setattr(suggested_text, field, value)

    db.commit()
    db.refresh(suggested_text)

    return AdminSuggestedTextResponse.model_validate(suggested_text)


@router.delete("/suggested-texts/{text_id}")
async def delete_suggested_text(
    text_id: str,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Delete a suggested text entry"""
    suggested_text = db.query(AdminSuggestedText).filter(AdminSuggestedText.id == text_id).first()
    if not suggested_text:
        raise HTTPException(status_code=404, detail="Suggested text not found")

    db.delete(suggested_text)
    db.commit()

    return {"message": "Suggested text deleted successfully"}


# Background Management Endpoints
@router.get("/backgrounds", response_model=AdminResourceListResponse)
async def list_backgrounds(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_premium: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """List all backgrounds with pagination and filtering"""
    query = db.query(AdminBackground)

    if search:
        query = query.filter(
            AdminBackground.name.ilike(f"%{search}%") |
            AdminBackground.display_name.ilike(f"%{search}%")
        )

    if category:
        query = query.filter(AdminBackground.category == category)

    if is_active is not None:
        query = query.filter(AdminBackground.is_active == is_active)

    if is_premium is not None:
        query = query.filter(AdminBackground.is_premium == is_premium)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return AdminResourceListResponse(
        items=[AdminBackgroundResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


@router.post("/backgrounds", response_model=AdminBackgroundResponse)
async def create_background(
    background_data: AdminBackgroundCreate,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Create a new background entry"""
    # Check if background name already exists
    existing_background = db.query(AdminBackground).filter(AdminBackground.name == background_data.name).first()
    if existing_background:
        raise HTTPException(status_code=400, detail="Background name already exists")

    background = AdminBackground(
        name=background_data.name,
        display_name=background_data.display_name,
        description=background_data.description,
        category=background_data.category,
        is_premium=background_data.is_premium,
        file_path="",  # Will be set when file is uploaded
    )

    db.add(background)
    db.commit()
    db.refresh(background)

    return AdminBackgroundResponse.model_validate(background)


@router.post("/backgrounds/{background_id}/upload")
async def upload_background_file(
    background_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Upload background image file for a background entry"""
    # Validate background exists
    background = db.query(AdminBackground).filter(AdminBackground.id == background_id).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")

    # Validate file type
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and WebP files are allowed")

    # Create backgrounds directory if it doesn't exist
    backgrounds_dir = "backgrounds/admin"
    os.makedirs(backgrounds_dir, exist_ok=True)

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{background.name}_{uuid.uuid4().hex[:8]}{file_extension}"
    file_path = os.path.join(backgrounds_dir, filename)

    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Update background record
    background.file_path = file_path
    background.file_size = len(content)
    db.commit()

    return {"message": "Background file uploaded successfully", "file_path": file_path}


@router.get("/backgrounds/{background_id}", response_model=AdminBackgroundResponse)
async def get_background(
    background_id: str,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Get a specific background by ID"""
    background = db.query(AdminBackground).filter(AdminBackground.id == background_id).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")

    return AdminBackgroundResponse.model_validate(background)


@router.put("/backgrounds/{background_id}", response_model=AdminBackgroundResponse)
async def update_background(
    background_id: str,
    background_data: AdminBackgroundUpdate,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Update a background entry"""
    background = db.query(AdminBackground).filter(AdminBackground.id == background_id).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")

    # Update fields
    for field, value in background_data.model_dump(exclude_unset=True).items():
        setattr(background, field, value)

    db.commit()
    db.refresh(background)

    return AdminBackgroundResponse.model_validate(background)


@router.delete("/backgrounds/{background_id}")
async def delete_background(
    background_id: str,
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Delete a background entry and its file"""
    background = db.query(AdminBackground).filter(AdminBackground.id == background_id).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")

    # Delete file if it exists
    if background.file_path and os.path.exists(background.file_path):
        os.remove(background.file_path)

    db.delete(background)
    db.commit()

    return {"message": "Background deleted successfully"}


# Statistics Endpoints
@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    _: bool = admin_auth.get_admin_dependency(),
):
    """Get admin dashboard statistics"""
    font_stats = db.query(
        func.count(AdminFont.id).label('total'),
        func.count(AdminFont.id).filter(AdminFont.is_active == True).label('active'),
        func.count(AdminFont.id).filter(AdminFont.is_premium == True).label('premium')
    ).first()

    text_stats = db.query(
        func.count(AdminSuggestedText.id).label('total'),
        func.count(AdminSuggestedText.id).filter(AdminSuggestedText.is_active == True).label('active'),
        func.count(AdminSuggestedText.id).filter(AdminSuggestedText.is_premium == True).label('premium')
    ).first()

    background_stats = db.query(
        func.count(AdminBackground.id).label('total'),
        func.count(AdminBackground.id).filter(AdminBackground.is_active == True).label('active'),
        func.count(AdminBackground.id).filter(AdminBackground.is_premium == True).label('premium')
    ).first()

    return {
        "fonts": {
            "total": font_stats.total,
            "active": font_stats.active,
            "premium": font_stats.premium
        },
        "suggested_texts": {
            "total": text_stats.total,
            "active": text_stats.active,
            "premium": text_stats.premium
        },
        "backgrounds": {
            "total": background_stats.total,
            "active": background_stats.active,
            "premium": background_stats.premium
        }
    }
