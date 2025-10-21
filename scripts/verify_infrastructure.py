#!/usr/bin/env python3
"""
Infrastructure Verification Script for ClinChat-RAG
Verifies all components are properly installed and configured
"""

import sys
import subprocess
import importlib
import platform
from pathlib import Path
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class InfrastructureVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.failures = []
        
    def check_python_version(self):
        """Verify Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.failures.append(f"Python version {version.major}.{version.minor} < 3.8")
            return False
    
    def check_virtual_environment(self):
        """Verify we're running in virtual environment"""
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.info("✅ Running in virtual environment")
            return True
        else:
            self.failures.append("Not running in virtual environment")
            return False
    
    def check_core_packages(self):
        """Verify core AI/ML packages are importable"""
        packages = {
            'langchain': 'LangChain framework',
            'openai': 'OpenAI API client',
            'anthropic': 'Anthropic API client', 
            'faiss': 'Vector search (FAISS)',
            'pandas': 'Data manipulation',
            'numpy': 'Numerical computing',
            'fastapi': 'API framework',
            'pydantic': 'Data validation',
            'chromadb': 'Vector database',
            'sklearn': 'Scikit-learn ML',
            'transformers': 'Hugging Face Transformers',
            'sentence_transformers': 'Sentence embeddings',
            'psycopg2': 'PostgreSQL adapter',
            'redis': 'Redis client',
            'spacy': 'spaCy NLP'
        }
        
        logger.info("Checking core packages...")
        success = True
        
        for package, description in packages.items():
            try:
                importlib.import_module(package)
                logger.info(f"  ✅ {package:<20} - {description}")
            except ImportError as e:
                logger.error(f"  ❌ {package:<20} - {description} - {e}")
                self.failures.append(f"Missing package: {package}")
                success = False
                
        return success
    
    def check_project_structure(self):
        """Verify project directories exist"""
        required_dirs = [
            'api',
            'embeddings', 
            'nlp',
            'vectorstore',
            'data/raw',
            'data/store/raw',
            'data/store/processed',
            'docs',
            'scripts',
            'tests'
        ]
        
        logger.info("Checking project structure...")
        success = True
        
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists():
                logger.info(f"  ✅ {directory}")
            else:
                logger.error(f"  ❌ {directory} - Missing directory")
                self.failures.append(f"Missing directory: {directory}")
                success = False
                
        return success
    
    def check_configuration_files(self):
        """Verify configuration files exist"""
        config_files = [
            '.env.example',
            'requirements.txt',
            'README.md',
            'docs/compliance.md',
            'docs/fusion_ai_architecture.md'
        ]
        
        logger.info("Checking configuration files...")
        success = True
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                logger.info(f"  ✅ {config_file}")
            else:
                logger.error(f"  ❌ {config_file} - Missing file")
                self.failures.append(f"Missing file: {config_file}")
                success = False
                
        return success
    
    def check_data_files(self):
        """Verify clinical data files exist"""
        data_files = [
            'data/raw/lab_data_chemistry_panel_5k.csv',
            'data/raw/ae_data_safety_database_5k.csv',
            'scripts/generate_clinical_data.py',
            'scripts/analyze_datasets.py'
        ]
        
        logger.info("Checking data files...")
        success = True
        
        for data_file in data_files:
            file_path = self.project_root / data_file
            if file_path.exists():
                file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"  ✅ {data_file} ({file_size:.2f} MB)")
            else:
                logger.error(f"  ❌ {data_file} - Missing file")
                self.failures.append(f"Missing data file: {data_file}")
                success = False
                
        return success
    
    def check_api_key_configuration(self):
        """Check if API keys are configured"""
        env_file = self.project_root / '.env'
        
        if not env_file.exists():
            logger.warning("⚠️  .env file not found - API keys not configured")
            return False
        
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        # Check for key environment variables (without revealing values)
        key_vars = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
        configured = 0
        
        for var in key_vars:
            value = os.getenv(var)
            if value and value.strip():
                logger.info(f"  ✅ {var} configured")
                configured += 1
            else:
                logger.warning(f"  ⚠️  {var} not configured")
        
        if configured > 0:
            logger.info(f"✅ {configured}/{len(key_vars)} API keys configured")
            return True
        else:
            logger.warning("⚠️  No API keys configured")
            return False
    
    def check_gpu_availability(self):
        """Check if GPU is available for AI workloads"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"✅ GPU available: {gpu_count}x {gpu_name}")
                return True
            else:
                logger.info("ℹ️  No GPU available - will use CPU")
                return False
        except ImportError:
            logger.info("ℹ️  PyTorch not installed - GPU check skipped")
            return False
    
    def check_spacy_models(self):
        """Check if spaCy models are installed"""
        try:
            import spacy
            
            models_to_check = ['en_core_web_sm', 'en_core_web_md']
            installed_models = []
            
            for model in models_to_check:
                try:
                    spacy.load(model)
                    installed_models.append(model)
                    logger.info(f"  ✅ spaCy model: {model}")
                except OSError:
                    logger.warning(f"  ⚠️  spaCy model not installed: {model}")
            
            if installed_models:
                logger.info(f"✅ {len(installed_models)} spaCy models available")
                return True
            else:
                logger.warning("⚠️  No spaCy models installed")
                return False
                
        except ImportError:
            logger.error("❌ spaCy not installed")
            return False
    
    def run_verification(self):
        """Run complete infrastructure verification"""
        logger.info("🔍 Starting ClinChat-RAG Infrastructure Verification")
        logger.info(f"📁 Project root: {self.project_root}")
        logger.info(f"🖥️  System: {platform.system()} {platform.release()}")
        logger.info("="*60)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Virtual Environment", self.check_virtual_environment),
            ("Core Packages", self.check_core_packages),
            ("Project Structure", self.check_project_structure),
            ("Configuration Files", self.check_configuration_files),
            ("Data Files", self.check_data_files),
            ("API Configuration", self.check_api_key_configuration),
            ("GPU Availability", self.check_gpu_availability),
            ("spaCy Models", self.check_spacy_models)
        ]
        
        passed = 0
        total = len(checks)
        
        for check_name, check_function in checks:
            logger.info(f"\n🔧 {check_name}:")
            try:
                result = check_function()
                if result:
                    passed += 1
            except Exception as e:
                logger.error(f"❌ {check_name} check failed: {e}")
                self.failures.append(f"{check_name}: {str(e)}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 VERIFICATION SUMMARY")
        logger.info("="*60)
        
        if passed == total:
            logger.info("🎉 ALL CHECKS PASSED!")
            logger.info("✅ Infrastructure is ready for ClinChat-RAG")
        else:
            logger.warning(f"⚠️  {passed}/{total} checks passed")
            
            if self.failures:
                logger.error("\n❌ FAILURES:")
                for failure in self.failures:
                    logger.error(f"   - {failure}")
        
        logger.info("\n🚀 READY TO START:")
        logger.info("   1. Configure API keys in .env file")
        logger.info("   2. Run: python -m api.main")
        logger.info("   3. Access: http://localhost:8000/docs")
        
        return passed == total

def main():
    """Main entry point"""
    verifier = InfrastructureVerifier()
    success = verifier.run_verification()
    
    if success:
        logger.info("\n✅ Verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n⚠️  Verification completed with issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()