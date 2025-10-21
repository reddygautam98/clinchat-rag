#!/usr/bin/env python3
"""
Test AWS Connection using .env file
"""

import os
import sys
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    print("📁 Loading .env file...")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    return True

def test_aws_connection():
    """Test AWS connection."""
    try:
        import boto3
        
        print("🔑 AWS Credentials:")
        print(f"   Access Key: {os.environ.get('AWS_ACCESS_KEY_ID', 'NOT SET')[:8]}...")
        print(f"   Region: {os.environ.get('AWS_REGION', 'NOT SET')}")
        
        print("\n🧪 Testing AWS connection...")
        
        # Test STS
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print("✅ AWS Connection Successful!")
        print(f"   Account ID: {identity.get('Account', 'N/A')}")
        print(f"   User ARN: {identity.get('Arn', 'N/A')}")
        
        # Test S3
        print("\n🪣 Testing S3 access...")
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()
        print(f"✅ S3 Access: Found {len(buckets['Buckets'])} buckets")
        
        # Test DynamoDB
        print("\n🗄️ Testing DynamoDB access...")
        dynamodb = boto3.client('dynamodb')
        tables = dynamodb.list_tables()
        print(f"✅ DynamoDB Access: Found {len(tables['TableNames'])} tables")
        
        # Test ECS
        print("\n🐳 Testing ECS access...")
        ecs = boto3.client('ecs')
        clusters = ecs.list_clusters()
        print(f"✅ ECS Access: Found {len(clusters['clusterArns'])} clusters")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS connection failed: {str(e)}")
        return False

def main():
    print("🔍 AWS .env File Connection Test")
    print("=" * 40)
    
    # Load .env file
    if not load_env_file():
        return False
    
    # Test connection
    if test_aws_connection():
        print("\n🎉 All AWS services are accessible!")
        print("\n📋 Next Steps:")
        print("1. Configure GitHub secrets")
        print("2. Deploy infrastructure via GitHub Actions")
        return True
    else:
        print("\n❌ AWS connection failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)