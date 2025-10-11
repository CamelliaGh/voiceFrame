# Background Migration Guide

## Overview

All backgrounds are now managed through the admin panel instead of being hardcoded. This guide helps you migrate existing background images to the admin panel.

## What Changed

### Before (Hardcoded)
- Background IDs and file paths were hardcoded in `visual_pdf_generator.py`
- Frontend had hardcoded fallback backgrounds
- No way to add/remove backgrounds without code changes

### After (Admin-Managed)
- All backgrounds are stored in the database via admin panel
- Only "none" (no background) is hardcoded as a special case
- Backgrounds can be added, edited, or removed through the admin UI
- Supports orientation filtering (portrait/landscape/both)
- Supports categories and premium backgrounds

## Migration Steps

### 1. Access Admin Panel

Navigate to `/admin` and log in with your admin credentials.

### 2. Add Existing Backgrounds

For each existing background file in the `backgrounds/` directory, create an admin panel entry:

#### Background 1: Abstract Blurred
- **Name (ID)**: `abstract-blurred`
- **Display Name**: `Abstract Blurred`
- **Description**: `Soft abstract background`
- **Category**: `Abstract`
- **Orientation**: `both` (or specific if needed)
- **Is Premium**: `false`
- **Is Active**: `true`
- **File**: Upload `backgrounds/237.jpg`

#### Background 2: Roses & Wood
- **Name (ID)**: `roses-wooden`
- **Display Name**: `Roses & Wood`
- **Description**: `Beautiful roses on wooden background`
- **Category**: `Romantic`
- **Orientation**: `both`
- **Is Premium**: `false`
- **Is Active**: `true`
- **File**: Upload `backgrounds/beautiful-roses-great-white-wooden-background-with-space-right.jpg`

#### Background 3: Cute Hearts
- **Name (ID)**: `cute-hearts`
- **Display Name**: `Cute Hearts`
- **Description**: `Romantic hearts background`
- **Category**: `Romantic`
- **Orientation**: `both`
- **Is Premium**: `false`
- **Is Active**: `true`
- **File**: Upload `backgrounds/copy-space-with-cute-hearts.jpg`

#### Background 4: Flat Lay Hearts
- **Name (ID)**: `flat-lay-hearts`
- **Display Name**: `Flat Lay Hearts`
- **Description**: `Elegant flat lay hearts`
- **Category**: `Romantic`
- **Orientation**: `both`
- **Is Premium**: `false`
- **Is Active**: `true`
- **File**: Upload `backgrounds/flat-lay-small-cute-hearts.jpg`

### 3. Important: Use Same Name IDs

⚠️ **Critical**: Use the exact same "Name (ID)" values as shown above. This ensures existing user sessions that reference these background IDs will continue to work.

The system uses the `name` field as the background ID for compatibility with existing data.

### 4. Orientation Guidelines

Set appropriate orientation for each background:
- **portrait**: Shows only when portrait PDF sizes are selected (A4, A3, Letter)
- **landscape**: Shows only when landscape PDF sizes are selected (A4_Landscape, etc.)
- **both**: Shows for all orientations (recommended for most backgrounds)

### 5. Verify Migration

After adding all backgrounds:

1. **Test Background Selection**:
   - Go to customization panel
   - Switch between portrait and landscape orientations
   - Verify all backgrounds appear correctly

2. **Test PDF Generation**:
   - Select each background
   - Generate preview PDF
   - Verify background appears correctly in PDF

3. **Test Existing Sessions**:
   - If you have existing user sessions with backgrounds
   - Verify they still render correctly with the new system

## Alternative: Automated Migration Script

If you have many backgrounds or want to automate this, you can create a migration script:

```python
# scripts/migrate_backgrounds.py
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from backend.database import SessionLocal
from backend.models import AdminBackground
import uuid

def migrate_backgrounds():
    db = SessionLocal()

    backgrounds = [
        {
            'name': 'abstract-blurred',
            'display_name': 'Abstract Blurred',
            'description': 'Soft abstract background',
            'category': 'Abstract',
            'file_path': 'backgrounds/237.jpg',
            'orientation': 'both'
        },
        {
            'name': 'roses-wooden',
            'display_name': 'Roses & Wood',
            'description': 'Beautiful roses on wooden background',
            'category': 'Romantic',
            'file_path': 'backgrounds/beautiful-roses-great-white-wooden-background-with-space-right.jpg',
            'orientation': 'both'
        },
        {
            'name': 'cute-hearts',
            'display_name': 'Cute Hearts',
            'description': 'Romantic hearts background',
            'category': 'Romantic',
            'file_path': 'backgrounds/copy-space-with-cute-hearts.jpg',
            'orientation': 'both'
        },
        {
            'name': 'flat-lay-hearts',
            'display_name': 'Flat Lay Hearts',
            'description': 'Elegant flat lay hearts',
            'category': 'Romantic',
            'file_path': 'backgrounds/flat-lay-small-cute-hearts.jpg',
            'orientation': 'both'
        }
    ]

    for bg_data in backgrounds:
        # Check if already exists
        existing = db.query(AdminBackground).filter(
            AdminBackground.name == bg_data['name']
        ).first()

        if existing:
            print(f"Background {bg_data['name']} already exists, skipping...")
            continue

        # Get file size
        file_size = None
        if os.path.exists(bg_data['file_path']):
            file_size = os.path.getsize(bg_data['file_path'])

        # Create new background entry
        background = AdminBackground(
            id=str(uuid.uuid4()),
            name=bg_data['name'],
            display_name=bg_data['display_name'],
            description=bg_data['description'],
            category=bg_data['category'],
            file_path=bg_data['file_path'],
            file_size=file_size,
            orientation=bg_data['orientation'],
            is_premium=False,
            is_active=True,
            usage_count=0
        )

        db.add(background)
        print(f"Added background: {bg_data['name']}")

    db.commit()
    db.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate_backgrounds()
```

Run the script:
```bash
python3 scripts/migrate_backgrounds.py
```

## New Background Workflow

After migration, to add new backgrounds:

1. **Go to Admin Panel** → Backgrounds section
2. **Click "Add Background"**
3. **Fill in details**:
   - Name (ID): lowercase-with-hyphens (e.g., `sunset-beach`)
   - Display Name: User-friendly name
   - Description: Brief description
   - Category: Romantic, Abstract, Nature, etc.
   - Orientation: portrait/landscape/both
   - Premium: Check if this is a premium background
4. **Upload image file**
5. **Click "Create"**

The background will immediately be available for selection!

## Benefits of Admin-Managed Backgrounds

✅ **Dynamic Management**: Add/remove backgrounds without code changes
✅ **Orientation Filtering**: Show appropriate backgrounds per PDF size
✅ **Categories**: Organize backgrounds for better UX
✅ **Premium Options**: Mark backgrounds as premium
✅ **Usage Tracking**: Track which backgrounds are most popular
✅ **Active/Inactive**: Temporarily hide backgrounds without deleting
✅ **No Code Deployment**: Changes take effect immediately

## Troubleshooting

### Background Not Appearing in Selection

1. Check background is marked as "Active" in admin panel
2. Verify orientation matches the selected PDF size
3. Check file path exists and is correct
4. Look at browser console for errors

### Background Not Rendering in PDF

1. Verify file exists at the stored `file_path`
2. Check file permissions (readable by application)
3. Look at backend logs for errors
4. Verify background ID matches exactly

### Old Backgrounds Still Showing

1. Clear browser cache
2. Restart the backend server
3. Verify old hardcoded backgrounds were removed from code

## Files Modified

- `backend/services/visual_pdf_generator.py` - Removed hardcoded mapping
- `src/components/BackgroundSelection.tsx` - Removed hardcoded fallbacks
- `docs/BACKGROUND_PATH_FIX.md` - Updated documentation
