#!/usr/bin/env python3
"""
Check S3 bucket permissions for Terraform state
"""

import boto3
import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key.startswith('AWS_'):
                        os.environ[key] = value

def check_s3_permissions():
    """Check S3 bucket permissions."""
    try:
        s3 = boto3.client('s3')
        bucket_name = 'clinchat-terraform-state-bucket'
        
        print('🔍 Checking S3 bucket permissions...')
        print(f'   Bucket: {bucket_name}')
        
        # Test bucket access
        response = s3.head_bucket(Bucket=bucket_name)
        print(f'✅ Bucket exists and accessible')
        
        # Test list objects
        try:
            objects = s3.list_objects_v2(Bucket=bucket_name)
            print(f'✅ Can list objects in bucket')
            if objects.get('Contents'):
                print(f'📄 Found {len(objects["Contents"])} objects')
                for obj in objects['Contents'][:3]:  # Show first 3 objects
                    print(f'   - {obj["Key"]} ({obj["Size"]} bytes)')
            else:
                print('📄 Bucket is empty (expected for new deployment)')
        except Exception as e:
            print(f'❌ List objects failed: {e}')
        
        # Test write permissions
        try:
            test_key = 'test-permissions.txt'
            s3.put_object(Bucket=bucket_name, Key=test_key, Body='test')
            print('✅ Write permissions working')
            s3.delete_object(Bucket=bucket_name, Key=test_key)
            print('✅ Delete permissions working')
        except Exception as e:
            print(f'❌ Write/Delete test failed: {e}')
            
        return True
        
    except Exception as e:
        print(f'❌ Bucket access failed: {e}')
        return False

def main():
    print('🔍 S3 Terraform State Bucket Permission Check')
    print('=' * 50)
    
    load_env()
    
    if check_s3_permissions():
        print('\n✅ S3 permissions are working correctly!')
        print('The GitHub Actions failure is likely due to a different issue.')
    else:
        print('\n❌ S3 permission issues detected!')
        print('This could be the cause of GitHub Actions failures.')

if __name__ == "__main__":
    main()