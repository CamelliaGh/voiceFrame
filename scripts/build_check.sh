#!/bin/bash

# Build verification script to catch common errors before running tests

echo "🔍 Running build verification..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run from project root."
    exit 1
fi

# Check Python syntax
echo "📝 Checking Python syntax..."
if ! python -m py_compile backend/**/*.py 2>/dev/null; then
    echo "❌ Python syntax errors found. Please fix before running tests."
    exit 1
fi
echo "✅ Python syntax check passed"

# Check imports (if we can run Python)
echo "📦 Checking imports..."
if python scripts/validate_imports.py; then
    echo "✅ Import validation passed"
else
    echo "❌ Import validation failed. Please fix missing imports."
    exit 1
fi

# Check if Docker is running
echo "🐳 Checking Docker..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker before running tests."
    exit 1
fi
echo "✅ Docker is running"

# Check if test dependencies are available in Docker
echo "🧪 Checking test environment..."
if docker-compose run --rm test python -c "import fastapi, pytest; print('Test dependencies available')" 2>/dev/null; then
    echo "✅ Test environment is ready"
else
    echo "❌ Test environment not ready. Please run: docker-compose build test"
    exit 1
fi

echo ""
echo "🎉 Build verification complete! Ready to run tests."
echo "💡 To run tests: docker-compose run --rm test"
