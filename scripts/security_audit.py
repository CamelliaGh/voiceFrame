#!/usr/bin/env python3
"""
Security Audit Script

This script performs a comprehensive security audit of the AudioPoster application
to identify hardcoded credentials, security vulnerabilities, and configuration issues.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Comprehensive security audit tool"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.recommendations = []

        # Patterns to detect hardcoded credentials
        self.credential_patterns = {
            'api_keys': [
                r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
                r'access[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
                r'secret[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
                r'token\s*=\s*["\'][^"\']{20,}["\']',
            ],
            'passwords': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'pwd\s*=\s*["\'][^"\']+["\']',
                r'pass\s*=\s*["\'][^"\']+["\']',
            ],
            'database_urls': [
                r'postgresql://[^:]+:[^@]+@',
                r'mysql://[^:]+:[^@]+@',
                r'mongodb://[^:]+:[^@]+@',
            ],
            'aws_credentials': [
                r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
                r'[A-Za-z0-9/+=]{40}',  # AWS Secret Access Key
            ],
            'stripe_keys': [
                r'sk_[a-z]+_[a-zA-Z0-9]{24,}',
                r'pk_[a-z]+_[a-zA-Z0-9]{24,}',
            ],
            'sendgrid_keys': [
                r'SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}',
            ]
        }

        # Default/example values that should not be used in production
        self.default_values = [
            'your-secret-key-change-this',
            'your-super-secret-key-change-this-in-production',
            'your_aws_access_key',
            'your_aws_secret_key',
            'sk_test_your_stripe_secret_key',
            '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',
            'audioposter_password',
            'password',
            '123456',
            'admin',
            'test',
            'example',
            'dummy',
            'placeholder'
        ]

        # File extensions to scan
        self.scan_extensions = ['.py', '.js', '.ts', '.tsx', '.json', '.yml', '.yaml', '.env', '.ini', '.cfg']

        # Directories to exclude
        self.exclude_dirs = [
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'dist', 'build', '.venv', 'venv', 'env'
        ]

    def run_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        logger.info("Starting security audit...")

        # Scan for hardcoded credentials
        self._scan_hardcoded_credentials()

        # Check environment configuration
        self._check_environment_config()

        # Check file permissions
        self._check_file_permissions()

        # Check for security headers
        self._check_security_headers()

        # Check dependencies for vulnerabilities
        self._check_dependencies()

        # Generate report
        return self._generate_report()

    def _scan_hardcoded_credentials(self):
        """Scan for hardcoded credentials in source files"""
        logger.info("Scanning for hardcoded credentials...")

        for file_path in self._get_files_to_scan():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    line_number = 0

                    for line in content.split('\n'):
                        line_number += 1

                        # Check for credential patterns
                        for category, patterns in self.credential_patterns.items():
                            for pattern in patterns:
                                if re.search(pattern, line, re.IGNORECASE):
                                    self.issues.append({
                                        'type': 'hardcoded_credential',
                                        'category': category,
                                        'file': str(file_path.relative_to(self.project_root)),
                                        'line': line_number,
                                        'content': line.strip(),
                                        'severity': 'high'
                                    })

                        # Check for default values
                        for default_value in self.default_values:
                            if default_value in line.lower():
                                self.warnings.append({
                                    'type': 'default_value',
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': line_number,
                                    'content': line.strip(),
                                    'default_value': default_value,
                                    'severity': 'medium'
                                })

            except Exception as e:
                logger.warning(f"Error scanning {file_path}: {e}")

    def _check_environment_config(self):
        """Check environment configuration security"""
        logger.info("Checking environment configuration...")

        env_file = self.project_root / '.env'
        env_example = self.project_root / 'env.example'

        # Check if .env file exists and is in .gitignore
        if env_file.exists():
            gitignore_file = self.project_root / '.gitignore'
            if gitignore_file.exists():
                with open(gitignore_file, 'r') as f:
                    gitignore_content = f.read()
                    if '.env' not in gitignore_content:
                        self.issues.append({
                            'type': 'env_file_not_ignored',
                            'file': '.gitignore',
                            'severity': 'high',
                            'description': '.env file is not in .gitignore'
                        })
        else:
            self.warnings.append({
                'type': 'no_env_file',
                'severity': 'low',
                'description': 'No .env file found - using environment variables or defaults'
            })

        # Check env.example for hardcoded values
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
                for default_value in self.default_values:
                    if default_value in content:
                        self.warnings.append({
                            'type': 'example_file_contains_defaults',
                            'file': 'env.example',
                            'default_value': default_value,
                            'severity': 'low',
                            'description': f'Example file contains default value: {default_value}'
                        })

    def _check_file_permissions(self):
        """Check file permissions for security issues"""
        logger.info("Checking file permissions...")

        sensitive_files = ['.env', 'config.py', 'docker-compose.yml']

        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                stat = file_path.stat()
                # Check if file is world-readable (permission 644 or more permissive)
                if stat.st_mode & 0o004:
                    self.warnings.append({
                        'type': 'world_readable_file',
                        'file': file_name,
                        'severity': 'medium',
                        'description': f'{file_name} is world-readable'
                    })

    def _check_security_headers(self):
        """Check if security headers are implemented"""
        logger.info("Checking security headers implementation...")

        middleware_file = self.project_root / 'backend' / 'middleware' / 'security_headers.py'
        if not middleware_file.exists():
            self.issues.append({
                'type': 'missing_security_headers',
                'severity': 'medium',
                'description': 'Security headers middleware not implemented'
            })
        else:
            self.recommendations.append({
                'type': 'security_headers_implemented',
                'description': 'Security headers middleware is implemented'
            })

    def _check_dependencies(self):
        """Check dependencies for known vulnerabilities"""
        logger.info("Checking dependencies for vulnerabilities...")

        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            try:
                # Try to run safety check if available
                result = subprocess.run(
                    ['safety', 'check', '-r', str(requirements_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    self.warnings.append({
                        'type': 'dependency_vulnerabilities',
                        'severity': 'medium',
                        'description': 'Potential dependency vulnerabilities found',
                        'details': result.stdout
                    })
                else:
                    self.recommendations.append({
                        'type': 'dependencies_secure',
                        'description': 'No known dependency vulnerabilities found'
                    })

            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.warnings.append({
                    'type': 'safety_check_unavailable',
                    'severity': 'low',
                    'description': 'Safety tool not available - install with: pip install safety'
                })

    def _get_files_to_scan(self) -> List[Path]:
        """Get list of files to scan for security issues"""
        files = []

        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                    continue

                # Check file extension
                if file_path.suffix in self.scan_extensions:
                    files.append(file_path)

        return files

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security audit report"""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_recommendations = len(self.recommendations)

        # Calculate severity breakdown
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}

        for issue in self.issues:
            severity_counts[issue.get('severity', 'medium')] += 1

        for warning in self.warnings:
            severity_counts[warning.get('severity', 'low')] += 1

        report = {
            'summary': {
                'total_issues': total_issues,
                'total_warnings': total_warnings,
                'total_recommendations': total_recommendations,
                'severity_breakdown': severity_counts,
                'overall_risk': self._calculate_overall_risk()
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'next_steps': self._generate_next_steps()
        }

        return report

    def _calculate_overall_risk(self) -> str:
        """Calculate overall security risk level"""
        high_issues = sum(1 for issue in self.issues if issue.get('severity') == 'high')
        medium_issues = sum(1 for issue in self.issues if issue.get('severity') == 'medium')

        if high_issues > 0:
            return 'HIGH'
        elif medium_issues > 3:
            return 'MEDIUM'
        elif medium_issues > 0 or len(self.warnings) > 5:
            return 'LOW'
        else:
            return 'MINIMAL'

    def _generate_next_steps(self) -> List[str]:
        """Generate recommended next steps"""
        steps = []

        if any(issue['type'] == 'hardcoded_credential' for issue in self.issues):
            steps.append("Replace all hardcoded credentials with environment variables")
            steps.append("Use a secrets management service (AWS Secrets Manager, Azure Key Vault, etc.)")

        if any(issue['type'] == 'env_file_not_ignored' for issue in self.issues):
            steps.append("Add .env file to .gitignore")

        if any(issue['type'] == 'missing_security_headers' for issue in self.issues):
            steps.append("Implement security headers middleware")

        if any(warning['type'] == 'dependency_vulnerabilities' for warning in self.warnings):
            steps.append("Update vulnerable dependencies")
            steps.append("Set up automated dependency scanning in CI/CD")

        steps.extend([
            "Enable HTTPS in production",
            "Implement proper authentication and authorization",
            "Set up security monitoring and logging",
            "Conduct regular security audits",
            "Implement input validation and sanitization",
            "Set up automated security testing"
        ])

        return steps

def main():
    """Main function to run security audit"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."

    auditor = SecurityAuditor(project_root)
    report = auditor.run_audit()

    # Print summary
    print("\n" + "="*60)
    print("SECURITY AUDIT REPORT")
    print("="*60)

    summary = report['summary']
    print(f"Overall Risk Level: {summary['overall_risk']}")
    print(f"Total Issues: {summary['total_issues']}")
    print(f"Total Warnings: {summary['total_warnings']}")
    print(f"Total Recommendations: {summary['total_recommendations']}")

    print(f"\nSeverity Breakdown:")
    for severity, count in summary['severity_breakdown'].items():
        print(f"  {severity.upper()}: {count}")

    # Print issues
    if report['issues']:
        print(f"\n🚨 SECURITY ISSUES ({len(report['issues'])}):")
        for issue in report['issues']:
            print(f"  [{issue['severity'].upper()}] {issue['type']}")
            if 'file' in issue:
                print(f"    File: {issue['file']}:{issue.get('line', 'N/A')}")
            print(f"    Description: {issue.get('description', 'No description')}")
            if 'content' in issue:
                print(f"    Content: {issue['content'][:100]}...")
            print()

    # Print warnings
    if report['warnings']:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
        for warning in report['warnings']:
            print(f"  [{warning['severity'].upper()}] {warning['type']}")
            if 'file' in warning:
                print(f"    File: {warning['file']}:{warning.get('line', 'N/A')}")
            print(f"    Description: {warning.get('description', 'No description')}")
            print()

    # Print recommendations
    if report['recommendations']:
        print(f"\n✅ RECOMMENDATIONS ({len(report['recommendations'])}):")
        for rec in report['recommendations']:
            print(f"  - {rec['description']}")

    # Print next steps
    if report['next_steps']:
        print(f"\n📋 NEXT STEPS:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"  {i}. {step}")

    # Save detailed report
    report_file = Path(project_root) / 'security_audit_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    if summary['overall_risk'] in ['HIGH', 'MEDIUM']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
