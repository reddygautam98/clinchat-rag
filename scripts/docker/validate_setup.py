#!/usr/bin/env python3
"""
Docker Configuration Validator for ClinChat-RAG Fusion AI System
Tests Docker setup and validates all components before deployment
"""

import os
import sys
import subprocess
import json
import time
import requests
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_info(message):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")

def log_success(message):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {message}")

def log_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.ENDC} {message}")

def log_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.ENDC} {message}")

def log_header(message):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{message}{Colors.ENDC}")
    print("=" * len(message))

def run_command(command, check=True, capture_output=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        return e

def check_docker():
    """Check if Docker is installed and running"""
    log_header("Docker Environment Check")
    
    # Check Docker installation
    result = run_command("docker --version")
    if result.returncode == 0:
        version = result.stdout.strip()
        log_success(f"Docker installed: {version}")
    else:
        log_error("Docker is not installed or not in PATH")
        return False
    
    # Check Docker Compose
    result = run_command("docker-compose --version")
    if result.returncode == 0:
        version = result.stdout.strip()
        log_success(f"Docker Compose available: {version}")
    else:
        log_error("Docker Compose is not available")
        return False
    
    # Check if Docker daemon is running
    result = run_command("docker info")
    if result.returncode == 0:
        log_success("Docker daemon is running")
    else:
        log_error("Docker daemon is not running. Please start Docker Desktop.")
        return False
    
    return True

def check_files():
    """Check if required Docker files exist"""
    log_header("Required Files Check")
    
    required_files = [
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.dev.yml", 
        ".dockerignore",
        ".env.docker",
        "requirements.txt"
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            log_success(f"✓ {file}")
        else:
            log_error(f"✗ {file} - Missing")
            all_exist = False
    
    # Check infrastructure files
    infra_files = [
        "infra/init-db.sql",
        "infra/nginx.conf",
        "infra/prometheus.yml"
    ]
    
    for file in infra_files:
        if Path(file).exists():
            log_success(f"✓ {file}")
        else:
            log_warning(f"⚠ {file} - Optional but recommended")
    
    return all_exist

def validate_compose():
    """Validate Docker Compose configuration"""
    log_header("Docker Compose Validation")
    
    # Test compose file syntax
    result = run_command("docker-compose config --quiet")
    if result.returncode == 0:
        log_success("Docker Compose syntax is valid")
    else:
        log_error(f"Docker Compose validation failed: {result.stderr}")
        return False
    
    # Check if we can parse the config
    result = run_command("docker-compose config")
    if result.returncode == 0:
        log_success("Docker Compose configuration can be parsed")
        
        # Check for required services
        required_services = ["clinchat-rag", "postgres", "redis", "chroma"]
        config_output = result.stdout
        
        for service in required_services:
            if service in config_output:
                log_success(f"✓ Service '{service}' configured")
            else:
                log_warning(f"⚠ Service '{service}' not found")
    else:
        log_error("Failed to parse Docker Compose configuration")
        return False
    
    return True

def check_environment():
    """Check environment configuration"""
    log_header("Environment Configuration Check")
    
    # Check if .env file exists
    env_files = [".env", ".env.docker"]
    env_file = None
    
    for ef in env_files:
        if Path(ef).exists():
            env_file = ef
            log_success(f"Environment file found: {ef}")
            break
    
    if not env_file:
        log_warning("No environment file found. You'll need to create .env before deployment.")
        return True
    
    # Check for required environment variables
    required_vars = [
        "GOOGLE_API_KEY",
        "GROQ_API_KEY"
    ]
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    for var in required_vars:
        if var in env_content and not env_content.split(f"{var}=")[1].split('\n')[0].strip() in ["", "your_api_key_here"]:
            log_success(f"✓ {var} configured")
        else:
            log_warning(f"⚠ {var} not configured or using placeholder")
    
    return True

def test_build():
    """Test Docker image build"""
    log_header("Docker Image Build Test")
    
    log_info("Testing Docker build (this may take a few minutes)...")
    
    # Test build with cache
    result = run_command("docker-compose build --quiet clinchat-rag", check=False)
    
    if result.returncode == 0:
        log_success("Docker image builds successfully")
        
        # Check if image was created
        result = run_command("docker images clinchat-rag-clinchat-rag")
        if result.returncode == 0:
            log_success("Docker image created and available")
        else:
            log_warning("Build succeeded but image not found in docker images")
        
        return True
    else:
        log_error(f"Docker build failed: {result.stderr}")
        return False

def check_ports():
    """Check if required ports are available"""
    log_header("Port Availability Check")
    
    required_ports = [8002, 5432, 6379, 8001, 9091, 3000, 80]
    
    for port in required_ports:
        # On Windows, use PowerShell to check ports
        if os.name == 'nt':
            result = run_command(f"powershell \"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue\"")
            if result.stdout.strip():
                log_warning(f"Port {port} is already in use")
            else:
                log_success(f"Port {port} is available")
        else:
            result = run_command(f"netstat -ln | grep :{port}")
            if result.returncode == 0:
                log_warning(f"Port {port} is already in use")
            else:
                log_success(f"Port {port} is available")

def generate_summary():
    """Generate deployment summary"""
    log_header("Docker Setup Summary")
    
    print(f"""
{Colors.BOLD}ClinChat-RAG Docker Configuration Summary{Colors.ENDC}

{Colors.GREEN}✅ Ready for deployment:{Colors.ENDC}
   • Docker and Docker Compose are installed
   • All configuration files are present
   • Docker Compose syntax is valid
   • Docker image can be built successfully

{Colors.CYAN}🚀 Quick Start Commands:{Colors.ENDC}
   
   {Colors.BOLD}Production Deployment:{Colors.ENDC}
   docker-compose up -d
   
   {Colors.BOLD}Development Mode:{Colors.ENDC}
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   
   {Colors.BOLD}Using Scripts:{Colors.ENDC}
   scripts/docker/deploy.bat start    # Windows
   ./scripts/docker/deploy.sh start   # Linux/Mac

{Colors.CYAN}📋 Services & Ports:{Colors.ENDC}
   • Main API: http://localhost:8002
   • API Docs: http://localhost:8002/docs
   • Chroma Vector DB: http://localhost:8001  
   • Grafana: http://localhost:3000
   • Prometheus: http://localhost:9091

{Colors.YELLOW}⚠️  Before deploying:{Colors.ENDC}
   1. Ensure your API keys are set in .env file
   2. Stop any services using the same ports
   3. Have at least 4GB RAM available

{Colors.PURPLE}🎯 Features included:{Colors.ENDC}
   • Unified database for Google Gemini & Groq APIs
   • Production-ready with monitoring
   • Development mode with hot reloading
   • Automatic health checks
   • Comprehensive logging and metrics
    """)

def main():
    """Main validation function"""
    print(f"{Colors.BOLD}{Colors.PURPLE}🐳 ClinChat-RAG Docker Validation{Colors.ENDC}")
    print(f"{Colors.PURPLE}{'=' * 40}{Colors.ENDC}\n")
    
    checks = [
        ("Docker Environment", check_docker),
        ("Required Files", check_files),
        ("Compose Configuration", validate_compose),
        ("Environment Setup", check_environment),
        ("Port Availability", check_ports),
        ("Docker Build Test", test_build)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            print()  # Add spacing between checks
        except Exception as e:
            log_error(f"{name} check failed with exception: {e}")
            print()
    
    # Summary
    log_header("Validation Results")
    
    if passed == total:
        log_success(f"All checks passed ({passed}/{total})")
        generate_summary()
        return 0
    else:
        log_warning(f"Checks passed: {passed}/{total}")
        log_info("Please address the warnings/errors above before deployment")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_info("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)