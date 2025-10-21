#!/usr/bin/env python3
"""
AWS Credentials Configuration Script
This script helps configure AWS credentials for the ClinChat-RAG project.
"""

import os
import sys
import json
from pathlib import Path

def create_aws_directories():
    """Create AWS configuration directories if they don't exist."""
    aws_dir = Path.home() / '.aws'
    aws_dir.mkdir(exist_ok=True)
    return aws_dir

def configure_aws_credentials():
    """Configure AWS credentials interactively."""
    print("🔧 AWS Credentials Configuration")
    print("=" * 50)
    
    # Get AWS credentials from user
    print("\nPlease enter your AWS credentials:")
    print("(You can get these from the AWS Console > IAM > Users > Security credentials)")
    
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    region = input("Default region (e.g., us-east-1): ").strip() or "us-east-1"
    
    if not access_key or not secret_key:
        print("❌ Error: Access Key ID and Secret Access Key are required!")
        return False
    
    # Create AWS directory
    aws_dir = create_aws_directories()
    
    # Write credentials file
    credentials_file = aws_dir / 'credentials'
    credentials_content = f"""[default]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}
"""
    
    with open(credentials_file, 'w') as f:
        f.write(credentials_content)
    
    # Write config file
    config_file = aws_dir / 'config'
    config_content = f"""[default]
region = {region}
output = json
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"\n✅ AWS credentials configured successfully!")
    print(f"📁 Credentials file: {credentials_file}")
    print(f"📁 Config file: {config_file}")
    
    return True

def set_environment_variables(access_key, secret_key, region):
    """Set AWS environment variables."""
    os.environ['AWS_ACCESS_KEY_ID'] = access_key
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    os.environ['AWS_DEFAULT_REGION'] = region
    
    print("🌍 Environment variables set for current session:")
    print(f"   AWS_ACCESS_KEY_ID = {access_key[:8]}...")
    print(f"   AWS_SECRET_ACCESS_KEY = {'*' * 20}")
    print(f"   AWS_DEFAULT_REGION = {region}")

def test_aws_connection():
    """Test AWS connection using boto3."""
    try:
        import boto3
        
        print("\n🧪 Testing AWS connection...")
        
        # Test STS to verify credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS connection successful!")
        print(f"   Account ID: {identity.get('Account', 'N/A')}")
        print(f"   User ARN: {identity.get('Arn', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS connection failed: {str(e)}")
        return False

def check_existing_credentials():
    """Check if AWS credentials already exist."""
    aws_dir = Path.home() / '.aws'
    credentials_file = aws_dir / 'credentials'
    
    if credentials_file.exists():
        print("📋 Existing AWS credentials found:")
        print(f"   {credentials_file}")
        
        # Check environment variables
        if 'AWS_ACCESS_KEY_ID' in os.environ:
            print("   Environment variables are also set")
        
        return True
    
    return False

def main():
    """Main function to configure AWS credentials."""
    print("🚀 ClinChat-RAG AWS Configuration Tool")
    print("=" * 50)
    
    # Check if credentials already exist
    if check_existing_credentials():
        choice = input("\nCredentials exist. Reconfigure? (y/N): ").strip().lower()
        if choice != 'y':
            print("Using existing credentials...")
            if test_aws_connection():
                return True
            else:
                print("Existing credentials failed. Reconfiguring...")
    
    # Configure new credentials
    if configure_aws_credentials():
        # Test the connection
        if test_aws_connection():
            print("\n🎉 AWS setup complete!")
            
            # Provide GitHub secrets information
            print("\n📝 Next Steps - GitHub Secrets:")
            print("1. Go to: https://github.com/reddygautam98/clinchat-rag/settings/secrets/actions")
            print("2. Add these secrets:")
            print("   - AWS_ACCESS_KEY_ID")
            print("   - AWS_SECRET_ACCESS_KEY")
            print("   - AWS_DEFAULT_REGION")
            print("   - TF_STATE_BUCKET (value: clinchat-terraform-state-bucket)")
            
            return True
        else:
            print("\n❌ Configuration failed. Please check your credentials.")
            return False
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)