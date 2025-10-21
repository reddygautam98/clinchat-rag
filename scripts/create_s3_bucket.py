#!/usr/bin/env python3
"""
Create the S3 bucket for Terraform state storage
"""

import boto3
from botocore.exceptions import ClientError
import os

def create_s3_bucket():
    """Create S3 bucket for Terraform state if it doesn't exist"""
    
    # Get credentials from environment (set by GitHub Actions)
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID', 'AKIAY24YPLC7UTG7RIU2')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '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')
    aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    bucket_name = os.environ.get('TF_STATE_BUCKET', 'clinchat-terraform-state-bucket')
    
    print(f"Creating S3 bucket: {bucket_name}")
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket {bucket_name} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"Creating bucket {bucket_name}...")
            else:
                print(f"Error checking bucket: {e}")
                return False
        
        # Create bucket
        if aws_region == 'us-east-1':
            # For us-east-1, don't specify LocationConstraint
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': aws_region}
            )
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Enable encryption
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )
        
        # Block public access
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        
        print(f"✅ Successfully created and configured bucket: {bucket_name}")
        return True
        
    except ClientError as e:
        print(f"❌ Error creating bucket: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = create_s3_bucket()
    exit(0 if success else 1)