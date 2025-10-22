#!/usr/bin/env python3
"""
Programmatically check current AWS policy usage
"""

import boto3
import os
from pathlib import Path
from datetime import datetime

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

def check_user_policies():
    """Check policies attached to current user."""
    try:
        iam = boto3.client('iam')
        
        # Get current user info
        sts = boto3.client('sts')
        caller_info = sts.get_caller_identity()
        user_arn = caller_info['Arn']
        username = user_arn.split('/')[-1]
        
        print(f"🔍 Checking policies for user: {username}")
        print(f"📋 Account ID: {caller_info['Account']}")
        print(f"🎯 User ARN: {user_arn}")
        
        # Get attached policies
        response = iam.list_attached_user_policies(UserName=username)
        attached_policies = response['AttachedPolicies']
        
        print(f"\n📊 ATTACHED POLICIES ({len(attached_policies)}):")
        print("=" * 60)
        
        for i, policy in enumerate(attached_policies, 1):
            policy_name = policy['PolicyName']
            policy_arn = policy['PolicyArn']
            
            print(f"{i:2d}. {policy_name}")
            print(f"    ARN: {policy_arn}")
            
            # Get policy details
            try:
                policy_details = iam.get_policy(PolicyArn=policy_arn)
                policy_info = policy_details['Policy']
                
                print(f"    Description: {policy_info.get('Description', 'No description')}")
                print(f"    Created: {policy_info['CreateDate'].strftime('%Y-%m-%d')}")
                print(f"    Updated: {policy_info['UpdateDate'].strftime('%Y-%m-%d')}")
                
                # Check if it's AWS managed
                if policy_arn.startswith('arn:aws:iam::aws:policy/'):
                    print("    Type: ✅ AWS Managed Policy")
                else:
                    print("    Type: 🔧 Customer Managed Policy")
                    
            except Exception as e:
                print(f"    Error getting details: {e}")
            
            print()
        
        return attached_policies
        
    except Exception as e:
        print(f"❌ Error checking policies: {e}")
        return []

def check_policy_usage(policy_arn):
    """Check who else is using a specific policy."""
    try:
        iam = boto3.client('iam')
        
        print(f"\n🔍 CHECKING USAGE FOR: {policy_arn.split('/')[-1]}")
        print("=" * 60)
        
        # Get entities for policy
        response = iam.list_entities_for_policy(PolicyArn=policy_arn)
        
        users = response.get('PolicyUsers', [])
        groups = response.get('PolicyGroups', [])
        roles = response.get('PolicyRoles', [])
        
        print(f"👥 Users with this policy: {len(users)}")
        for user in users[:5]:  # Show first 5
            print(f"   - {user['UserName']}")
        if len(users) > 5:
            print(f"   ... and {len(users) - 5} more users")
        
        print(f"\n🏷️  Groups with this policy: {len(groups)}")
        for group in groups[:5]:
            print(f"   - {group['GroupName']}")
        
        print(f"\n🎭 Roles with this policy: {len(roles)}")
        for role in roles[:5]:
            print(f"   - {role['RoleName']}")
        if len(roles) > 5:
            print(f"   ... and {len(roles) - 5} more roles")
            
    except Exception as e:
        print(f"❌ Error checking policy usage: {e}")

def generate_policy_report():
    """Generate a comprehensive policy report."""
    
    print("📋 AWS POLICY USAGE REPORT")
    print("=" * 60)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check user policies
    attached_policies = check_user_policies()
    
    if not attached_policies:
        print("❌ No policies found or unable to retrieve policies")
        return
    
    # Check usage for key policies
    key_policies = [
        'AmazonS3FullAccess',
        'AmazonECS_FullAccess', 
        'AmazonDynamoDBFullAccess'
    ]
    
    print("\n" + "="*60)
    print("🔍 KEY POLICY USAGE ANALYSIS")
    print("="*60)
    
    for policy_name in key_policies:
        # Find matching policy ARN
        matching_policy = None
        for policy in attached_policies:
            if policy_name in policy['PolicyName']:
                matching_policy = policy
                break
        
        if matching_policy:
            check_policy_usage(matching_policy['PolicyArn'])
        else:
            print(f"\n❌ {policy_name} not found in attached policies")

def main():
    print("🎯 AWS Account Policy Usage Checker")
    print("=" * 60)
    
    load_env()
    generate_policy_report()
    
    print("\n" + "="*60)
    print("💡 NEXT STEPS")
    print("="*60)
    print("1. Review the policies listed above")
    print("2. Check AWS Console for visual confirmation:")
    print("   https://console.aws.amazon.com/iam/home#/users/clinchat-github-actions")
    print("3. Use the AWS Console methods from the guide for detailed analysis")

if __name__ == "__main__":
    main()