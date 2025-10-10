# Background Path Mismatch Fix

## Issue Description

The admin panel was uploading background files to a path that the customization panel couldn't access properly.

## Root Cause

FastAPI's static file route mounting order was incorrect. When routes are mounted:

```python
# INCORRECT ORDER (before fix)
app.mount("/backgrounds", StaticFiles(directory=backgrounds_dir), name="backgrounds")
app.mount("/backgrounds/admin", StaticFiles(directory=admin_backgrounds_dir), name="admin_backgrounds")
```

The more general `/backgrounds` route was registered first, causing it to intercept ALL requests starting with `/backgrounds`, including those meant for `/backgrounds/admin`.

## How It Works

### Admin Upload Flow

1. **Admin uploads background** → saved to `backgrounds/admin/filename_{uuid}.jpg`
2. **Database stores** → `file_path: "backgrounds/admin/filename_{uuid}.jpg"`
3. **API returns** → `file_path: "backgrounds/admin/filename_{uuid}.jpg"`

### Frontend Access Flow

1. **Frontend fetches** → `/api/resources/backgrounds`
2. **Frontend constructs URL** → `/backgrounds/admin/filename.jpg`
3. **Browser requests** → `/backgrounds/admin/filename.jpg`
4. **FastAPI serves** → Static file from appropriate mount

### PDF Generation Flow

1. **PDF generator fetches** → background metadata from database
2. **Gets file_path** → `backgrounds/admin/filename.jpg`
3. **Reads directly from filesystem** → `Path(background_data['file_path'])`
4. **Works correctly** → No URL involved, just filesystem access

## Solution

Reorder the static file mounts so more specific routes are registered BEFORE general ones:

```python
# CORRECT ORDER (after fix)
# Mount admin backgrounds directory FIRST
app.mount("/backgrounds/admin", StaticFiles(directory=admin_backgrounds_dir), name="admin_backgrounds")

# Mount general backgrounds directory SECOND
app.mount("/backgrounds", StaticFiles(directory=backgrounds_dir), name="backgrounds")
```

## Impact

- **Frontend preview**: Now correctly loads admin-uploaded backgrounds in the customization panel
- **PDF generation**: Already worked, continues to work (uses filesystem paths, not URLs)
- **Default backgrounds**: Continue to work (mounted at `/backgrounds`, served from `backgrounds/` directory)
- **Admin-uploaded backgrounds**: Now work (mounted at `/backgrounds/admin`, served from `backgrounds/admin/` directory)

## Files Modified

- `backend/main.py` - Fixed static mount order (lines 108-117)

## Testing

To verify the fix works:

1. **Admin Panel**:
   - Login to admin panel
   - Upload a background image
   - Verify file is saved to `backgrounds/admin/` directory

2. **Customization Panel**:
   - Open customization panel
   - Change PDF orientation (portrait/landscape)
   - Verify admin-uploaded backgrounds appear in the background selection
   - Select an admin-uploaded background
   - Verify it displays correctly in the preview

3. **PDF Generation**:
   - Generate a preview PDF with an admin-uploaded background
   - Verify the background appears correctly in the PDF
   - Generate a final PDF
   - Verify the background appears correctly in the final PDF

## Related Code

- **Admin upload endpoint**: `backend/routers/admin.py:384-420`
- **Resource service**: `backend/services/admin_resource_service.py:59-93`
- **Frontend background selection**: `src/components/BackgroundSelection.tsx:86-148`
- **PDF background loading**: `backend/services/visual_pdf_generator.py:721-807`
- **Static file mounts**: `backend/main.py:108-117`
