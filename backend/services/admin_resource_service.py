"""
Admin Resource Service

Provides access to admin-managed resources (fonts, suggested texts, backgrounds)
for use in the PDF generation system.
"""

import os
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import AdminFont, AdminSuggestedText, AdminBackground
from ..database import get_db


class AdminResourceService:
    """Service for accessing admin-managed resources"""

    def __init__(self):
        pass

    def get_active_fonts(self, db: Session) -> List[Dict[str, Any]]:
        """Get all active fonts for use in PDF generation"""
        fonts = db.query(AdminFont).filter(AdminFont.is_active == True).all()

        result = []
        for font in fonts:
            result.append({
                'id': font.name,  # Use name as ID for compatibility
                'name': font.name,
                'display_name': font.display_name,
                'file_path': font.file_path,
                'is_premium': font.is_premium,
                'description': font.description
            })

        return result

    def get_active_suggested_texts(self, db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active suggested texts, optionally filtered by category"""
        query = db.query(AdminSuggestedText).filter(AdminSuggestedText.is_active == True)

        if category:
            query = query.filter(AdminSuggestedText.category == category)

        texts = query.all()

        result = []
        for text in texts:
            result.append({
                'id': str(text.id),
                'text': text.text,
                'category': text.category,
                'is_premium': text.is_premium,
                'usage_count': text.usage_count
            })

        return result

    def get_active_backgrounds(self, db: Session, category: Optional[str] = None, orientation: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active backgrounds, optionally filtered by category and orientation"""
        query = db.query(AdminBackground).filter(AdminBackground.is_active == True)

        if category:
            query = query.filter(AdminBackground.category == category)

        if orientation:
            # Filter by orientation: show backgrounds that match the requested orientation or are suitable for 'both'
            query = query.filter(
                (AdminBackground.orientation == orientation) |
                (AdminBackground.orientation == 'both')
            )

        backgrounds = query.all()

        result = []
        for background in backgrounds:
            result.append({
                'id': background.name,  # Use name as ID for compatibility
                'name': background.name,
                'display_name': background.display_name,
                'file_path': background.file_path,
                'is_premium': background.is_premium,
                'description': background.description,
                'category': background.category,
                'orientation': background.orientation,
                'usage_count': background.usage_count
            })

        return result

    def get_font_by_name(self, db: Session, font_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific font by name"""
        font = db.query(AdminFont).filter(
            AdminFont.name == font_name,
            AdminFont.is_active == True
        ).first()

        if not font:
            return None

        return {
            'id': font.name,
            'name': font.name,
            'display_name': font.display_name,
            'file_path': font.file_path,
            'is_premium': font.is_premium,
            'description': font.description
        }

    def get_background_by_name(self, db: Session, background_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific background by name"""
        background = db.query(AdminBackground).filter(
            AdminBackground.name == background_name,
            AdminBackground.is_active == True
        ).first()

        if not background:
            return None

        return {
            'id': background.name,
            'name': background.name,
            'display_name': background.display_name,
            'file_path': background.file_path,
            'is_premium': background.is_premium,
            'description': background.description,
            'category': background.category,
            'orientation': background.orientation,
            'usage_count': background.usage_count
        }

    def increment_usage_count(self, db: Session, resource_type: str, resource_id: str):
        """Increment usage count for a resource"""
        if resource_type == 'suggested_text':
            text = db.query(AdminSuggestedText).filter(AdminSuggestedText.id == resource_id).first()
            if text:
                text.usage_count += 1
                db.commit()
        elif resource_type == 'background':
            background = db.query(AdminBackground).filter(AdminBackground.name == resource_id).first()
            if background:
                background.usage_count += 1
                db.commit()

    def get_font_file_path(self, db: Session, font_name: str) -> Optional[str]:
        """Get the file path for a font"""
        font = db.query(AdminFont).filter(
            AdminFont.name == font_name,
            AdminFont.is_active == True
        ).first()

        if not font or not font.file_path:
            return None

        # Check if file exists
        if os.path.exists(font.file_path):
            return font.file_path

        return None

    def get_background_file_path(self, db: Session, background_name: str) -> Optional[str]:
        """Get the file path for a background"""
        background = db.query(AdminBackground).filter(
            AdminBackground.name == background_name,
            AdminBackground.is_active == True
        ).first()

        if not background or not background.file_path:
            return None

        # Check if file exists
        if os.path.exists(background.file_path):
            return background.file_path

        return None

    def get_categories(self, db: Session, resource_type: str) -> List[str]:
        """Get all categories for a resource type"""
        if resource_type == 'suggested_text':
            categories = db.query(AdminSuggestedText.category).filter(
                AdminSuggestedText.category.isnot(None),
                AdminSuggestedText.is_active == True
            ).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        elif resource_type == 'background':
            categories = db.query(AdminBackground.category).filter(
                AdminBackground.category.isnot(None),
                AdminBackground.is_active == True
            ).distinct().all()
            return [cat[0] for cat in categories if cat[0]]

        return []


# Global instance
admin_resource_service = AdminResourceService()
