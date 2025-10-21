#!/usr/bin/env python3
"""
Fix S3 permissions for Terraform state bucket access
"""

import boto3
import json
from botocore.exceptions import ClientError
import os

def fix_s3_permissions():
    """Fix S3 bucket permissions for Terraform state access"""
    
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID', 'AKIAY24YPLC7UTG7RIU2')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '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')
    aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    bucket_name = os.environ.get('TF_STATE_BUCKET', 'clinchat-terraform-state-bucket')
    
    print(f"Fixing S3 permissions for bucket: {bucket_name}")
    
    try:
        # Create S3 and IAM clients
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        iam = boto3.client(
            'iam',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # 1. Check and fix bucket policy
        print("Checking bucket policy...")
        
        # Create a permissive bucket policy for Terraform state access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "TerraformStateAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::607520774335:user/clinchat-github-actions"
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }
        
        try:
            s3.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Updated bucket policy with Terraform permissions")
        except ClientError as e:
            print(f"⚠️ Could not update bucket policy: {e}")
        
        # 2. Check IAM user policies
        print("Checking IAM user policies...")
        
        try:
            # Get current user policies
            user_policies = iam.list_attached_user_policies(UserName='clinchat-github-actions')
            print(f"Current attached policies: {[p['PolicyName'] for p in user_policies['AttachedPolicies']]}")
            
            # Check if user has S3 permissions
            s3_policy_found = False
            for policy in user_policies['AttachedPolicies']:
                if 'S3' in policy['PolicyName'] or 'AmazonS3FullAccess' in policy['PolicyName']:
                    s3_policy_found = True
                    print(f"✅ Found S3 policy: {policy['PolicyName']}")
            
            if not s3_policy_found:
                print("❌ No S3 policy found, need to attach AmazonS3FullAccess")
                
        except ClientError as e:
            print(f"⚠️ Could not check IAM policies: {e}")
        
        # 3. Test bucket access
        print("Testing bucket access...")
        
        try:
            # Test ListBucket permission
            s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            print("✅ ListBucket permission working")
        except ClientError as e:
            print(f"❌ ListBucket failed: {e}")
            
        try:
            # Test PutObject permission
            s3.put_object(
                Bucket=bucket_name,
                Key='test-terraform-access.txt',
                Body='test'
            )
            print("✅ PutObject permission working")
            
            # Clean up test object
            s3.delete_object(Bucket=bucket_name, Key='test-terraform-access.txt')
            print("✅ DeleteObject permission working")
            
        except ClientError as e:
            print(f"❌ Object operations failed: {e}")
        
        # 4. Provide fix instructions
        print("\n" + "="*50)
        print("TERRAFORM S3 PERMISSIONS FIX")
        print("="*50)
        print("If permissions are still failing, manually apply these fixes:")
        print("")
        print("1. AWS Console → IAM → Users → clinchat-github-actions")
        print("2. Attach policy: AmazonS3FullAccess")
        print("3. Or create custom policy with these permissions:")
        print(json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = fix_s3_permissions()
    exit(0 if success else 1)