#!/usr/bin/env python3
"""
Environment Setup Script for ClinChat-RAG
Automated infrastructure provisioning and configuration
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import platform
import venv
import json
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentSetup:
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.venv_path = self.project_root / ".venv"
        self.system = platform.system().lower()
        self.python_executable = sys.executable
        
    def check_python_version(self) -> bool:
        """Check if Python version is compatible (>=3.8)"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
            return True
        else:
            logger.error(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create virtual environment if it doesn't exist"""
        try:
            if self.venv_path.exists():
                logger.info("✅ Virtual environment already exists")
                return True
            
            logger.info("🔧 Creating virtual environment...")
            venv.create(self.venv_path, with_pip=True)
            logger.info("✅ Virtual environment created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def get_venv_python(self) -> Path:
        """Get path to Python executable in virtual environment"""
        if self.system == "windows":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def get_venv_pip(self) -> Path:
        """Get path to pip executable in virtual environment"""
        if self.system == "windows":
            return self.venv_path / "Scripts" / "pip.exe"
        else:
            return self.venv_path / "bin" / "pip"
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip in virtual environment"""
        try:
            logger.info("🔧 Upgrading pip...")
            result = subprocess.run([
                str(self.get_venv_python()), "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True, check=True)
            logger.info("✅ Pip upgraded successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to upgrade pip: {e}")
            return False
    
    def install_core_dependencies(self) -> bool:
        """Install core project dependencies"""
        core_packages = [
            "langchain",
            "openai", 
            "anthropic",
            "faiss-cpu",
            "pymupdf",
            "spacy",
            "pandas",
            "fastapi",
            "uvicorn",
            "pydantic",
            "chromadb",
            "scikit-learn",
            "psycopg2-binary",
            "redis",
            "sentence-transformers",
            "transformers",
            "python-dotenv",
            "streamlit",
            "plotly",
            "matplotlib",
            "seaborn"
        ]
        
        try:
            logger.info("🔧 Installing core dependencies...")
            for package in core_packages:
                logger.info(f"  Installing {package}...")
                subprocess.run([
                    str(self.get_venv_pip()), "install", package
                ], capture_output=True, text=True, check=True)
            
            logger.info("✅ Core dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def install_spacy_model(self) -> bool:
        """Install spaCy English model"""
        try:
            logger.info("🔧 Installing spaCy English model...")
            subprocess.run([
                str(self.get_venv_python()), "-m", "spacy", "download", "en_core_web_sm"
            ], capture_output=True, text=True, check=True)
            logger.info("✅ spaCy model installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️  Failed to install spaCy model: {e}")
            logger.info("   You can install it later with: python -m spacy download en_core_web_sm")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary project directories"""
        directories = [
            "data/store/raw",
            "data/store/processed", 
            "data/store/embeddings",
            "data/store/models",
            "logs",
            "temp",
            "notebooks",
            "config"
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create .env file from .env.example if it doesn't exist"""
        try:
            env_file = self.project_root / ".env"
            env_example = self.project_root / ".env.example"
            
            if env_file.exists():
                logger.info("✅ .env file already exists")
                return True
            
            if env_example.exists():
                shutil.copy2(env_example, env_file)
                logger.info("✅ Created .env file from .env.example")
                logger.warning("⚠️  Please configure your API keys in the .env file")
                return True
            else:
                logger.warning("⚠️  .env.example not found - skipping .env creation")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that key packages are importable"""
        packages_to_test = [
            "langchain",
            "openai",
            "anthropic", 
            "faiss",
            "pandas",
            "fastapi",
            "chromadb",
            "sklearn",
            "transformers"
        ]
        
        logger.info("🔧 Verifying installation...")
        
        for package in packages_to_test:
            try:
                result = subprocess.run([
                    str(self.get_venv_python()), "-c", f"import {package}"
                ], capture_output=True, text=True, check=True)
                logger.info(f"  ✅ {package}")
            except subprocess.CalledProcessError:
                logger.error(f"  ❌ {package} - Import failed")
                return False
        
        logger.info("✅ All packages verified successfully")
        return True
    
    def generate_requirements_file(self) -> bool:
        """Generate requirements.txt file"""
        try:
            logger.info("🔧 Generating requirements.txt...")
            result = subprocess.run([
                str(self.get_venv_pip()), "freeze"
            ], capture_output=True, text=True, check=True)
            
            requirements_file = self.project_root / "requirements.txt"
            with open(requirements_file, "w") as f:
                f.write(result.stdout)
            
            logger.info("✅ requirements.txt generated successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to generate requirements.txt: {e}")
            return False
    
    def display_summary(self):
        """Display setup summary and next steps"""
        logger.info("\n" + "="*60)
        logger.info("🎉 ENVIRONMENT SETUP COMPLETE!")
        logger.info("="*60)
        
        # Activation command
        if self.system == "windows":
            activate_cmd = r".\.venv\Scripts\Activate.ps1"
        else:
            activate_cmd = "source .venv/bin/activate"
        
        logger.info("\n📋 NEXT STEPS:")
        logger.info(f"1. Activate virtual environment:")
        logger.info(f"   {activate_cmd}")
        logger.info("\n2. Configure your API keys in .env file")
        logger.info("\n3. Run the application:")
        logger.info("   python -m api.main")
        logger.info("\n4. Access the API documentation:")
        logger.info("   http://localhost:8000/docs")
        
        logger.info("\n🔧 USEFUL COMMANDS:")
        logger.info("   - Run tests: pytest tests/")
        logger.info("   - Generate data: python scripts/generate_clinical_data.py")
        logger.info("   - Start notebook: jupyter lab notebooks/")
        
        logger.info("\n📁 PROJECT STRUCTURE:")
        logger.info("   - Source code: api/, embeddings/, nlp/, vectorstore/")
        logger.info("   - Data: data/raw/, data/store/")
        logger.info("   - Documentation: docs/")
        logger.info("   - Configuration: .env, config/")
    
    def run_setup(self) -> bool:
        """Run complete environment setup"""
        logger.info("🚀 Starting ClinChat-RAG Environment Setup")
        logger.info(f"📁 Project root: {self.project_root}")
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Upgrading pip", self.upgrade_pip),
            ("Installing core dependencies", self.install_core_dependencies),
            ("Installing spaCy model", self.install_spacy_model),
            ("Creating project directories", self.create_directories),
            ("Creating .env file", self.create_env_file),
            ("Verifying installation", self.verify_installation),
            ("Generating requirements.txt", self.generate_requirements_file)
        ]
        
        for step_name, step_function in steps:
            logger.info(f"\n🔧 {step_name}...")
            try:
                success = step_function()
                if not success and step_name in ["Checking Python version", "Creating virtual environment"]:
                    logger.error("❌ Critical step failed - setup aborted")
                    return False
            except Exception as e:
                logger.error(f"❌ Unexpected error in {step_name}: {e}")
                if step_name in ["Checking Python version", "Creating virtual environment"]:
                    return False
        
        self.display_summary()
        return True

def main():
    """Main entry point"""
    setup = EnvironmentSetup()
    success = setup.run_setup()
    
    if success:
        logger.info("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()