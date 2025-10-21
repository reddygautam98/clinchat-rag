#!/usr/bin/env python3
"""
Automatically re-enable S3 backend after new credentials are created
"""

import os

def restore_s3_backend():
    """Restore S3 backend configuration in Terraform"""
    
    terraform_file = "infrastructure/main.tf"
    
    # Read current file
    with open(terraform_file, 'r') as f:
        content = f.read()
    
    # Replace commented S3 backend with active configuration
    old_backend = """  # Temporarily using local backend due to S3 access restrictions
  # backend "s3" {
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }"""
    
    new_backend = """  backend "s3" {
    bucket         = "clinchat-terraform-state-bucket"
    key            = "terraform/state"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }"""
    
    if old_backend in content:
        content = content.replace(old_backend, new_backend)
        
        with open(terraform_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Restored S3 backend configuration in {terraform_file}")
        return True
    else:
        print(f"⚠️ S3 backend configuration not found or already restored")
        return False

def update_workflow():
    """Update GitHub Actions workflow to use S3 backend"""
    
    workflow_file = ".github/workflows/deploy-infrastructure.yml"
    
    with open(workflow_file, 'r') as f:
        content = f.read()
    
    # Add S3 bucket creation and backend configuration
    old_init = """    - name: Terraform Init
      working-directory: infrastructure/
      run: terraform init"""
    
    new_init = """    - name: Create S3 bucket for Terraform state
      run: python scripts/create_s3_bucket.py
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_DEFAULT_REGION: ${{ secrets.AWS_DEFAULT_REGION }}
        TF_STATE_BUCKET: ${{ secrets.TF_STATE_BUCKET }}

    - name: Terraform Init
      working-directory: infrastructure/
      run: |
        terraform init \\
          -backend-config="bucket=${{ secrets.TF_STATE_BUCKET }}" \\
          -backend-config="key=terraform/state" \\
          -backend-config="region=${{ secrets.AWS_DEFAULT_REGION }}" \\
          -backend-config="dynamodb_table=terraform-state-lock"""
    
    if old_init in content and "backend-config" not in content:
        content = content.replace(old_init, new_init)
        
        with open(workflow_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated workflow to use S3 backend in {workflow_file}")
        return True
    else:
        print(f"⚠️ Workflow already configured for S3 backend")
        return False

def test_credentials():
    """Test if new credentials work"""
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Use environment variables (will be set by GitHub Actions)
        s3 = boto3.client('s3')
        
        # Test basic S3 access
        s3.list_buckets()
        print("✅ New credentials working - S3 access successful!")
        return True
        
    except ClientError as e:
        if "AccessDenied" in str(e):
            print("❌ Still getting access denied - check if quarantine policy is removed")
        else:
            print(f"❌ Credential test failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Could not test credentials: {e}")
        return False

if __name__ == "__main__":
    print("🔧 RESTORING S3 BACKEND CONFIGURATION")
    print("=" * 40)
    
    # Check if running in GitHub Actions (has environment variables)
    if os.environ.get('GITHUB_ACTIONS'):
        print("🟢 Running in GitHub Actions - testing credentials...")
        
        if test_credentials():
            print("🔄 Enabling S3 backend...")
            restore_s3_backend()
            update_workflow()
            print("🎉 S3 backend restored successfully!")
        else:
            print("⚠️ Credentials still not working - keeping local backend")
    else:
        print("🔧 Manual execution - preparing S3 backend configuration...")
        restore_s3_backend()
        print("\n📋 NEXT STEPS:")
        print("1. Create new AWS credentials (remove quarantine policy)")
        print("2. Update GitHub secrets with new credentials") 
        print("3. Push changes to trigger deployment with S3 backend")
        print("4. Monitor GitHub Actions for successful S3 backend initialization")