#!/usr/bin/env python3
"""
Validate Docker environment consistency to prevent container runtime errors.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


def parse_dockerfile(file_path: Path) -> Dict[str, List[str]]:
    """Parse a Dockerfile and extract key information."""
    info = {
        "base_image": None,
        "system_packages": [],
        "python_packages": [],
        "requirements_files": [],
        "environment_vars": [],
        "commands": [],
    }

    if not file_path.exists():
        return info

    with open(file_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # Base image
        if line.startswith("FROM "):
            info["base_image"] = line.split()[1]

        # System packages
        elif "apt-get install" in line:
            # Extract package names from apt-get install
            packages = re.findall(r"\\?\s+([a-zA-Z0-9\-_]+)", line)
            info["system_packages"].extend(packages)

        # Python packages
        elif "pip install" in line:
            if "-r " in line:
                # Extract requirements file
                req_file = re.search(r"-r\s+([^\s]+)", line)
                if req_file:
                    info["requirements_files"].append(req_file.group(1))
            else:
                # Direct package installation
                packages = re.findall(r"([a-zA-Z0-9\-_\[\]]+)", line)
                info["python_packages"].extend(packages)

        # Environment variables
        elif line.startswith("ENV "):
            env_var = line[4:].strip()
            info["environment_vars"].append(env_var)

        # Commands
        elif line.startswith("CMD ") or line.startswith("RUN "):
            info["commands"].append(line)

    return info


def parse_docker_compose(file_path: Path) -> Dict[str, Dict]:
    """Parse docker-compose.yml and extract service information."""
    services = {}

    if not file_path.exists():
        return services

    with open(file_path, "r") as f:
        content = f.read()

    # Simple YAML parsing for docker-compose
    service_pattern = r"(\w+):\s*\n((?:\s+.*\n)*)"
    matches = re.finditer(service_pattern, content)

    for match in matches:
        service_name = match.group(1)
        service_content = match.group(2)

        service_info = {
            "build": None,
            "environment": [],
            "volumes": [],
            "depends_on": [],
            "command": None,
        }

        # Extract build context
        build_match = re.search(r"build:\s*(.+)", service_content)
        if build_match:
            service_info["build"] = build_match.group(1).strip()

        # Extract environment variables
        env_matches = re.findall(r"-\s*([^:\n]+):\s*(.+)", service_content)
        for env_var, env_value in env_matches:
            service_info["environment"].append(f"{env_var}={env_value}")

        # Extract volumes
        volume_matches = re.findall(r"-\s*([^:\n]+):\s*(.+)", service_content)
        for volume_source, volume_target in volume_matches:
            if ":" in volume_source:  # This is a volume mount
                service_info["volumes"].append(f"{volume_source}:{volume_target}")

        # Extract depends_on
        depends_matches = re.findall(
            r"(\w+):\s*\n\s*condition:\s*(\w+)", service_content
        )
        for dep_service, condition in depends_matches:
            service_info["depends_on"].append(f"{dep_service}:{condition}")

        # Extract command
        cmd_match = re.search(r"command:\s*(.+)", service_content)
        if cmd_match:
            service_info["command"] = cmd_match.group(1).strip()

        services[service_name] = service_info

    return services


def validate_docker_consistency():
    """Main validation function."""
    project_root = Path(__file__).parent.parent

    print("🐳 Validating Docker consistency...")

    # Parse Docker files
    dockerfile = parse_dockerfile(project_root / "Dockerfile")
    dockerfile_test = parse_dockerfile(project_root / "Dockerfile.test")
    docker_compose = parse_docker_compose(project_root / "docker-compose.yml")

    issues = []

    # Check base image consistency
    if dockerfile["base_image"] and dockerfile_test["base_image"]:
        if dockerfile["base_image"] != dockerfile_test["base_image"]:
            issues.append(
                f"Base image mismatch: {dockerfile['base_image']} vs {dockerfile_test['base_image']}"
            )

    # Check system packages consistency
    prod_packages = set(dockerfile["system_packages"])
    test_packages = set(dockerfile_test["system_packages"])

    missing_in_test = prod_packages - test_packages
    if missing_in_test:
        issues.append(f"Missing system packages in test Dockerfile: {missing_in_test}")

    # Check requirements files
    prod_req_files = set(dockerfile["requirements_files"])
    test_req_files = set(dockerfile_test["requirements_files"])

    if "requirements.txt" not in prod_req_files:
        issues.append("Production Dockerfile missing requirements.txt")

    if "requirements.txt" not in test_req_files:
        issues.append("Test Dockerfile missing requirements.txt")

    if "backend/requirements-test.txt" not in test_req_files:
        issues.append("Test Dockerfile missing backend/requirements-test.txt")

    # Check docker-compose service consistency
    for service_name, service_info in docker_compose.items():
        if service_info["build"] == ".":
            # This service uses the main Dockerfile
            if "celery" in service_name.lower():
                # Celery services should have same environment as API
                api_service = docker_compose.get("api", {})
                if api_service.get("environment") != service_info.get("environment"):
                    issues.append(
                        f"Environment mismatch between api and {service_name}"
                    )

    # Check for required system packages
    required_packages = {
        "ffmpeg",
        "libsndfile1",
        "libsndfile1-dev",
        "gcc",
        "g++",
        "libpq-dev",
        "curl",
    }

    missing_packages = required_packages - prod_packages
    if missing_packages:
        issues.append(f"Missing required system packages: {missing_packages}")

    # Check for required Python packages in requirements files
    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, "r") as f:
            requirements_content = f.read()

        required_python_packages = {
            "psutil",
            "celery",
            "boto3",
            "pillow",
            "librosa",
            "soundfile",
            "pydub",
            "matplotlib",
            "scipy",
            "reportlab",
            "qrcode",
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "redis",
            "stripe",
            "sendgrid",
        }

        missing_python_packages = []
        for package in required_python_packages:
            if package not in requirements_content:
                missing_python_packages.append(package)

        if missing_python_packages:
            issues.append(
                f"Missing required Python packages: {missing_python_packages}"
            )

    # Report issues
    if issues:
        print("❌ Docker consistency issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Docker consistency validation passed!")
        return True


if __name__ == "__main__":
    success = validate_docker_consistency()
    sys.exit(0 if success else 1)
