#!/usr/bin/env python3
"""
Import validation script to catch missing imports before running tests.
"""
import ast
import os
import sys
from pathlib import Path


def validate_imports(file_path):
    """Validate that all imports in a file are available"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the file
        tree = ast.parse(content)

        # Check imports
        missing_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        __import__(alias.name)
                    except ImportError as e:
                        missing_imports.append(f"Import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        __import__(node.module)
                    except ImportError as e:
                        missing_imports.append(f"From import: {node.module}")

        if missing_imports:
            print(f"❌ Missing imports in {file_path}:")
            for missing in missing_imports:
                print(f"   - {missing}")
            return False
        else:
            print(f"✅ All imports valid in {file_path}")
            return True

    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False


def main():
    """Main validation function"""
    print("🔍 Validating imports in test files...")

    # Find all test files
    test_dir = Path("backend/tests")
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False

    test_files = list(test_dir.glob("*.py"))
    if not test_files:
        print(f"❌ No test files found in {test_dir}")
        return False

    all_valid = True

    for test_file in test_files:
        if not validate_imports(test_file):
            all_valid = False

    if all_valid:
        print("\n🎉 All imports validated successfully!")
        return True
    else:
        print("\n❌ Some imports are missing. Please fix before running tests.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
