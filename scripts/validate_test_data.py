#!/usr/bin/env python3
"""
Test data validation script to catch UUID and data structure issues.
"""
import ast
import sys
import re
from pathlib import Path

def validate_test_data(file_path):
    """Validate test data creation patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file
        tree = ast.parse(content)
        
        issues = []
        
        # Check for hardcoded UUID strings
        uuid_pattern = r'id=["\']test-[^"\']*["\']'
        matches = re.findall(uuid_pattern, content)
        if matches:
            issues.append(f"Hardcoded UUID strings found: {matches}")
        
        # Check for SessionModel/Order creation with hardcoded IDs
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's creating a model with hardcoded ID
                if (isinstance(node.func, ast.Name) and 
                    node.func.id in ['SessionModel', 'Order', 'TestSessionModel', 'TestOrder']):
                    
                    for keyword in node.keywords:
                        if (keyword.arg == 'id' and 
                            isinstance(keyword.value, ast.Constant) and
                            isinstance(keyword.value.value, str) and
                            keyword.value.value.startswith('test-')):
                            
                            issues.append(f"Hardcoded ID '{keyword.value.value}' in {node.func.id} creation")
        
        if issues:
            print(f"❌ Test data issues in {file_path}:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print(f"✅ Test data validation passed for {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating test data patterns...")
    
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
        if not validate_test_data(test_file):
            all_valid = False
    
    if all_valid:
        print("\n🎉 All test data validation passed!")
        return True
    else:
        print("\n❌ Some test data issues found. Please use proper UUID generation.")
        print("💡 Use: import uuid; id=str(uuid.uuid4())")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
