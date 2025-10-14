# File Migration Fix - 500 Error Resolution

## 🐛 **The Problem**

After fixing the EmailSubscriber table issue, users are still getting 500 errors during payment completion. The new errors are:

1. **QR Code Generation Error**: `Permanent audio file missing: No key set`
2. **Missing Method Error**: `'VisualPDFGenerator' object has no attribute 'convert_pdf_to_image'`

## 🔍 **Root Cause Analysis**

### Issue 1: Missing Method Error ✅ FIXED
The `pdf_generator` in `main.py` is initialized as `VisualPDFGenerator()`, but the code tries to call `convert_pdf_to_image()` method which only existed in the `PDFGenerator` class.

**Fix**: Added the `convert_pdf_to_image` method to `VisualPDFGenerator` class.

### Issue 2: QR Code Generation Error 🔧 NEEDS FIX
The QR code generation fails because `order.permanent_audio_s3_key` is `None`. This happens because the file migration process in `storage_manager.migrate_all_session_files()` is failing.

**Root Cause**: The migration logic is looking for files in local temporary storage, but the application actually stores files in S3. The method is looking for:

- **Photo**: `temp_photos/{session_token}.jpg` in local temp storage ❌
- **Audio**: Files in `temp_audio/` directory in local temp storage ❌
- **Waveform**: `waveforms/{session_token}.png` in S3 ✅

But the files are actually stored in S3 with keys like:
- `temp_photos/...`
- `temp_audio/...`
- `waveforms/...`

## ✅ **The Solution**

### Fix 1: Added Missing Method ✅ COMPLETED
Added `convert_pdf_to_image` method to `VisualPDFGenerator` class in `backend/services/visual_pdf_generator.py`.

### Fix 2: Fix File Migration Logic 🔧 NEEDED

The `migrate_all_session_files` method in `backend/services/storage_manager.py` needs to be updated to work with S3-stored files instead of local files.

**Current Logic (Broken)**:
```python
# Looking for local files
temp_photo_path = os.path.join(self.temp_storage_path, temp_photo_key)
if os.path.exists(temp_photo_path):  # This fails because files are in S3
```

**Fixed Logic (Needed)**:
```python
# Looking for S3 files
if self.file_uploader.file_exists(temp_photo_key):  # Check S3 instead
```

## 🚀 **Deployment Steps**

### Step 1: Apply the convert_pdf_to_image Fix ✅ COMPLETED
The missing method has been added to `VisualPDFGenerator`.

### Step 2: Fix the File Migration Logic 🔧 NEEDED

Update the `migrate_all_session_files` method to work with S3 files:

```python
async def migrate_all_session_files(self, session_token: str, order_id: str, context: Optional[FileOperationContext] = None, db=None) -> dict:
    """Migrate all files for a session to permanent storage after payment"""
    try:
        permanent_keys = {}
        migration_log = []
        start_time = time.time()

        # Migrate photo from S3 to S3
        temp_photo_key = f"temp_photos/{session_token}.jpg"
        if self.file_uploader.file_exists(temp_photo_key):
            permanent_photo_key = f"permanent/photos/{order_id}.jpg"
            await self._copy_s3_file(temp_photo_key, permanent_photo_key)
            permanent_keys['permanent_photo_s3_key'] = permanent_photo_key
            migration_log.append(f"Migrated photo: {temp_photo_key} -> {permanent_photo_key}")

        # Migrate audio from S3 to S3
        # Find audio file with session token prefix
        audio_files = self.file_uploader.list_files_with_prefix(f"temp_audio/{session_token}")
        for audio_key in audio_files:
            file_extension = audio_key.split('.')[-1]
            permanent_audio_key = f"permanent/audio/{order_id}.{file_extension}"
            await self._copy_s3_file(audio_key, permanent_audio_key)
            permanent_keys['permanent_audio_s3_key'] = permanent_audio_key
            migration_log.append(f"Migrated audio: {audio_key} -> {permanent_audio_key}")
            break  # Only migrate the first audio file found

        # Migrate waveform from S3 to S3
        waveform_s3_key = f"waveforms/{session_token}.png"
        if self.file_uploader.file_exists(waveform_s3_key):
            permanent_waveform_key = f"permanent/waveforms/{order_id}.png"
            await self._copy_s3_file(waveform_s3_key, permanent_waveform_key)
            permanent_keys['permanent_waveform_s3_key'] = permanent_waveform_key
            migration_log.append(f"Migrated waveform: {waveform_s3_key} -> {permanent_waveform_key}")

        print(f"Migration completed for order {order_id}: {len(permanent_keys)} files migrated")
        for log_entry in migration_log:
            print(f"  - {log_entry}")

        return permanent_keys

    except Exception as e:
        error_msg = f"Migration to permanent storage failed: {str(e)}"
        print(f"Migration error for order {order_id}: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
```

### Step 3: Deploy and Test

```bash
# SSH into production server
cd /opt/voiceframe

# Restart API to apply the convert_pdf_to_image fix
docker-compose -f docker-compose.prod.yml restart api

# Test payment flow
# 1. Go to https://vocaframe.com
# 2. Upload photo + audio
# 3. Customize and preview
# 4. Try payment with test card: 4242 4242 4242 4242
```

## 🧪 **Expected Results After Fix**

- ✅ Payment succeeds
- ✅ File migration completes successfully
- ✅ `order.permanent_audio_s3_key` is set correctly
- ✅ QR code generation works
- ✅ PDF generates without errors
- ✅ Download link appears
- ✅ Email is sent
- ✅ No more 500 errors!

## 📊 **Monitoring**

Check logs to verify the fixes:

```bash
# Watch API logs
docker-compose -f docker-compose.prod.yml logs -f api

# Look for these good signs:
# INFO: File migration completed successfully
# INFO: Migrated photo: temp_photos/... -> permanent/photos/...
# INFO: Migrated audio: temp_audio/... -> permanent/audio/...
# INFO: Migrated waveform: waveforms/... -> permanent/waveforms/...
# INFO: Payment succeeded: pi_xxx
# INFO: PDF created successfully
# INFO: Email sent to user@example.com
# INFO: 172.18.0.1:xxxxx - "POST /api/orders/{order_id}/complete HTTP/1.0" 200 OK

# No more QR code errors or missing method errors!
```

---

**Status**:
- ✅ Fix 1 (Missing Method): COMPLETED
- 🔧 Fix 2 (File Migration): NEEDS IMPLEMENTATION

The convert_pdf_to_image method has been added. The file migration logic still needs to be updated to work with S3 files instead of local files.
