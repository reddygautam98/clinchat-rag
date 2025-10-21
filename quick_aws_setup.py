#!/usr/bin/env python3
"""
Quick AWS Environment Variables Setup
This script helps you set AWS credentials as environment variables temporarily.
"""

import os

def set_aws_env_vars():
    """Set AWS credentials as environment variables."""
    print("🌍 AWS Environment Variables Setup")
    print("=" * 40)
    
    print("\nEnter your AWS credentials:")
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    region = input("AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    if not access_key or not secret_key:
        print("❌ Error: Both Access Key ID and Secret Key are required!")
        return False
    
    # Set environment variables
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    os.environ['AWS_DEFAULT_REGION'] = region
    
    print("\n✅ Environment variables set for current session!")
    print(f"AWS_ACCESS_KEY_ID = {access_key[:8]}...")
    print(f"AWS_SECRET_ACCESS_KEY = {'*' * 20}")
    print(f"AWS_DEFAULT_REGION = {region}")
    
    # Test connection
    try:
        import boto3
        print("\n🧪 Testing connection...")
        
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS connection successful!")
        print(f"Account ID: {identity.get('Account', 'N/A')}")
        print(f"User ARN: {identity.get('Arn', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify credentials are correct and active")
        print("2. Check if IAM user has required permissions")
        print("3. Go to AWS Console > IAM > Users to verify")
        return False

def show_powershell_commands(access_key, secret_key, region="us-east-1"):
    """Show PowerShell commands to set environment variables."""
    print("\n📋 PowerShell Commands (run these in your terminal):")
    print(f"$env:AWS_ACCESS_KEY_ID='{access_key}'")
    print(f"$env:AWS_SECRET_ACCESS_KEY='{secret_key}'")
    print(f"$env:AWS_DEFAULT_REGION='{region}'")

if __name__ == "__main__":
    if set_aws_env_vars():
        print("\n🎉 Setup complete! You can now run AWS status checks.")
    else:
        print("\n❌ Setup failed. Please verify your credentials.")