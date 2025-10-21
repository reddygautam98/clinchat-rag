#!/usr/bin/env python3
"""
Check current DynamoDB permissions for clinchat-github-actions user
"""

import boto3
from botocore.exceptions import ClientError

def check_dynamodb_permissions():
    """Check current DynamoDB permissions for the user"""
    
    # AWS credentials
    aws_access_key_id = "AKIAY24YPLC7UTG7RIU2"
    aws_secret_access_key = "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"
    aws_region = "us-east-1"
    
    print("🔍 Checking Current DynamoDB Permissions")
    print("=" * 50)
    
    try:
        # Create IAM client
        iam = boto3.client(
            'iam',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        username = "clinchat-github-actions"
        
        # Get attached user policies
        print(f"👤 Checking policies for user: {username}")
        
        try:
            response = iam.list_attached_user_policies(UserName=username)
            attached_policies = response['AttachedPolicies']
            
            print(f"\n📋 Currently Attached Policies ({len(attached_policies)}):")
            print("-" * 40)
            
            dynamodb_policy_found = False
            
            for policy in attached_policies:
                policy_name = policy['PolicyName']
                policy_arn = policy['PolicyArn']
                print(f"✅ {policy_name}")
                print(f"   ARN: {policy_arn}")
                
                # Check if DynamoDB policy is attached
                if 'DynamoDB' in policy_name or 'dynamodb' in policy_name.lower():
                    dynamodb_policy_found = True
                    print("   🎯 ← DynamoDB Policy Found!")
                
            # Check specifically for AmazonDynamoDBFullAccess
            amazon_dynamodb_full_access = any(
                policy['PolicyName'] == 'AmazonDynamoDBFullAccess' 
                for policy in attached_policies
            )
            
            print(f"\n🎯 AmazonDynamoDBFullAccess Status:")
            if amazon_dynamodb_full_access:
                print("✅ ATTACHED - User has AmazonDynamoDBFullAccess")
            else:
                print("❌ NOT ATTACHED - Need to add AmazonDynamoDBFullAccess")
            
            return amazon_dynamodb_full_access, attached_policies
            
        except ClientError as e:
            print(f"❌ Error listing user policies: {e}")
            return False, []
            
    except Exception as e:
        print(f"❌ Error checking permissions: {str(e)}")
        return False, []

def test_dynamodb_access():
    """Test actual DynamoDB access"""
    
    print("\n🧪 Testing DynamoDB Access")
    print("=" * 30)
    
    aws_access_key_id = "AKIAY24YPLC7UTG7RIU2"
    aws_secret_access_key = "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"
    aws_region = "us-east-1"
    
    try:
        # Create DynamoDB client
        dynamodb = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # Test 1: List Tables
        try:
            tables_response = dynamodb.list_tables()
            tables = tables_response.get('TableNames', [])
            print(f"✅ ListTables: SUCCESS - Found {len(tables)} tables")
            if tables:
                print(f"📋 Tables: {', '.join(tables)}")
        except ClientError as e:
            print(f"❌ ListTables: FAILED - {e.response['Error']['Code']}")
            print(f"   Message: {e.response['Error']['Message']}")
            return False
        
        # Test 2: Check if terraform-state-lock table exists
        terraform_table = "terraform-state-lock"
        if terraform_table in tables:
            print(f"✅ Terraform table '{terraform_table}' exists")
            
            # Test 3: Describe table
            try:
                describe_response = dynamodb.describe_table(TableName=terraform_table)
                status = describe_response['Table']['TableStatus']
                print(f"✅ DescribeTable: SUCCESS - Status: {status}")
            except ClientError as e:
                print(f"❌ DescribeTable: FAILED - {e.response['Error']['Code']}")
                
        else:
            print(f"⚠️  Terraform table '{terraform_table}' does not exist")
            
            # Test 4: Try to create table (dry run)
            print("🧪 Testing CreateTable permissions...")
            try:
                # This should work if permissions are correct
                create_response = dynamodb.create_table(
                    TableName=f"test-permissions-{aws_access_key_id[-4:]}",
                    KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                    BillingMode='PAY_PER_REQUEST'
                )
                
                test_table_name = create_response['TableDescription']['TableName']
                print(f"✅ CreateTable: SUCCESS - Created test table")
                
                # Clean up test table
                try:
                    dynamodb.delete_table(TableName=test_table_name)
                    print(f"✅ DeleteTable: SUCCESS - Cleaned up test table")
                except:
                    print(f"⚠️  Could not delete test table: {test_table_name}")
                    
            except ClientError as e:
                print(f"❌ CreateTable: FAILED - {e.response['Error']['Code']}")
                print(f"   Message: {e.response['Error']['Message']}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ DynamoDB access test failed: {str(e)}")
        return False

def generate_policy_attachment_command():
    """Generate the exact AWS CLI command to attach the policy"""
    
    print("\n🔧 Policy Attachment Command")
    print("=" * 35)
    
    print("If AmazonDynamoDBFullAccess is not attached, run this AWS CLI command:")
    print("```bash")
    print("aws iam attach-user-policy \\")
    print("  --user-name clinchat-github-actions \\")
    print("  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess")
    print("```")
    
    print("\nOr via AWS Console:")
    print("1. Go to: https://console.aws.amazon.com/iam/")
    print("2. Users → clinchat-github-actions")
    print("3. Permissions → Add permissions → Attach policies directly")
    print("4. Search: AmazonDynamoDBFullAccess")
    print("5. Select and Add permissions")

if __name__ == "__main__":
    print("🎯 DynamoDB Permissions Checker")
    print("=" * 50)
    
    # Check current policies
    has_dynamodb_policy, policies = check_dynamodb_permissions()
    
    # Test actual DynamoDB access
    access_works = test_dynamodb_access()
    
    # Generate summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if has_dynamodb_policy and access_works:
        print("✅ DynamoDB Permissions: FULLY CONFIGURED")
        print("✅ Terraform state locking: READY")
        print("🎉 No action needed - permissions are correct!")
        
    elif has_dynamodb_policy and not access_works:
        print("⚠️  DynamoDB Policy: ATTACHED")
        print("❌ DynamoDB Access: NOT WORKING")
        print("💡 Policy may be propagating - wait 2-3 minutes and try again")
        
    else:
        print("❌ DynamoDB Permissions: MISSING")
        print("🎯 Action Required: Attach AmazonDynamoDBFullAccess policy")
        generate_policy_attachment_command()
    
    print("\n" + "=" * 50)