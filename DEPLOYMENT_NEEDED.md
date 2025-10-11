# 🚨 DEPLOYMENT REQUIRED - Background Upload Fix

## What Was Wrong

The `backgrounds` directory was NOT mounted in your Docker production setup, so:
1. When you uploaded backgrounds via admin panel, files were saved **inside** the container
2. Files were lost on container restart or were never accessible from the host
3. This caused all those 404 errors and missing backgrounds

## What I Fixed

### ✅ Updated Files (Already Done)
1. **`docker-compose.prod.yml`** - Added `backgrounds` directory mounts to API, Celery, and Nginx services
2. **`nginx.prod.conf`** - Added location block to serve background images
3. **Cleaned up database** - Removed 4 stale background entries
4. **Cleaned up filesystem** - Removed 3 old background files that no longer exist in database

### 🔧 What You Need to Do NOW

**On your production server (vocaframe.com):**

```bash
# 1. Pull latest changes
cd /opt/voiceframe
git pull origin main

# 2. Ensure directory structure exists
mkdir -p backgrounds/admin fonts/admin
chmod 755 backgrounds backgrounds/admin

# 3. Restart all services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify the mounts are working
docker-compose -f docker-compose.prod.yml exec api ls -la /app/backgrounds/
docker-compose -f docker-compose.prod.yml exec nginx ls -la /var/www/backgrounds/

# 5. Check logs for any errors
docker-compose -f docker-compose.prod.yml logs api | tail -50
```

### 📤 Then Re-upload Your Backgrounds

1. Go to `https://vocaframe.com/admin`
2. Navigate to "Backgrounds" tab
3. Add new backgrounds with proper settings:
   - **Orientation is CRITICAL**:
     - Choose `portrait` for tall images (A4 portrait)
     - Choose `landscape` for wide images (A4 landscape)
     - Choose `both` only if image works well in both orientations
4. Upload the image files
5. Save and activate them

### 🧹 Clear Your Browser Cache

The old 404 errors may be cached:
- Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) to hard refresh
- Or clear your browser cache completely

## Expected Result

After deployment and re-uploading:
- ✅ Background files will persist across container restarts
- ✅ Backgrounds will appear in the customization panel
- ✅ No more 404 errors for backgrounds
- ✅ Background images will load correctly
- ✅ Backgrounds will filter correctly by orientation (portrait/landscape)

## Files Changed

- `docker-compose.prod.yml` (added volume mounts)
- `nginx.prod.conf` (added /backgrounds/ location block)
- `nginx-sites/vocaframe.com.conf` (added /backgrounds/ location block)
- Database: `admin_backgrounds` table cleaned
- Filesystem: Old background files removed

## Additional Nginx Setup (If Using Site-Specific Config)

If you're using the site-specific nginx config (`nginx-sites/vocaframe.com.conf`), you need to:

1. **Copy the updated site config**:
   ```bash
   sudo cp /opt/voiceframe/nginx-sites/vocaframe.com.conf /etc/nginx/sites-available/vocaframe.com.conf
   ```

2. **Ensure rate limiting zones are defined in main nginx.conf**:

   Edit `/etc/nginx/nginx.conf` and add these lines in the `http` block:
   ```nginx
   http {
       # Rate limiting zones
       limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
       limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;

       # ... rest of http config
   }
   ```

3. **Test and reload nginx**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Documentation

See full details in: **`docs/BACKGROUND_UPLOAD_FIX.md`**

---

**Status**: 🟡 PENDING DEPLOYMENT
**Priority**: HIGH - Required for background functionality to work
**Estimated Time**: 5-10 minutes
