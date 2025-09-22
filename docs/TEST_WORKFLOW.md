# Test Workflow Documentation

This document describes the comprehensive test workflow implemented to prevent common testing errors and ensure code quality.

## Overview

The test workflow consists of multiple layers of validation and testing:

1. **Pre-commit Hooks** - Catch errors before code is committed
2. **Validation Scripts** - Automated checks for common patterns
3. **Test Suite** - Comprehensive testing in Docker environment
4. **CI/CD Pipeline** - Automated testing on GitHub Actions
5. **Manual Workflow** - Developer tools for local testing

## Pre-commit Hooks

Pre-commit hooks automatically run validation checks before each commit:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Hook Types

1. **Test Import Validation** - Ensures all required imports are present
2. **Python Syntax Check** - Validates Python syntax
3. **UUID Field Validation** - Checks for proper UUID usage in test data
4. **Mock Pattern Validation** - Validates mocking patterns
5. **Docker Build Check** - Ensures Docker environment is ready
6. **Quick Test Suite** - Runs basic tests

## Validation Scripts

### 1. Import Validation (`scripts/validate_imports.py`)

Checks that all required imports are present in test files:

```bash
python scripts/validate_imports.py
```

**What it checks:**
- Missing `TestClient` imports
- Missing mock imports (`patch`, `MagicMock`, `AsyncMock`)
- Missing model imports
- Missing service imports

### 2. Test Data Validation (`scripts/validate_test_data.py`)

Validates test data creation patterns:

```bash
python scripts/validate_test_data.py
```

**What it checks:**
- Hardcoded UUID strings (e.g., `"test-session-id"`)
- Proper UUID generation usage
- Consistent test data structure

### 3. Mock Pattern Validation (`scripts/validate_mock_patterns.py`)

Validates mocking patterns and catches common mistakes:

```bash
python scripts/validate_mock_patterns.py
```

**What it checks:**
- Incorrect `@patch.object` usage for instance attributes
- Missing imports for validation errors
- Proper mock setup patterns

### 4. Build Check (`scripts/build_check.sh`)

Comprehensive build verification:

```bash
./scripts/build_check.sh
```

**What it checks:**
- Python syntax
- Import availability
- Docker status
- Test environment readiness

## Test Workflow Script

The main test workflow script runs all validation checks and tests:

```bash
./scripts/test_workflow.sh
```

**What it does:**
1. Builds test environment
2. Runs all validation checks
3. Executes test suite
4. Generates test report
5. Provides summary and next steps

## CI/CD Pipeline

GitHub Actions automatically runs tests on push and pull requests:

**Workflow file:** `.github/workflows/test.yml`

**What it does:**
1. Sets up Python and Docker
2. Builds test environment
3. Runs all validation scripts
4. Executes comprehensive test suite
5. Generates test reports

## Manual Testing Commands

### Quick Tests
```bash
# Run simple tests
docker-compose run --rm test python -m pytest backend/tests/test_simple.py -v

# Run specific test file
docker-compose run --rm test python -m pytest backend/tests/test_session_update.py -v
```

### Full Test Suite
```bash
# Run all tests
docker-compose run --rm test python -m pytest backend/tests/ -v

# Run with coverage
docker-compose run --rm test python -m pytest backend/tests/ -v --cov=backend
```

### Integration Tests
```bash
# Run integration tests
docker-compose run --rm test python -m pytest backend/tests/test_integration.py -v
```

## Error Prevention Patterns

### 1. Import Consistency
```python
# ✅ DO: Import all required dependencies
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import ValidationError

# ❌ DON'T: Use without importing
# TestClient(app)  # NameError: name 'TestClient' is not defined
```

### 2. UUID Field Handling
```python
# ✅ DO: Use proper UUID generation
import uuid
session = SessionModel(id=str(uuid.uuid4()))

# ❌ DON'T: Use hardcoded strings
session = SessionModel(id="test-session-id")  # Database error
```

### 3. Mock Attribute Patching
```python
# ✅ DO: Mock instance attributes directly
def test_example(self, pdf_generator):
    pdf_generator.file_uploader.file_exists.return_value = True

# ❌ DON'T: Try to patch class attributes that are instance attributes
@patch.object(PDFGenerator, 'file_uploader')  # AttributeError
```

### 4. Validation Error Testing
```python
# ✅ DO: Use correct exception type for Pydantic V2
from pydantic import ValidationError
with pytest.raises(ValidationError, match="Input should be 'square' or 'circle'"):
    SessionUpdate(photo_shape="invalid")

# ❌ DON'T: Use wrong exception type
with pytest.raises(ValueError, match="Photo shape must be either"):  # Won't match
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Run: `python scripts/validate_imports.py`
   - Check: All required imports are present

2. **UUID Errors**
   - Run: `python scripts/validate_test_data.py`
   - Check: Using `str(uuid.uuid4())` instead of hardcoded strings

3. **Mock Attribute Errors**
   - Run: `python scripts/validate_mock_patterns.py`
   - Check: Mocking instance attributes, not class attributes

4. **Validation Error Mismatches**
   - Check: Using `ValidationError` for Pydantic V2 Literal fields
   - Check: Using correct error message patterns

### Docker Issues

```bash
# Rebuild test environment
docker-compose build test

# Check Docker status
docker info

# Clean up containers
docker-compose down
docker system prune -f
```

## Best Practices

1. **Always run validation checks before committing**
2. **Use the test workflow script for comprehensive testing**
3. **Follow the established patterns for test data creation**
4. **Mock instance attributes, not class attributes**
5. **Use proper exception types for validation testing**
6. **Keep test data consistent with production models**

## Integration with Development Workflow

### Before Committing
```bash
# Run pre-commit hooks
pre-commit run --all-files

# Or run individual checks
python scripts/validate_imports.py
python scripts/validate_test_data.py
python scripts/validate_mock_patterns.py
```

### Before Pushing
```bash
# Run full test workflow
./scripts/test_workflow.sh
```

### During Development
```bash
# Quick validation
./scripts/build_check.sh

# Run specific tests
docker-compose run --rm test python -m pytest backend/tests/test_specific.py -v
```

This comprehensive test workflow ensures that common testing errors are caught early and prevented from reaching production.
