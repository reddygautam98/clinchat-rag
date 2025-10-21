#!/usr/bin/env python3
"""
GitHub Repository Setup Script for ClinChat-RAG
Automates the repository creation and initial setup process
"""

import subprocess
import os
import json
import urllib.request
import urllib.parse
import getpass
from pathlib import Path

class GitHubSetup:
    def __init__(self):
        self.repo_name = "clinchat-rag"
        self.repo_description = "ClinChat-RAG: AI-Powered Clinical Intelligence & RAG System with AWS Deployment"
        
    def check_git_status(self):
        """Check current git repository status"""
        print("🔍 Checking current git status...")
        
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                print("✅ Git repository exists")
                
                # Check remote status
                remote_result = subprocess.run(['git', 'remote', '-v'], 
                                             capture_output=True, text=True, cwd='.')
                if remote_result.stdout.strip():
                    print(f"📡 Existing remotes:\n{remote_result.stdout}")
                    return True, True  # Has git, has remote
                else:
                    print("⚠️  No remote repository configured")
                    return True, False  # Has git, no remote
            else:
                print("❌ Not a git repository")
                return False, False
                
        except FileNotFoundError:
            print("❌ Git not installed or not in PATH")
            return False, False
    
    def setup_git_repository(self):
        """Initialize git repository if needed"""
        has_git, has_remote = self.check_git_status()
        
        if not has_git:
            print("🎯 Initializing git repository...")
            subprocess.run(['git', 'init'], cwd='.')
            subprocess.run(['git', 'branch', '-M', 'main'], cwd='.')
            print("✅ Git repository initialized")
            
        return has_remote
    
    def create_github_repo_instructions(self):
        """Generate instructions for creating GitHub repository manually"""
        
        instructions = f"""
# 📋 MANUAL GITHUB REPOSITORY SETUP INSTRUCTIONS

## Step 1: Create GitHub Repository
1. Go to: https://github.com/new
2. Repository name: `{self.repo_name}`
3. Description: `{self.repo_description}`
4. Set to: ✅ Public (or Private if preferred)
5. DO NOT initialize with README, .gitignore, or license (we have these)
6. Click "Create repository"

## Step 2: Copy Repository URL
After creation, GitHub will show you the repository URL:
- HTTPS: `https://github.com/YOUR_USERNAME/{self.repo_name}.git`
- SSH: `git@github.com:YOUR_USERNAME/{self.repo_name}.git`

Copy the HTTPS URL for the next step.

## Step 3: Run the Setup Commands
After creating the repository, run these commands:

```bash
# Navigate to project directory
cd "{os.getcwd()}"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/{self.repo_name}.git

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: ClinChat-RAG with AWS infrastructure"

# Push to GitHub
git push -u origin main
```

## Step 4: Configure GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions
Add these secrets:

```
AWS_ACCESS_KEY_ID = AKIAY24YPLC7UTG7RIU2
AWS_SECRET_ACCESS_KEY = h2kodtZHjv/p7eRksh52UHoOKkildRltK/xAA9t0
TF_STATE_BUCKET = clinchat-terraform-state-bucket
AWS_DEFAULT_REGION = us-east-1
```
        """
        
        return instructions
    
    def prepare_commit_all_files(self):
        """Prepare to commit all files"""
        print("📦 Preparing to commit all files...")
        
        # Check git status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.stdout.strip():
            print("📋 Files to be committed:")
            print(result.stdout)
            
            # Add all files
            print("➕ Adding all files to git...")
            subprocess.run(['git', 'add', '.'], cwd='.')
            print("✅ All files added to staging area")
            
            return True
        else:
            print("✅ All files already committed")
            return False
    
    def commit_changes(self):
        """Create initial commit"""
        print("📝 Creating initial commit...")
        
        try:
            result = subprocess.run([
                'git', 'commit', '-m', 
                'Initial commit: ClinChat-RAG with AWS infrastructure\n\n- Complete ClinChat-RAG medical AI system\n- AWS infrastructure with Terraform\n- GitHub Actions CI/CD pipeline\n- Docker deployment configuration\n- HIPAA-compliant architecture'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                print("✅ Initial commit created successfully")
                return True
            else:
                print(f"⚠️  Commit result: {result.stderr}")
                return True  # Often just warnings
                
        except Exception as e:
            print(f"❌ Error creating commit: {e}")
            return False
    
    def generate_setup_script(self):
        """Generate a complete setup script"""
        
        script_content = f'''@echo off
REM GitHub Repository Setup Script for ClinChat-RAG
echo 🚀 Setting up ClinChat-RAG GitHub Repository...

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo ❌ Error: Please run this script from the clinchat-rag directory
    pause
    exit /b 1
)

echo 📦 Adding all files to git...
git add .

echo 📝 Creating initial commit...
git commit -m "Initial commit: ClinChat-RAG with AWS infrastructure"

echo 📋 Manual steps required:
echo 1. Create GitHub repository at: https://github.com/new
echo 2. Repository name: {self.repo_name}
echo 3. After creation, run:
echo    git remote add origin https://github.com/YOUR_USERNAME/{self.repo_name}.git
echo    git push -u origin main

pause
'''
        
        with open('setup_github.bat', 'w') as f:
            f.write(script_content)
            
        print("✅ Setup script created: setup_github.bat")

def main():
    print("🎯 ClinChat-RAG GitHub Repository Setup")
    print("=" * 50)
    
    setup = GitHubSetup()
    
    # Check current status
    has_remote = setup.setup_git_repository()
    
    if has_remote:
        print("✅ Repository already has remote configured")
        print("🎯 Ready to push changes if needed")
    else:
        print("🎯 Setting up repository for GitHub...")
        
        # Prepare files for commit
        has_changes = setup.prepare_commit_all_files()
        
        if has_changes:
            # Create commit
            setup.commit_changes()
        
        # Generate instructions
        instructions = setup.create_github_repo_instructions()
        
        # Save instructions to file
        with open('GITHUB_SETUP_INSTRUCTIONS.md', 'w') as f:
            f.write(instructions)
            
        print("✅ Instructions saved to: GITHUB_SETUP_INSTRUCTIONS.md")
        
        # Generate batch script
        setup.generate_setup_script()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Read: GITHUB_SETUP_INSTRUCTIONS.md")
        print("2. Create GitHub repository manually")
        print("3. Run: setup_github.bat")
        print("4. Configure GitHub secrets")

if __name__ == "__main__":
    main()