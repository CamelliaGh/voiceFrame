# Background Upload Fix - Deployment Guide

## Problem Summary

Background images uploaded via the admin panel were not persisting because the `backgrounds` directory was not mounted as a volume in the Docker Compose production configuration.

## Root Cause

1. **Missing Volume Mount**: The `docker-compose.prod.yml` file did not include the `backgrounds` directory as a volume mount
2. **Nginx Configuration**: The nginx config did not have a location block to serve background images
3. **File Persistence**: Files uploaded to `/app/backgrounds/admin/` inside the container were lost on restart

## Changes Made

### 1. Updated `docker-compose.prod.yml`

Added `backgrounds` directory mount to three services:

**API Service** (line 85):
```yaml
- ./backgrounds:/app/backgrounds  # WRITABLE: admin uploads backgrounds here
```

**Celery Worker Service** (line 136):
```yaml
- ./backgrounds:/app/backgrounds  # WRITABLE: admin uploads backgrounds here
```

**Nginx Service** (line 198):
```yaml
- ./backgrounds:/var/www/backgrounds:ro  # Serve background images
```

### 2. Updated Nginx Configurations

#### `nginx.prod.conf` (Docker production config)
Added new location block for serving background images (after line 77):
```nginx
# Background images (admin-managed)
location /backgrounds/ {
    alias /var/www/backgrounds/;
    expires 1d;
    add_header Cache-Control "public, max-age=86400";
    # Allow CORS for background previews
    add_header Access-Control-Allow-Origin "*";
    access_log off;
}
```

#### `nginx-sites/vocaframe.com.conf` (Site-specific config)
Added the same background location block and a note about rate limiting zones:
```nginx
# Background images (admin-managed)
location /backgrounds/ {
    alias /var/www/backgrounds/;
    expires 1d;
    add_header Cache-Control "public, max-age=86400";
    # Allow CORS for background previews
    add_header Access-Control-Allow-Origin "*";
    access_log off;
}
```

**Important**: If using the site-specific config, ensure rate limiting zones are defined in `/etc/nginx/nginx.conf` in the `http` block:
```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;
    # ... rest of config
}
```

### 3. Database Cleanup

Removed stale background entries that referenced non-existent files:
```sql
DELETE FROM admin_backgrounds;
```

### 4. File System Cleanup

Removed old background files that were no longer in the database:
- `copy-space-with-cute-hearts.jpg`
- `beautiful-roses-great-white-wooden-background-with-space-right.jpg`
- `flat-lay-small-cute-hearts.jpg`

## Deployment Steps

### On Production Server

1. **Pull Latest Changes**
   ```bash
   cd /opt/voiceframe
   git pull origin main
   ```

2. **Ensure Directory Structure**
   ```bash
   mkdir -p backgrounds/admin fonts/admin
   chmod 755 backgrounds backgrounds/admin fonts fonts/admin
   ```

3. **Update Nginx Configuration (if using site-specific config)**

   If you're using `/etc/nginx/sites-enabled/vocaframe.com.conf`:
   ```bash
   # Copy updated site config
   sudo cp /opt/voiceframe/nginx-sites/vocaframe.com.conf /etc/nginx/sites-available/vocaframe.com.conf

   # Ensure rate limiting zones are defined in main nginx.conf
   sudo nano /etc/nginx/nginx.conf
   # Add in the http block if not present:
   #   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   #   limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

   # Test nginx configuration
   sudo nginx -t

   # Reload nginx
   sudo systemctl reload nginx
   ```

4. **Restart Docker Services**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Verify Volume Mounts**
   ```bash
   docker-compose -f docker-compose.prod.yml exec api ls -la /app/backgrounds/
   docker-compose -f docker-compose.prod.yml exec nginx ls -la /var/www/backgrounds/
   ```

6. **Clear Browser Cache**
   - Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
   - Or clear browser cache completely

### Re-upload Backgrounds

1. Navigate to the admin panel: `https://vocaframe.com/admin`
2. Go to the "Backgrounds" tab
3. Click "Add Background"
4. Fill in the details:
   - **Name**: Short identifier (e.g., `floral-1`)
   - **Display Name**: User-friendly name (e.g., `Floral 1`)
   - **Description**: Brief description
   - **Category**: e.g., `nature`, `abstract`, `patterns`
   - **Orientation**: Choose `portrait`, `landscape`, or `both`
   - **Active**: Check to enable
5. Upload the image file (JPG, PNG, or WebP)
6. Save the background

**Important**: Set the correct **orientation** value:
- `portrait` - For tall/vertical images (A4 portrait, A3 portrait, etc.)
- `landscape` - For wide/horizontal images (A4 landscape, A3 landscape, etc.)
- `both` - For images that work well in both orientations

## Verification

### Check File Persistence

1. Upload a test background via admin panel
2. Check that the file exists on the host:
   ```bash
   ls -la /opt/voiceframe/backgrounds/admin/
   ```
3. Restart the API container:
   ```bash
   docker-compose -f docker-compose.prod.yml restart api
   ```
4. Verify the file still exists
5. Check that the background appears in the customization panel

### Check Image Serving

1. Open browser developer tools (F12)
2. Go to the customization panel
3. Check Network tab for background requests
4. Verify backgrounds load with `200 OK` status
5. No `404` errors should appear

### Check Orientation Filtering

1. Select "A4" (portrait) PDF size
2. Verify only portrait and "both" backgrounds appear
3. Switch to "A4 Landscape"
4. Verify only landscape and "both" backgrounds appear

## Troubleshooting

### Backgrounds Not Showing

1. **Check file exists**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec api ls -la /app/backgrounds/admin/
   ```

2. **Check database entry**:
   ```bash
   docker-compose exec db psql -U audioposter -d audioposter -c "SELECT name, file_path, orientation, is_active FROM admin_backgrounds;"
   ```

3. **Check nginx can access files**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec nginx ls -la /var/www/backgrounds/admin/
   ```

4. **Check nginx logs**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs nginx | grep backgrounds
   ```

### 404 Errors

1. **Clear browser cache** - Old entries may be cached
2. **Check nginx config** - Verify location block exists
3. **Restart nginx**:
   ```bash
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

### Permission Issues

If you get permission errors during upload:
```bash
sudo chown -R 1000:1000 /opt/voiceframe/backgrounds/admin
sudo chmod -R 755 /opt/voiceframe/backgrounds
```

## Notes

- The `backgrounds` directory is now mounted as **writable** (not read-only) to allow admin uploads
- Background images are served with 1-day cache expiration
- Old hardcoded backgrounds have been completely removed
- All backgrounds now come from the admin panel database
- Frontend filters backgrounds by orientation based on selected PDF size

## Related Documentation

- [Background Quick Start](./BACKGROUND_QUICK_START.md) - User guide for managing backgrounds
- [Admin Panel Setup](./admin_panel_setup.md) - Admin authentication setup
