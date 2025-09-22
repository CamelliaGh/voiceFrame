#!/bin/bash

# Setup script for test workflow
# This script installs pre-commit hooks and sets up the test environment

set -e

echo "🚀 Setting up test workflow..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run from project root."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

print_success "Python 3 is available"

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    print_status "Installing pre-commit..."
    if pip install pre-commit; then
        print_success "Pre-commit installed successfully"
    else
        print_error "Failed to install pre-commit"
        exit 1
    fi
else
    print_success "Pre-commit is already installed"
fi

# Install pre-commit hooks
print_status "Installing pre-commit hooks..."
if pre-commit install; then
    print_success "Pre-commit hooks installed successfully"
else
    print_error "Failed to install pre-commit hooks"
    exit 1
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/*.sh
chmod +x scripts/*.py
print_success "Scripts are now executable"

# Test Docker availability
print_status "Checking Docker availability..."
if docker info >/dev/null 2>&1; then
    print_success "Docker is available"
    
    # Build test environment
    print_status "Building test environment..."
    if docker-compose build test; then
        print_success "Test environment built successfully"
    else
        print_warning "Failed to build test environment. You can build it later with: docker-compose build test"
    fi
else
    print_warning "Docker is not available. Please start Docker to run tests."
fi

# Run initial validation
print_status "Running initial validation..."
if python scripts/validate_imports.py; then
    print_success "Import validation passed"
else
    print_warning "Import validation failed. This is expected if dependencies are not installed locally."
fi

# Create .gitignore entry for test reports
if [ ! -f ".gitignore" ]; then
    touch .gitignore
fi

if ! grep -q "test_report_*.txt" .gitignore; then
    echo "test_report_*.txt" >> .gitignore
    print_success "Added test report files to .gitignore"
fi

# Summary
echo ""
echo "🎉 Test workflow setup completed!"
echo ""
echo "What was installed:"
echo "  ✅ Pre-commit hooks"
echo "  ✅ Executable validation scripts"
echo "  ✅ Test environment (if Docker available)"
echo ""
echo "Next steps:"
echo "  1. Run validation: python scripts/validate_imports.py"
echo "  2. Run full test workflow: ./scripts/test_workflow.sh"
echo "  3. Test pre-commit hooks: pre-commit run --all-files"
echo ""
echo "💡 For more information, see docs/TEST_WORKFLOW.md"
echo ""
