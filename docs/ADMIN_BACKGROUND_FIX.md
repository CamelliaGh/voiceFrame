# Admin Panel Background Display Fix

## Problem Summary

The admin panel shows no backgrounds while the customization panel displays several backgrounds correctly. This is caused by a file path resolution issue in the `admin_resource_service.py`.

## Root Cause

The `get_active_backgrounds` method in `backend/services/admin_resource_service.py` was using a simple `os.path.exists()` check that didn't account for different file path contexts between development and production environments.

**Key Issues:**
1. **File Path Context**: Database stores paths like `backgrounds/admin/filename.jpg`
2. **Docker Environment**: Files are mounted at `/app/backgrounds/admin/` in containers
3. **Working Directory**: The service wasn't checking multiple possible file locations
4. **API Difference**: `/api/resources/backgrounds` (used by customization panel) filters by file existence, while `/admin/backgrounds` (used by admin panel) returns all database entries

## Solution Applied

### 1. Enhanced File Path Resolution

Updated `admin_resource_service.py` to check multiple possible file locations:

```python
# Check if file exists - handle both absolute and relative paths
file_path = background.file_path
file_exists = False

if file_path:
    # Try the path as-is first
    if os.path.exists(file_path):
        file_exists = True
    # If not found and it's a relative path, try from current working directory
    elif not os.path.isabs(file_path):
        # For Docker containers, files are typically at /app/backgrounds/admin/
        abs_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(abs_path):
            file_exists = True
        # Also try without current working directory for cases where file_path is already correct
        elif file_path.startswith('backgrounds/') and os.path.exists(f"/{file_path}"):
            file_exists = True
```

### 2. Updated Methods

Fixed three methods in `admin_resource_service.py`:
- `get_active_backgrounds()` - Used by `/api/resources/backgrounds` endpoint
- `get_background_file_path()` - Used for background file access
- `get_font_file_path()` - Applied same fix for consistency

## Deployment Instructions

### 1. Deploy the Code Fix

```bash
# On production server
cd /opt/voiceframe
git pull origin main

# Restart the API container to apply the fix
docker-compose -f docker-compose.prod.yml restart api
```

### 2. Verify the Fix

Run the diagnostic script to check the current state:

```bash
# From the host
cd /opt/voiceframe
python3 scripts/diagnose_background_issue.py

# Or from within the Docker container
docker-compose -f docker-compose.prod.yml exec api python3 scripts/diagnose_background_issue.py
```

### 3. Test Admin Panel

1. Navigate to `https://vocaframe.com/admin`
2. Go to the "Backgrounds" tab
3. Verify that backgrounds are now visible
4. If still not showing, check the browser console for any JavaScript errors

### 4. Clear Browser Cache

The admin panel might have cached the empty state:
- Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Or clear browser cache completely

## Verification Steps

### Check Database Backgrounds
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U audioposter -d audioposter -c "SELECT name, display_name, file_path, is_active FROM admin_backgrounds;"
```

### Check File Existence
```bash
# Check files exist in container
docker-compose -f docker-compose.prod.yml exec api ls -la /app/backgrounds/admin/

# Check files exist for nginx
docker-compose -f docker-compose.prod.yml exec nginx ls -la /var/www/backgrounds/admin/
```

### Test API Endpoints

1. **Customization Panel Endpoint** (should work):
   ```bash
   curl https://vocaframe.com/api/resources/backgrounds
   ```

2. **Admin Panel Endpoint** (should now work):
   ```bash
   curl -H "Authorization: Basic <admin-credentials>" https://vocaframe.com/admin/backgrounds
   ```

## Troubleshooting

### If Backgrounds Still Don't Show

1. **Check Container Logs**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs api | grep -i background
   ```

2. **Verify File Permissions**:
   ```bash
   # Check file permissions on host
   ls -la /opt/voiceframe/backgrounds/admin/

   # Fix permissions if needed
   sudo chown -R 1000:1000 /opt/voiceframe/backgrounds/admin/
   sudo chmod -R 755 /opt/voiceframe/backgrounds/
   ```

3. **Check Volume Mounts**:
   ```bash
   docker-compose -f docker-compose.prod.yml config | grep -A 5 -B 5 backgrounds
   ```

4. **Restart All Services**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

### If No Backgrounds in Database

The admin needs to upload backgrounds via the admin panel:

1. Go to `https://vocaframe.com/admin`
2. Navigate to "Backgrounds" tab
3. Click "Add Background"
4. Fill in details and upload image files
5. Make sure to set the correct **orientation** (portrait/landscape/both)
6. Enable the background by checking "Active"

## Technical Details

### File Path Storage
- Database stores: `backgrounds/admin/filename_12345678.jpg`
- Docker container path: `/app/backgrounds/admin/filename_12345678.jpg`
- Nginx serves from: `/var/www/backgrounds/admin/filename_12345678.jpg`

### API Endpoints
- **Customization Panel**: `GET /api/resources/backgrounds?orientation=portrait`
  - Filters by file existence and orientation
  - Used by `BackgroundSelection.tsx`

- **Admin Panel**: `GET /admin/backgrounds`
  - Returns all database entries with pagination
  - Used by admin dashboard

### Docker Volume Mounts
```yaml
# In docker-compose.prod.yml
volumes:
  - ./backgrounds:/app/backgrounds  # API container (read/write)
  - ./backgrounds:/var/www/backgrounds:ro  # Nginx container (read-only)
```

## Related Files Modified

- `backend/services/admin_resource_service.py` - Main fix
- `scripts/diagnose_background_issue.py` - Diagnostic tool
- `docs/ADMIN_BACKGROUND_FIX.md` - This documentation

## Prevention

To prevent this issue in the future:
1. Always test admin panel functionality after deployment
2. Use the diagnostic script during deployment verification
3. Ensure proper volume mounts in Docker configurations
4. Test file path resolution in different environments

## Related Documentation

- [Background Upload Fix](./BACKGROUND_UPLOAD_FIX.md) - Volume mount setup
- [Background Quick Start](./BACKGROUND_QUICK_START.md) - User guide
- [Admin Panel Setup](./admin_panel_setup.md) - Admin authentication
