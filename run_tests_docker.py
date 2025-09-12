#!/usr/bin/env python3
"""
Docker-based test runner script for AudioPoster backend
Uses Docker to ensure consistent environment and avoid dependency conflicts
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests_docker():
    """Run all tests using Docker and return success status"""
    print("🧪 Running AudioPoster Backend Tests (Docker)")
    print("=" * 50)
    
    # Check if Docker is running
    try:
        subprocess.run(["docker", "ps"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ Docker is not running. Please start Docker and try again.")
        return False
    
    # Build the test image
    print("🔨 Building test image...")
    try:
        subprocess.run([
            "docker", "build", 
            "-t", "audioposter-test",
            "-f", "Dockerfile.test",
            "."
        ], check=True)
        print("✅ Test image built successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build test image: {e}")
        return False
    
    # Run tests in Docker
    print("\n🔍 Running tests in Docker...")
    try:
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{Path.cwd()}/backend:/app/backend",
            "audioposter-test",
            "python", "-m", "pytest", 
            "backend/tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], check=True)
        
        print("\n✅ All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False

def run_specific_test_docker(test_file):
    """Run a specific test file using Docker"""
    print(f"🧪 Running {test_file} (Docker)")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{Path.cwd()}/backend:/app/backend",
            "audioposter-test",
            "python", "-m", "pytest", 
            f"backend/tests/{test_file}", 
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
        success = run_specific_test_docker(test_file)
    else:
        # Run all tests
        success = run_tests_docker()
    
    sys.exit(0 if success else 1)
