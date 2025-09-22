# Test Workflow Quick Reference

## 🚀 Quick Start

```bash
# Setup test workflow (run once)
./scripts/setup_test_workflow.sh

# Run full test workflow
./scripts/test_workflow.sh

# Run individual validation checks
python scripts/validate_imports.py
python scripts/validate_test_data.py
python scripts/validate_mock_patterns.py
```

## 🔧 Common Commands

### Validation Checks
```bash
# Check imports
python scripts/validate_imports.py

# Check test data patterns
python scripts/validate_test_data.py

# Check mock patterns
python scripts/validate_mock_patterns.py

# Build verification
./scripts/build_check.sh
```

### Testing
```bash
# Quick tests
docker-compose run --rm test python -m pytest backend/tests/test_simple.py -v

# All tests
docker-compose run --rm test python -m pytest backend/tests/ -v

# Specific test file
docker-compose run --rm test python -m pytest backend/tests/test_session_update.py -v
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run test-imports
```

## 🐛 Common Issues & Fixes

### 1. Import Errors
**Error:** `NameError: name 'TestClient' is not defined`

**Fix:**
```python
# Add import at top of test file
from fastapi.testclient import TestClient
```

### 2. UUID Errors
**Error:** `'str' object has no attribute 'hex'`

**Fix:**
```python
# Use proper UUID generation
import uuid
session = SessionModel(id=str(uuid.uuid4()))

# Instead of hardcoded strings
# session = SessionModel(id="test-session-id")  # ❌
```

### 3. Mock Attribute Errors
**Error:** `AttributeError: <class 'PDFGenerator'> does not have the attribute 'file_uploader'`

**Fix:**
```python
# Mock instance attributes directly
def test_example(self, pdf_generator):
    pdf_generator.file_uploader.file_exists.return_value = True

# Instead of class-level patching
# @patch.object(PDFGenerator, 'file_uploader')  # ❌
```

### 4. Validation Error Mismatches
**Error:** `AssertionError: Regex pattern did not match`

**Fix:**
```python
# Use correct exception type for Pydantic V2
from pydantic import ValidationError
with pytest.raises(ValidationError, match="Input should be 'square' or 'circle'"):
    SessionUpdate(photo_shape="invalid")

# Instead of ValueError
# with pytest.raises(ValueError, match="Photo shape must be either"):  # ❌
```

## 📋 Checklist Before Committing

- [ ] Run `python scripts/validate_imports.py`
- [ ] Run `python scripts/validate_test_data.py`
- [ ] Run `python scripts/validate_mock_patterns.py`
- [ ] Run `./scripts/build_check.sh`
- [ ] Run `pre-commit run --all-files`
- [ ] Run `./scripts/test_workflow.sh` (optional, for full validation)

## 🎯 Best Practices

### Test Data Creation
```python
# ✅ DO: Use proper UUID generation
import uuid
@pytest.fixture
def mock_session(self):
    return SessionModel(
        id=str(uuid.uuid4()),
        session_token="test-session-token",
        # ... other fields
    )
```

### Mocking Patterns
```python
# ✅ DO: Mock instance attributes
def test_example(self, pdf_generator):
    pdf_generator.file_uploader.file_exists.return_value = True
    result = pdf_generator.some_method()
    pdf_generator.file_uploader.file_exists.assert_called_once()
```

### Validation Testing
```python
# ✅ DO: Use correct exception types
from pydantic import ValidationError
with pytest.raises(ValidationError, match="Input should be 'square' or 'circle'"):
    SessionUpdate(photo_shape="invalid")
```

### Import Management
```python
# ✅ DO: Import all required dependencies
import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import ValidationError
```

## 🚨 Emergency Fixes

### If tests are completely broken:
```bash
# Rebuild everything
docker-compose down
docker-compose build test
./scripts/test_workflow.sh
```

### If pre-commit hooks are failing:
```bash
# Skip hooks temporarily
git commit --no-verify -m "Your commit message"

# Or fix and re-run
pre-commit run --all-files
```

### If Docker is not working:
```bash
# Check Docker status
docker info

# Restart Docker
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop  # macOS/Windows
```

## 📞 Getting Help

1. **Check the logs:** Look at the output of validation scripts
2. **Read the rules:** Check `.cursor/rules/` for detailed patterns
3. **Run individual checks:** Use specific validation scripts
4. **Check Docker:** Ensure Docker is running and test environment is built

## 🔗 Related Files

- **Rules:** `.cursor/rules/testing.mdc`, `.cursor/rules/database.mdc`, `.cursor/rules/mocking.mdc`
- **Scripts:** `scripts/validate_*.py`, `scripts/test_workflow.sh`
- **Config:** `.pre-commit-config.yaml`, `.github/workflows/test.yml`
- **Docs:** `docs/TEST_WORKFLOW.md`, `docs/TEST_QUICK_REFERENCE.md`
