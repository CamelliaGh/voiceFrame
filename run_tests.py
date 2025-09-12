#!/usr/bin/env python3
"""
Test runner script for AudioPoster backend
Run this after each change to ensure nothing is broken
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests and return success status"""
    print("🧪 Running AudioPoster Backend Tests")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Install test dependencies
    print("📦 Installing test dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True, capture_output=True)
        print("✅ Test dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install test dependencies: {e}")
        return False
    
    # Run tests
    print("\n🔍 Running tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], check=True)
        
        print("\n✅ All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"🧪 Running {test_file}")
    print("=" * 50)
    
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/{test_file}", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], check=True)
        
        print(f"\n✅ {test_file} tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {test_file} tests failed with exit code {e.returncode}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        success = run_specific_test(test_file)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)
