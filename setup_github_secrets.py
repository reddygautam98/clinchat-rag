#!/usr/bin/env python3
"""
GitHub Secrets Setup Helper
ClinChat-RAG AWS Deployment Configuration
"""

def display_github_secrets_info():
    """Display the required GitHub secrets for AWS deployment"""
    
    print("🔐 GITHUB SECRETS CONFIGURATION")
    print("=" * 50)
    print()
    
    secrets = {
        "AWS_ACCESS_KEY_ID": "AKIAY24YPLC7UTG7RIU2",
        "AWS_SECRET_ACCESS_KEY": "[REDACTED - See AWS_PENDING_WORK_OCTOBER_2025.md for full key]",
        "AWS_DEFAULT_REGION": "us-east-1", 
        "TF_STATE_BUCKET": "clinchat-terraform-state-bucket"
    }
    
    print("📍 REPOSITORY URL:")
    print("   https://github.com/reddygautam98/clinchat-rag")
    print()
    
    print("🔧 SECRETS CONFIGURATION URL:")
    print("   https://github.com/reddygautam98/clinchat-rag/settings/secrets/actions")
    print()
    
    print("📋 REQUIRED SECRETS TO ADD:")
    print("-" * 30)
    
    for secret_name, secret_value in secrets.items():
        print(f"Secret Name: {secret_name}")
        print(f"Secret Value: {secret_value}")
        print()
    
    print("🚀 DEPLOYMENT WORKFLOW:")
    print("-" * 25)
    print("1. ✅ Open the GitHub repository secrets page (browser opened)")
    print("2. ✅ Click 'New repository secret' button")
    print("3. ✅ Add each secret name and value from above")
    print("4. ✅ Save all 4 secrets")
    print("5. ✅ Trigger deployment workflow")
    print()
    
    print("⏭️  NEXT STEP:")
    print("   After adding secrets, run: python trigger_deployment.py")
    print()

def create_deployment_trigger():
    """Create a script to trigger the GitHub Actions deployment"""
    
    trigger_script = '''#!/usr/bin/env python3
"""
AWS Infrastructure Deployment Trigger
Starts GitHub Actions workflow for ClinChat-RAG
"""

import subprocess
import webbrowser
import time

def trigger_github_deployment():
    """Open GitHub Actions page to manually trigger deployment"""
    
    print("🚀 TRIGGERING AWS INFRASTRUCTURE DEPLOYMENT")
    print("=" * 50)
    
    # Open GitHub Actions workflow page
    actions_url = "https://github.com/reddygautam98/clinchat-rag/actions"
    
    print("📍 Opening GitHub Actions page...")
    webbrowser.open(actions_url)
    
    print()
    print("🔧 MANUAL TRIGGER STEPS:")
    print("1. Look for 'Infrastructure Deployment' workflow")
    print("2. Click 'Run workflow' button")
    print("3. Select environment: 'staging'")
    print("4. Select action: 'apply'") 
    print("5. Click 'Run workflow' to start")
    print()
    
    print("⏱️  EXPECTED DEPLOYMENT TIME: 15-20 minutes")
    print()
    print("📊 MONITOR PROGRESS:")
    print(f"   {actions_url}")
    print()
    
    # Also provide git push option
    print("🔄 ALTERNATIVE - TRIGGER VIA CODE PUSH:")
    print("   Any push to main branch will trigger deployment")
    print("   Run: git add . && git commit -m 'trigger deployment' && git push")
    print()

if __name__ == "__main__":
    trigger_github_deployment()
'''
    
    with open("trigger_deployment.py", "w") as f:
        f.write(trigger_script)
    
    print("✅ Created trigger_deployment.py")

if __name__ == "__main__":
    print("🎯 CLINCHAT-RAG AWS DEPLOYMENT SETUP")
    print("=" * 40)
    print()
    
    display_github_secrets_info()
    create_deployment_trigger()
    
    print("🎉 SETUP COMPLETE!")
    print("   Browser opened to GitHub secrets page")
    print("   Follow the steps above to add secrets")
    print("   Then run: python trigger_deployment.py")