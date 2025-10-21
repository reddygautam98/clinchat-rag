#!/usr/bin/env python3
"""
Check AWS infrastructure status for ClinChat-RAG
"""

import boto3
from botocore.exceptions import ClientError
import os

def check_aws_status():
    """Check current AWS infrastructure status"""
    
    # AWS credentials
    aws_access_key_id = "AKIAY24YPLC7UTG7RIU2"
    aws_secret_access_key = "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" 
    aws_region = "us-east-1"
    
    print("CHECKING AWS INFRASTRUCTURE STATUS")
    print("=" * 50)
    
    pending_work = []
    completed_work = []
    
    try:
        # Check S3 bucket
        s3 = boto3.client('s3', 
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key, 
                         region_name=aws_region)
        
        bucket_name = "clinchat-terraform-state-bucket"
        try:
            s3.head_bucket(Bucket=bucket_name)
            completed_work.append(f"S3 Bucket: {bucket_name} (ACTIVE)")
            
            # Check if Terraform state exists
            try:
                objects = s3.list_objects_v2(Bucket=bucket_name, Prefix='terraform.tfstate')
                if 'Contents' in objects:
                    completed_work.append("Terraform state file exists in S3")
                else:
                    pending_work.append("Terraform state file - will be created on first apply")
            except ClientError:
                pending_work.append("Terraform state file - will be created on first apply")
                
        except ClientError as e:
            pending_work.append(f"S3 Bucket: {bucket_name} - NEEDS CREATION")

        # Check DynamoDB table  
        dynamodb = boto3.client('dynamodb',
                               aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key,
                               region_name=aws_region)
        
        table_name = "terraform-state-lock"
        try:
            table_info = dynamodb.describe_table(TableName=table_name)
            status = table_info['Table']['TableStatus']
            completed_work.append(f"DynamoDB Table: {table_name} ({status})")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                pending_work.append(f"DynamoDB Table: {table_name} - NEEDS CREATION")
            else:
                pending_work.append(f"DynamoDB Table: ERROR - {e}")

        # Check ECS clusters
        ecs = boto3.client('ecs',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=aws_region)
        
        try:
            clusters = ecs.list_clusters()
            clinchat_clusters = [c for c in clusters['clusterArns'] if 'clinchat' in c.lower()]
            if clinchat_clusters:
                completed_work.append(f"ECS Clusters: {len(clinchat_clusters)} found")
                for cluster in clinchat_clusters:
                    cluster_name = cluster.split('/')[-1]
                    completed_work.append(f"  - {cluster_name}")
            else:
                pending_work.append("ECS Clusters: Will be created by Terraform deployment")
        except ClientError as e:
            pending_work.append(f"ECS Clusters: ERROR - {e}")

        # Check ECR repositories
        ecr = boto3.client('ecr',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=aws_region)
        
        try:
            repos = ecr.describe_repositories()
            clinchat_repos = [r for r in repos['repositories'] if 'clinchat' in r['repositoryName'].lower()]
            if clinchat_repos:
                completed_work.append(f"ECR Repositories: {len(clinchat_repos)} found")
                for repo in clinchat_repos:
                    completed_work.append(f"  - {repo['repositoryName']}")
            else:
                pending_work.append("ECR Repositories: Will be created by Terraform deployment")
        except ClientError as e:
            pending_work.append(f"ECR Repositories: ERROR - {e}")

        # Check Load Balancers
        elbv2 = boto3.client('elbv2',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key,
                            region_name=aws_region)
        
        try:
            lbs = elbv2.describe_load_balancers()
            clinchat_lbs = [lb for lb in lbs['LoadBalancers'] if 'clinchat' in lb['LoadBalancerName'].lower()]
            if clinchat_lbs:
                completed_work.append(f"Load Balancers: {len(clinchat_lbs)} found")
                for lb in clinchat_lbs:
                    completed_work.append(f"  - {lb['LoadBalancerName']} ({lb['State']['Code']})")
            else:
                pending_work.append("Load Balancers: Will be created by Terraform deployment")
        except ClientError as e:
            pending_work.append(f"Load Balancers: ERROR - {e}")

    except Exception as e:
        pending_work.append(f"AWS Connection Error: {str(e)}")

    # Print results
    print(f"\nCOMPLETED INFRASTRUCTURE:")
    print("=" * 30)
    if completed_work:
        for item in completed_work:
            print(f"[DONE] {item}")
    else:
        print("None yet - awaiting initial deployment")

    print(f"\nPENDING WORK:")
    print("=" * 15)
    if pending_work:
        for item in pending_work:
            print(f"[TODO] {item}")
    else:
        print("All infrastructure is deployed!")

    # GitHub secrets check
    print(f"\nGITHUB CONFIGURATION:")
    print("=" * 25)
    print("[TODO] Verify GitHub secrets are configured:")
    print("  - AWS_ACCESS_KEY_ID")
    print("  - AWS_SECRET_ACCESS_KEY") 
    print("  - AWS_DEFAULT_REGION")
    print("  - TF_STATE_BUCKET")
    
    print(f"\nNEXT STEPS:")
    print("=" * 15)
    if pending_work:
        print("1. Configure GitHub secrets (if not done)")
        print("2. Trigger GitHub Actions workflow to deploy infrastructure")
        print("3. Monitor deployment in GitHub Actions tab")
    else:
        print("Infrastructure is ready! You can deploy application updates.")

    return len(pending_work)

if __name__ == "__main__":
    pending_count = check_aws_status()
    if pending_count == 0:
        print(f"\nSTATUS: All AWS infrastructure is ready!")
    else:
        print(f"\nSTATUS: {pending_count} items need deployment")