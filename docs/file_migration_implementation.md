# File Migration Implementation Guide

## Overview
This document outlines the implementation of the file migration system that transfers files from temporary local storage to permanent S3 storage upon successful payment completion.

## Current State
- Files are stored locally in `/tmp/audioposter/temp/` during preview generation
- Files are uploaded to S3 for waveform generation
- **Missing**: Automatic migration of files to permanent S3 storage after payment

## Implementation Requirements

### 1. Database Schema Updates
**File**: `backend/models.py`
- Add `permanent_photo_s3_key` field to Order model
- Add `permanent_audio_s3_key` field to Order model  
- Add `permanent_waveform_s3_key` field to Order model
- Add `permanent_pdf_s3_key` field to Order model
- Add `migration_status` field (pending, completed, failed)
- Add `migration_completed_at` timestamp

### 2. Storage Manager Updates
**File**: `backend/services/storage_manager.py`
- Add `migrate_file_to_permanent()` method
- Add `migrate_all_session_files()` method
- Add `verify_migration_success()` method
- Add `rollback_migration()` method for error handling

### 3. Payment Flow Integration
**File**: `backend/main.py` (complete_order endpoint)
- After successful payment, trigger file migration
- Update Order model with permanent S3 keys
- Verify all files migrated successfully
- Rollback payment if migration fails

### 4. QR Code Updates
**File**: `backend/services/pdf_generator.py` and `backend/services/visual_pdf_generator.py`
- Update `_generate_qr_url()` to use 5-year expiration for paid versions
- Ensure QR codes point to permanent S3 files for paid orders

### 5. Cleanup Task Updates
**File**: `backend/tasks.py`
- Remove session-based file deletion
- Keep only manual cleanup for files older than 7 days
- Disable automated cleanup tasks

## Implementation Steps

### Step 1: Update Database Schema
```python
# Add to Order model in backend/models.py
permanent_photo_s3_key = Column(String(500), nullable=True)
permanent_audio_s3_key = Column(String(500), nullable=True)
permanent_waveform_s3_key = Column(String(500), nullable=True)
permanent_pdf_s3_key = Column(String(500), nullable=True)
migration_status = Column(String(50), default='pending')
migration_completed_at = Column(DateTime, nullable=True)
```

### Step 2: Implement Storage Manager Methods
```python
# Add to StorageManager class
async def migrate_file_to_permanent(self, temp_key: str, permanent_key: str) -> bool:
    """Migrate a single file from temp to permanent storage"""
    
async def migrate_all_session_files(self, session_token: str, order_id: str) -> dict:
    """Migrate all files for a session to permanent storage"""
    
def verify_migration_success(self, permanent_keys: list) -> bool:
    """Verify all permanent files exist in S3"""
    
async def rollback_migration(self, permanent_keys: list) -> bool:
    """Rollback migration by deleting permanent files"""
```

### Step 3: Update Payment Flow
```python
# In complete_order endpoint
# After successful payment:
1. Get session data
2. Call migrate_all_session_files()
3. Update Order with permanent S3 keys
4. Verify migration success
5. If migration fails, rollback payment
6. Return success/failure response
```

### Step 4: Update QR Code Generation
```python
# In _generate_qr_url methods
# For paid orders, use 5-year expiration:
expiration = 86400 * 365 * 5  # 5 years
```

### Step 5: Update Cleanup Tasks
```python
# Remove session-based cleanup
# Keep only manual cleanup for files older than 7 days
# Disable automated tasks
```

## Error Handling
- **Migration Failure**: Rollback payment, log error, notify admin
- **Partial Migration**: Rollback all files, retry migration
- **S3 Errors**: Retry with exponential backoff
- **File Not Found**: Log error, skip migration for that file

## Testing
- Test successful migration flow
- Test migration failure scenarios
- Test rollback functionality
- Test QR code generation with permanent files
- Test cleanup tasks with new logic

## Monitoring
- Log all migration operations
- Track migration success/failure rates
- Monitor S3 storage costs
- Alert on migration failures

## Security Considerations
- Verify file ownership before migration
- Use presigned URLs for secure file transfer
- Encrypt files during transfer
- Validate file integrity after migration

## Performance Considerations
- Use async operations for file transfers
- Implement retry logic for failed transfers
- Monitor transfer speeds and optimize if needed
- Consider using S3 transfer acceleration for large files
