#!/usr/bin/env python3
"""
Git Setup Script for ClinChat-RAG Medical AI System
Automated configuration for medical development environment
"""

import os
import subprocess
import sys
from pathlib import Path

def print_header(message):
    print(f"\n{'='*60}")
    print(f"🏥 {message}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def run_git_command(command, description):
    """Run a git command and return success status"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print_success(f"{description}")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print_error(f"{description} - Failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print_error(f"{description} - Exception: {str(e)}")
        return False

def check_git_installation():
    """Check if Git is installed and accessible"""
    print_header("CHECKING GIT INSTALLATION")
    
    if run_git_command("git --version", "Git version check"):
        return True
    else:
        print_error("Git is not installed or not in PATH")
        print_info("Please install Git from: https://git-scm.com/")
        return False

def initialize_repository():
    """Initialize Git repository if not already initialized"""
    print_header("INITIALIZING GIT REPOSITORY")
    
    if os.path.exists('.git'):
        print_info("Git repository already initialized")
        return True
    else:
        return run_git_command("git init", "Initialize Git repository")

def configure_git_settings():
    """Configure Git settings for medical development"""
    print_header("CONFIGURING GIT SETTINGS")
    
    configurations = [
        ("git config --local init.defaultBranch main", "Set default branch to main"),
        ("git config --local commit.template .gitmessage", "Set commit template"),
        ("git config --local core.hooksPath .githooks", "Set hooks path"),
        ("git config --local core.autocrlf false", "Disable auto CRLF conversion"),
        ("git config --local core.safecrlf true", "Enable safe CRLF checking"),
        ("git config --local pull.rebase false", "Set merge strategy for pulls"),
        ("git config --local branch.autosetupmerge always", "Auto-setup merge tracking"),
        ("git config --local branch.autosetuprebase always", "Auto-setup rebase tracking"),
    ]
    
    success_count = 0
    for command, description in configurations:
        if run_git_command(command, description):
            success_count += 1
    
    print_info(f"Configured {success_count}/{len(configurations)} Git settings")
    return success_count == len(configurations)

def setup_git_hooks():
    """Set up Git hooks for medical development"""
    print_header("SETTING UP GIT HOOKS")
    
    hooks_dir = Path(".githooks")
    
    if not hooks_dir.exists():
        print_error("Git hooks directory not found")
        return False
    
    # Make hooks executable (Unix/Linux/Mac)
    if os.name != 'nt':  # Not Windows
        try:
            for hook_file in hooks_dir.glob("*"):
                if hook_file.is_file():
                    os.chmod(hook_file, 0o755)
                    print_success(f"Made {hook_file.name} executable")
        except Exception as e:
            print_warning(f"Could not make hooks executable: {e}")
    
    # Test pre-commit hook
    pre_commit = hooks_dir / "pre-commit"
    if pre_commit.exists():
        print_success("Pre-commit hook found and configured")
        print_info("Hook will run medical compliance and security checks")
        return True
    else:
        print_error("Pre-commit hook not found")
        return False

def configure_user_info():
    """Configure Git user information"""
    print_header("CONFIGURING USER INFORMATION")
    
    # Check if user info is already configured
    try:
        result = subprocess.run(["git", "config", "--global", "user.name"], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print_success(f"Git user name already set: {result.stdout.strip()}")
            
        result = subprocess.run(["git", "config", "--global", "user.email"], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print_success(f"Git user email already set: {result.stdout.strip()}")
            return True
            
    except:
        pass
    
    print_info("Git user information not configured")
    print_info("Please configure your Git identity:")
    print_info("  git config --global user.name 'Your Name'")
    print_info("  git config --global user.email 'your.email@domain.com'")
    
    return False

def create_initial_commit():
    """Create initial commit if repository is empty"""
    print_header("CREATING INITIAL COMMIT")
    
    # Check if there are any commits
    result = subprocess.run(["git", "rev-parse", "HEAD"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print_info("Repository already has commits")
        return True
    
    # Stage essential files
    files_to_stage = [
        ".gitignore",
        ".gitattributes", 
        ".gitmessage",
        "README.md",
        "GIT_WORKFLOW.md",
        ".github/REQUIRED_SECRETS.md"
    ]
    
    staged_files = []
    for file in files_to_stage:
        if os.path.exists(file):
            if run_git_command(f"git add {file}", f"Stage {file}"):
                staged_files.append(file)
    
    if staged_files:
        commit_message = "chore: initial Git setup for ClinChat-RAG medical AI system\\n\\n- Configure Git workflow for medical development\\n- Add comprehensive .gitignore for sensitive data protection\\n- Set up pre-commit hooks for security and compliance\\n- Add medical-specific commit templates and PR workflows\\n- Ensure HIPAA compliance in version control"
        
        if run_git_command(f'git commit -m "{commit_message}"', "Create initial commit"):
            print_success("Initial commit created successfully")
            return True
    
    print_warning("No files to commit for initial setup")
    return False

def setup_default_branch():
    """Ensure we're on the main branch"""
    print_header("SETTING UP DEFAULT BRANCH")
    
    # Check current branch
    result = subprocess.run(["git", "branch", "--show-current"], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        current_branch = result.stdout.strip()
        if current_branch == "main":
            print_success("Already on main branch")
            return True
        elif current_branch:
            # Rename current branch to main
            if run_git_command("git branch -M main", "Rename current branch to main"):
                print_success("Renamed current branch to main")
                return True
    
    # Create and checkout main branch
    if run_git_command("git checkout -b main", "Create and checkout main branch"):
        return True
    
    return False

def display_next_steps():
    """Display next steps for the user"""
    print_header("SETUP COMPLETE - NEXT STEPS")
    
    print_info("🎉 Git setup completed successfully!")
    print_info("")
    print_info("📋 Next Steps:")
    print_info("1. Configure your Git identity (if not already done):")
    print_info("   git config --global user.name 'Your Name'")
    print_info("   git config --global user.email 'your.email@medical-org.com'")
    print_info("")
    print_info("2. Review the Git workflow documentation:")
    print_info("   📖 GIT_WORKFLOW.md - Complete development workflow guide")
    print_info("   📋 .gitmessage - Commit message template for medical commits")
    print_info("")
    print_info("3. Set up GitHub/GitLab repository:")
    print_info("   🔐 Configure required secrets (see .github/REQUIRED_SECRETS.md)")
    print_info("   🛡️  Set up branch protection rules for main/develop branches")
    print_info("   👥 Add medical professionals as reviewers")
    print_info("")
    print_info("4. Install development dependencies:")
    print_info("   🐍 pip install -r requirements.txt")
    print_info("   🧪 Set up testing environment")
    print_info("   🔍 Configure linting tools (flake8, black, eslint)")
    print_info("")
    print_info("5. Test the pre-commit hook:")
    print_info("   📝 Make a small change and try: git add . && git commit")
    print_info("   🔍 Verify security and compliance checks run")
    print_info("")
    print_info("🏥 Medical Development Reminders:")
    print_info("✅ Never commit PHI (Protected Health Information)")
    print_info("✅ Always use environment variables for secrets")
    print_info("✅ Get medical review for clinical features")
    print_info("✅ Ensure HIPAA compliance in all changes")
    print_info("✅ Follow clinical testing procedures")
    print_info("")
    print_info("📞 Need Help?")
    print_info("   📖 Read: GIT_WORKFLOW.md")
    print_info("   🚨 Medical Issues: Contact Medical Director")
    print_info("   🔒 Security Issues: Contact Security Team")

def main():
    """Main setup function"""
    print_header("CLINCHAT-RAG GIT SETUP WIZARD")
    print_info("Setting up Git for medical AI development...")
    print_info("This will configure Git for HIPAA-compliant medical software development")
    
    # Run setup steps
    setup_steps = [
        ("Check Git Installation", check_git_installation),
        ("Initialize Repository", initialize_repository),
        ("Configure Git Settings", configure_git_settings),
        ("Set Up Git Hooks", setup_git_hooks),
        ("Configure User Info", configure_user_info),
        ("Set Up Default Branch", setup_default_branch),
        ("Create Initial Commit", create_initial_commit),
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print_error(f"{step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    # Summary
    print_header("SETUP SUMMARY")
    
    if not failed_steps:
        print_success("🎉 All setup steps completed successfully!")
        display_next_steps()
        return 0
    else:
        print_warning(f"⚠️  {len(failed_steps)} step(s) had issues:")
        for step in failed_steps:
            print_warning(f"   - {step}")
        print_info("Review the errors above and complete manual configuration if needed")
        display_next_steps()
        return 1

if __name__ == "__main__":
    sys.exit(main())