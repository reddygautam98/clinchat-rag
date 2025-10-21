#!/usr/bin/env python3
"""
Clean GitHub Deployment Script
Uses environment variables instead of hardcoded credentials
"""

import os
import webbrowser

def get_aws_credentials_from_env():
    """Get AWS credentials from environment or .env file."""
    # Try to load from .env file
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key.startswith('AWS_'):
                        os.environ[key] = value
    
    return {
        'access_key': os.environ.get('AWS_ACCESS_KEY_ID', '[Not found]'),
        'secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY', '[Not found]'),
        'region': os.environ.get('AWS_REGION', 'us-east-1')
    }

def show_github_secrets_setup():
    """Show GitHub secrets setup instructions."""
    print("🔐 GitHub Secrets Configuration")
    print("=" * 50)
    
    creds = get_aws_credentials_from_env()
    
    print("\n📋 REQUIRED SECRETS:")
    print("Add these 4 secrets to your GitHub repository:")
    print("")
    print("1️⃣ AWS_ACCESS_KEY_ID")
    print(f"   Value: {creds['access_key'][:8]}..." if len(creds['access_key']) > 8 else f"   Value: {creds['access_key']}")
    print("")
    print("2️⃣ AWS_SECRET_ACCESS_KEY")
    print("   Value: [Your Secret Key - found in .env file]")
    print("")
    print("3️⃣ AWS_DEFAULT_REGION")
    print(f"   Value: {creds['region']}")
    print("")
    print("4️⃣ TF_STATE_BUCKET")
    print("   Value: clinchat-terraform-state-bucket")
    
    print("\n🌐 Opening GitHub Secrets page...")
    url = "https://github.com/reddygautam98/clinchat-rag/settings/secrets/actions"
    
    try:
        webbrowser.open(url)
        print(f"✅ Opened: {url}")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"📋 Manual URL: {url}")
    
    print("\n📝 MANUAL STEPS:")
    print("1. Click 'New repository secret'")
    print("2. Add each secret with the values shown above")
    print("3. Use your actual AWS credentials from the .env file")
    print("4. Come back when all 4 secrets are added")
    
    input("\n⏳ Press Enter after configuring GitHub secrets...")

def trigger_deployment():
    """Instructions for triggering deployment."""
    print("\n🚀 TRIGGER DEPLOYMENT")
    print("=" * 40)
    
    print("✅ Credentials secured")
    print("✅ GitHub secrets configured") 
    print("✅ Ready to deploy!")
    
    print("\n🔍 Monitor deployment:")
    actions_url = "https://github.com/reddygautam98/clinchat-rag/actions"
    print(f"📊 {actions_url}")
    
    try:
        webbrowser.open(actions_url)
        print("✅ Opened GitHub Actions page")
    except:
        print("📋 Open manually if needed")

def main():
    """Main deployment function."""
    print("🚀 ClinChat-RAG Secure Deployment")
    print("=" * 50)
    
    # Check environment
    creds = get_aws_credentials_from_env()
    
    if '[Not found]' in creds['access_key']:
        print("❌ AWS credentials not found in environment!")
        print("📋 Make sure your .env file has the correct AWS credentials")
        return False
    
    print("✅ AWS credentials loaded from environment")
    print(f"✅ Access Key: {creds['access_key'][:8]}...")
    print(f"✅ Region: {creds['region']}")
    
    # Setup GitHub secrets
    show_github_secrets_setup()
    
    # Show deployment trigger
    trigger_deployment()
    
    print("\n🎉 DEPLOYMENT READY!")
    print("The GitHub Actions workflow will now deploy your infrastructure")

if __name__ == "__main__":
    main()