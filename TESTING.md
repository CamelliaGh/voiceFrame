# AudioPoster Backend Testing Guide

## Overview

This document describes the comprehensive test suite for the AudioPoster backend, designed to ensure that all changes are properly validated and nothing is broken.

## Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_session_update.py   # Session update validation tests
├── test_file_migration.py   # File migration system tests
├── test_qr_code_expiration.py # QR code expiration tests
├── test_cleanup_tasks.py    # Cleanup task modification tests
└── test_integration.py      # End-to-end integration tests
```

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test File
```bash
python run_tests.py test_session_update.py
python run_tests.py test_file_migration.py
python run_tests.py test_qr_code_expiration.py
python run_tests.py test_cleanup_tasks.py
python run_tests.py test_integration.py
```

### Run Tests with Coverage
```bash
cd backend
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

## Test Categories

### 1. Session Update Tests (`test_session_update.py`)

**Purpose**: Validate session update functionality and schema validation

**Key Tests**:
- ✅ Valid session update data
- ✅ Handling of `None` values (as sent by frontend)
- ✅ Validation errors for invalid data
- ✅ Text validation and trimming
- ✅ API endpoint success/failure scenarios
- ✅ Missing file validation

**Critical for**: Fixing the 400 Bad Request error on session updates

### 2. File Migration Tests (`test_file_migration.py`)

**Purpose**: Test the complete file migration system from temporary to permanent storage

**Key Tests**:
- ✅ Successful migration of all file types (photo, audio, waveform)
- ✅ Migration verification
- ✅ Rollback on failure
- ✅ Error handling
- ✅ Integration with payment completion flow
- ✅ Content type detection for audio files

**Critical for**: Ensuring files are properly migrated after payment

### 3. QR Code Expiration Tests (`test_qr_code_expiration.py`)

**Purpose**: Verify QR code expiration times for paid vs unpaid versions

**Key Tests**:
- ✅ Paid versions: 5-year expiration
- ✅ Preview versions: 7-day expiration
- ✅ Missing file error handling
- ✅ Both PDF generators (visual and non-visual)

**Critical for**: Ensuring QR codes work correctly for different user types

### 4. Cleanup Task Tests (`test_cleanup_tasks.py`)

**Purpose**: Validate cleanup task modifications

**Key Tests**:
- ✅ Session cleanup only removes database records
- ✅ Keeps sessions with paid orders
- ✅ Orphaned file cleanup respects 7-day rule
- ✅ Files referenced by sessions are not deleted
- ✅ Files moved to permanent storage are not deleted

**Critical for**: Preventing accidental file deletion

### 5. Integration Tests (`test_integration.py`)

**Purpose**: End-to-end testing of the complete system

**Key Tests**:
- ✅ Complete payment flow with migration
- ✅ Migration failure handling
- ✅ Session update validation with various data
- ✅ QR code expiration differences
- ✅ Database schema updates
- ✅ Manual-only cleanup tasks

**Critical for**: Ensuring all components work together

## Test Fixtures

### Database Fixtures
- `db_session`: Fresh database session for each test
- `client`: Test client with database override
- `sample_session`: Pre-configured session for testing
- `sample_order`: Pre-configured order for testing

### Mock Fixtures
- `mock_s3_client`: Mock S3 operations
- `mock_stripe_service`: Mock payment processing
- `mock_email_service`: Mock email sending
- `mock_storage_manager`: Mock file migration

## What Each Test Validates

### Session Update Fixes
```python
# Tests that None values are handled correctly
data_with_none = {
    "custom_text": "Test text",
    "photo_shape": None,  # This was causing 400 errors
    "pdf_size": "A4",
    "template_id": "framed_a4_portrait",
    "background_id": None
}
```

### File Migration System
```python
# Tests that files are properly migrated
result = await storage_manager.migrate_all_session_files(
    session_token, order_id
)
assert "permanent_photo_s3_key" in result
assert "permanent_audio_s3_key" in result
assert "permanent_waveform_s3_key" in result
```

### QR Code Expiration
```python
# Tests different expiration times
# Preview: 7 days
assert call_args[1]['expiration'] == 86400 * 7

# Paid: 5 years  
assert call_args[1]['expiration'] == 86400 * 365 * 5
```

## Running Tests After Changes

### Before Making Changes
1. Run all tests to ensure baseline is working
2. Note any failing tests

### After Making Changes
1. Run the specific test file related to your changes
2. Run all tests to ensure nothing else broke
3. Fix any new failures

### Example Workflow
```bash
# 1. Run all tests before changes
python run_tests.py

# 2. Make your changes to the code

# 3. Run specific tests for your changes
python run_tests.py test_session_update.py

# 4. Run all tests to ensure nothing broke
python run_tests.py
```

## Test Data

Tests use in-memory SQLite database to avoid affecting production data. Each test gets a fresh database instance.

## Mocking Strategy

- **S3 Operations**: Mocked to avoid actual file uploads
- **Stripe Payments**: Mocked to avoid real payment processing
- **Email Sending**: Mocked to avoid sending actual emails
- **File System**: Mocked for file operations

## Continuous Integration

These tests should be run:
- Before each commit
- After each pull request
- Before each deployment
- After any schema changes
- After any API changes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're in the correct directory
2. **Database Errors**: Check that test database is properly configured
3. **Mock Errors**: Verify mock setup matches actual service calls
4. **Timeout Errors**: Increase timeout for slow operations

### Debug Mode
```bash
cd backend
pytest tests/ -v -s --tb=long
```

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage for core business logic
- **Integration Tests**: 80%+ coverage for API endpoints
- **Error Handling**: 100% coverage for error scenarios

## Adding New Tests

When adding new features:

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test API endpoints and workflows
3. **Error Tests**: Test error conditions and edge cases
4. **Update Fixtures**: Add new test data as needed

## Test Maintenance

- Update tests when changing APIs
- Add tests for new features
- Remove tests for deprecated features
- Keep test data realistic and up-to-date
