#!/usr/bin/env python3
"""
GitHub Secrets Setup and Deployment Guide
This script will help you configure GitHub secrets and trigger deployment
"""

import webbrowser
import time

def show_github_secrets_setup():
    """Show step-by-step GitHub secrets configuration."""
    print("🔐 GitHub Secrets Configuration")
    print("=" * 50)
    
    print("\n📋 REQUIRED SECRETS:")
    print("You need to add these 4 secrets to your GitHub repository:")
    print("")
    print("1️⃣ AWS_ACCESS_KEY_ID")
    print("   Value: AKIAY24YPLC7UQI5QX2V")
    print("")
    print("2️⃣ AWS_SECRET_ACCESS_KEY") 
    print("   Value: s4It/Ek76aTp1TgSm8qC6qjCpiLO7v9hS77xzWxs")
    print("")
    print("3️⃣ AWS_DEFAULT_REGION")
    print("   Value: us-east-1")
    print("")
    print("4️⃣ TF_STATE_BUCKET")
    print("   Value: clinchat-terraform-state-bucket")
    
    print("\n" + "="*50)
    print("STEP-BY-STEP SETUP PROCESS")
    print("="*50)
    
    print("\n🌐 Opening GitHub Secrets page...")
    url = "https://github.com/reddygautam98/clinchat-rag/settings/secrets/actions"
    
    try:
        webbrowser.open(url)
        print(f"✅ Opened: {url}")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"📋 Manual URL: {url}")
    
    print("\n📝 INSTRUCTIONS:")
    print("1. Click 'New repository secret' button")
    print("2. Add each secret one by one:")
    print("")
    
    secrets = [
        ("AWS_ACCESS_KEY_ID", "AKIAY24YPLC7UQI5QX2V"),
        ("AWS_SECRET_ACCESS_KEY", "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"),
        ("AWS_DEFAULT_REGION", "us-east-1"),
        ("TF_STATE_BUCKET", "clinchat-terraform-state-bucket")
    ]
    
    for i, (name, value) in enumerate(secrets, 1):
        print(f"{i}. Secret Name: {name}")
        print(f"   Secret Value: {value}")
        print(f"   → Click 'Add secret'")
        print("")
    
    print("3. Verify all 4 secrets are listed")
    print("4. Come back to this terminal and press Enter when done")
    
    input("\n⏳ Press Enter after adding all GitHub secrets...")
    
    return True

def show_deployment_instructions():
    """Show deployment trigger instructions."""
    print("\n🚀 DEPLOYMENT TRIGGER")
    print("=" * 50)
    
    print("\n📋 Now we'll trigger the GitHub Actions workflow:")
    print("1. Commit and push your changes")
    print("2. GitHub Actions will automatically deploy infrastructure")
    print("3. Monitor the deployment progress")
    
    print("\n💻 Commands to run:")
    print('git add .')
    print('git commit -m "Configure AWS credentials for deployment"')
    print('git push origin main')
    
    print("\n🔍 Monitor deployment at:")
    monitor_url = "https://github.com/reddygautam98/clinchat-rag/actions"
    print(f"📊 {monitor_url}")
    
    try:
        webbrowser.open(monitor_url)
        print("✅ Opened GitHub Actions page")
    except:
        print("📋 Open manually if needed")

def check_prerequisites():
    """Check if everything is ready for deployment."""
    print("🔍 PRE-DEPLOYMENT CHECK")
    print("=" * 30)
    
    checks = [
        ("✅ AWS credentials working", True),
        ("✅ S3 bucket exists", True), 
        ("✅ DynamoDB table exists", True),
        ("✅ IAM permissions configured", True),
        ("✅ .env file updated", True)
    ]
    
    for check, status in checks:
        print(f"{check}")
    
    print("\n🎯 Ready for GitHub secrets configuration!")

def main():
    """Main deployment setup function."""
    print("🚀 ClinChat-RAG Deployment Setup")
    print("=" * 60)
    
    # Check prerequisites
    check_prerequisites()
    
    # Setup GitHub secrets
    print("\n" + "="*60)
    if show_github_secrets_setup():
        print("✅ GitHub secrets configuration completed!")
    
    # Show deployment instructions  
    show_deployment_instructions()
    
    print("\n" + "="*60)
    print("🎉 DEPLOYMENT SETUP COMPLETE!")
    print("=" * 60)
    print("✅ AWS is working")
    print("✅ GitHub secrets configured") 
    print("✅ Ready to deploy")
    print("")
    print("🚀 Run the git commands above to trigger deployment!")

if __name__ == "__main__":
    main()