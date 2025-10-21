#!/usr/bin/env python3
"""
Push a clean repository without secrets to GitHub
"""
import os
import subprocess
import shutil

def create_clean_repo():
    """Create a clean repository without any secrets"""
    
    print("🧹 Creating Clean Repository...")
    
    # Create a temporary directory for clean repo
    clean_dir = "clinchat-rag-clean"
    if os.path.exists(clean_dir):
        shutil.rmtree(clean_dir)
    
    os.makedirs(clean_dir)
    
    # Essential files to include (without secrets)
    essential_files = [
        'infrastructure/main.tf',
        'infrastructure/variables.tf', 
        'infrastructure/outputs.tf',
        '.github/workflows/infrastructure.yml',
        '.github/workflows/ci-cd.yml',
        'api/',
        'frontend/',
        'Dockerfile',
        'docker-compose.yml',
        'requirements.txt',
        'README.md',
        'MANUAL_GITHUB_SETUP_STEPS.md',
        'FINAL_AWS_SETUP_COMPLETE.md'
    ]
    
    print("📁 Copying essential files...")
    for file_path in essential_files:
        src = file_path
        dst = os.path.join(clean_dir, file_path)
        
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            print(f"✅ Copied: {file_path}")
        else:
            print(f"⚠️  Not found: {file_path}")
    
    # Initialize git in clean directory
    os.chdir(clean_dir)
    subprocess.run(['git', 'init'], check=True)
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit: Clean ClinChat-RAG infrastructure'], check=True)
    
    # Add remote
    subprocess.run(['git', 'remote', 'add', 'origin', 
                   'https://github.com/reddygautam98/clinchat-rag.git'], check=True)
    
    # Force push to overwrite
    result = subprocess.run(['git', 'push', '-f', 'origin', 'main'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Successfully pushed clean repository!")
        return True
    else:
        print(f"❌ Push failed: {result.stderr}")
        return False

if __name__ == "__main__":
    success = create_clean_repo()
    if success:
        print("🎉 Clean repository created successfully!")
        print("📋 Next: Add GitHub secrets and trigger deployment")
    else:
        print("❌ Failed to create clean repository")