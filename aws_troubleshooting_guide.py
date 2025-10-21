#!/usr/bin/env python3
"""
AWS Credential Troubleshooting Guide
"""

def show_troubleshooting_guide():
    print("🔍 AWS Credentials Troubleshooting Guide")
    print("=" * 50)
    
    print("\n❌ ERROR: Invalid AWS Credentials")
    print("The credentials provided are not valid. Here's how to fix this:")
    
    print("\n📋 Step 1: Get Valid Credentials")
    print("1. Go to AWS Console: https://console.aws.amazon.com/")
    print("2. Navigate to: IAM > Users > [Your Username]")
    print("3. Click 'Security credentials' tab")
    print("4. In 'Access keys' section:")
    print("   - If you have existing keys, check if they're 'Active'")
    print("   - If inactive/expired, create new access keys")
    print("   - Click 'Create access key'")
    
    print("\n🔑 Step 2: Required IAM Permissions")
    print("Your AWS user needs these policies attached:")
    print("- AmazonS3FullAccess")
    print("- AmazonDynamoDBFullAccess") 
    print("- AmazonECS_FullAccess")
    print("- AmazonEC2ContainerRegistryFullAccess")
    print("- ElasticLoadBalancingFullAccess")
    print("- IAMReadOnlyAccess")
    
    print("\n⚠️  Alternative Solution: Use Environment Variables")
    print("If you prefer not to store credentials in files:")
    
    print("\nFor PowerShell:")
    print("$env:AWS_ACCESS_KEY_ID='your-access-key-id'")
    print("$env:AWS_SECRET_ACCESS_KEY='your-secret-access-key'")
    print("$env:AWS_DEFAULT_REGION='us-east-1'")
    
    print("\n🔄 Step 3: Re-run Configuration")
    print("After getting valid credentials, run:")
    print("python fix_aws_credentials.py")
    
    print("\n📞 Need Help?")
    print("1. Check AWS user exists: IAM > Users")
    print("2. Verify user has required policies")
    print("3. Ensure access keys are 'Active' status")
    print("4. Try creating new access keys")

if __name__ == "__main__":
    show_troubleshooting_guide()