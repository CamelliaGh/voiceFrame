#!/usr/bin/env python3
"""
Mock pattern validation script to catch incorrect mocking patterns.
"""
import ast
import sys
from pathlib import Path

def validate_mock_patterns(file_path):
    """Validate mock patterns in test files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file
        tree = ast.parse(content)
        
        issues = []
        
        # Check for problematic @patch.object patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for @patch.object decorators
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'object' and
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'patch'):
                    
                    if len(node.args) >= 2:
                        class_name = node.args[0]
                        attribute_name = node.args[1]
                        
                        # Check if it's trying to patch instance attributes that are created in __init__
                        if (isinstance(class_name, ast.Name) and
                            isinstance(attribute_name, ast.Constant) and
                            class_name.id in ['PDFGenerator', 'VisualPDFGenerator'] and
                            attribute_name.value in ['file_uploader', 'template_service', 'image_processor']):
                            
                            issues.append(f"Potentially incorrect @patch.object for {class_name.id}.{attribute_name.value} - consider mocking instance attributes instead")
        
        # Check for missing imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Check for TestClient usage without import
        if 'TestClient' in content and 'fastapi.testclient' not in imports:
            issues.append("TestClient used but not imported from fastapi.testclient")
        
        # Check for ValidationError usage without import
        if 'ValidationError' in content and 'pydantic' not in imports:
            issues.append("ValidationError used but pydantic not imported")
        
        if issues:
            print(f"❌ Mock pattern issues in {file_path}:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print(f"✅ Mock pattern validation passed for {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating mock patterns...")
    
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
        if not validate_mock_patterns(test_file):
            all_valid = False
    
    if all_valid:
        print("\n🎉 All mock pattern validation passed!")
        return True
    else:
        print("\n❌ Some mock pattern issues found. Please review the suggestions above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
