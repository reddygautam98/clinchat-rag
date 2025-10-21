#!/usr/bin/env python3
"""
Create Terraform DynamoDB state lock table
"""

import boto3
from botocore.exceptions import ClientError

def create_terraform_state_lock_table():
    """Create the terraform-state-lock DynamoDB table"""
    
    # AWS credentials
    aws_access_key_id = "AKIAY24YPLC7UTG7RIU2"
    aws_secret_access_key = "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"
    aws_region = "us-east-1"
    table_name = "terraform-state-lock"
    
    print("🚀 Creating Terraform State Lock Table")
    print("=" * 45)
    
    try:
        # Create DynamoDB client
        dynamodb = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # Check if table already exists
        try:
            existing_tables = dynamodb.list_tables()['TableNames']
            if table_name in existing_tables:
                print(f"✅ Table '{table_name}' already exists")
                
                # Check table status
                table_info = dynamodb.describe_table(TableName=table_name)
                status = table_info['Table']['TableStatus']
                print(f"📊 Table status: {status}")
                
                if status == 'ACTIVE':
                    print("🎉 Terraform state locking is ready!")
                    return True
                else:
                    print(f"⏳ Table is {status}, waiting for ACTIVE status...")
                    
        except ClientError:
            pass  # Table doesn't exist, continue with creation
        
        print(f"🔨 Creating table '{table_name}'...")
        
        # Create the table with proper configuration for Terraform state locking
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'LockID',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'LockID',
                    'AttributeType': 'S'  # String type
                }
            ],
            BillingMode='PAY_PER_REQUEST',  # No provisioned capacity needed
            Tags=[
                {
                    'Key': 'Purpose',
                    'Value': 'TerraformStateLocking'
                },
                {
                    'Key': 'Project', 
                    'Value': 'ClinChat-RAG'
                },
                {
                    'Key': 'ManagedBy',
                    'Value': 'Terraform'
                }
            ]
        )
        
        creation_status = response['TableDescription']['TableStatus']
        print(f"✅ Table creation initiated: {creation_status}")
        
        # Wait for table to become active
        print("⏳ Waiting for table to become ACTIVE...")
        
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 5,  # Check every 5 seconds
                'MaxAttempts': 24  # Wait up to 2 minutes
            }
        )
        
        # Verify table is active
        final_status = dynamodb.describe_table(TableName=table_name)
        table_status = final_status['Table']['TableStatus']
        
        if table_status == 'ACTIVE':
            print("🎉 Terraform state lock table created successfully!")
            print(f"📊 Table ARN: {final_status['Table']['TableArn']}")
            return True
        else:
            print(f"⚠️  Table status: {table_status}")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS Error: {error_code}")
        print(f"📝 Message: {error_message}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def cleanup_test_table():
    """Clean up any test tables created during permission testing"""
    
    aws_access_key_id = "AKIAY24YPLC7UTG7RIU2"
    aws_secret_access_key = "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"
    aws_region = "us-east-1"
    
    print("\n🧹 Cleaning up test tables...")
    
    try:
        dynamodb = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        # List all tables
        tables = dynamodb.list_tables()['TableNames']
        
        # Find test tables
        test_tables = [t for t in tables if t.startswith('test-permissions-')]
        
        if test_tables:
            for test_table in test_tables:
                print(f"🗑️  Deleting test table: {test_table}")
                try:
                    dynamodb.delete_table(TableName=test_table)
                    print(f"✅ Deleted: {test_table}")
                except ClientError as e:
                    print(f"⚠️  Could not delete {test_table}: {e}")
        else:
            print("✅ No test tables to clean up")
            
    except Exception as e:
        print(f"⚠️  Cleanup error: {str(e)}")

def verify_terraform_backend():
    """Verify both S3 and DynamoDB components are ready"""
    
    print("\n🔍 Verifying Complete Terraform Backend Setup")
    print("=" * 50)
    
    aws_access_key_id = "AKIAY24YPLC7UTG7RIU2"
    aws_secret_access_key = "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"
    aws_region = "us-east-1"
    
    s3_bucket = "clinchat-terraform-state-bucket"
    dynamodb_table = "terraform-state-lock"
    
    # Check S3
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, 
                         aws_secret_access_key=aws_secret_access_key, region_name=aws_region)
        s3.head_bucket(Bucket=s3_bucket)
        print(f"✅ S3 State Storage: {s3_bucket} (ready)")
    except Exception as e:
        print(f"❌ S3 State Storage: {e}")
        return False
    
    # Check DynamoDB
    try:
        dynamodb = boto3.client('dynamodb', aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key, region_name=aws_region)
        table_info = dynamodb.describe_table(TableName=dynamodb_table)
        status = table_info['Table']['TableStatus']
        print(f"✅ DynamoDB State Locking: {dynamodb_table} ({status})")
    except Exception as e:
        print(f"❌ DynamoDB State Locking: {e}")
        return False
    
    print("\n🎉 TERRAFORM BACKEND FULLY CONFIGURED!")
    print("🚀 Ready for infrastructure deployment!")
    return True

if __name__ == "__main__":
    print("🎯 Terraform Backend Setup")
    print("=" * 30)
    
    # Clean up any test tables first
    cleanup_test_table()
    
    # Create the terraform state lock table
    success = create_terraform_state_lock_table()
    
    if success:
        # Verify complete backend setup
        verify_terraform_backend()
    else:
        print("❌ Failed to create Terraform state lock table")
        print("💡 Please check the error messages above")
    
    print("\n" + "=" * 50)