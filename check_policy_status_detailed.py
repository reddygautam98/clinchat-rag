#!/usr/bin/env python3
"""
AWS Policy Status Checker for ClinChat-RAG Project
Checks which policies are attached and which are missing for the clinchat-github-actions user
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os

def check_policy_status():
    """Check current policy attachment status for ClinChat-RAG deployment"""
    
    print("🔍 ClinChat-RAG AWS Policy Status Checker")
    print("=" * 60)
    
    # Required core policies for basic functionality
    required_policies = {
        'AmazonECS_FullAccess': 'Container orchestration (CRITICAL)',
        'AmazonEC2ContainerRegistryFullAccess': 'Docker image storage (CRITICAL)',
        'AmazonS3FullAccess': 'Terraform state & document storage (CRITICAL)',
        'AmazonDynamoDBFullAccess': 'State locking & session storage (CRITICAL)',
        'IAMReadOnlyAccess': 'Permission verification (REQUIRED)'
    }
    
    # Recommended healthcare compliance policies
    healthcare_policies = {
        'SecurityAudit': 'HIPAA compliance monitoring',
        'CloudWatchFullAccess': 'Performance monitoring & metrics',
        'CloudWatchLogsFullAccess': 'Audit logging (7-year retention)',
        'AWSConfigServiceRolePolicy': 'Configuration compliance tracking'
    }
    
    # Infrastructure policies for production
    infrastructure_policies = {
        'AmazonVPCFullAccess': 'Network isolation & security groups',
        'ElasticLoadBalancingFullAccess': 'Load balancer & SSL termination',
        'AmazonRDSFullAccess': 'PostgreSQL with pgvector database',
        'AmazonElastiCacheFullAccess': 'Redis caching for sessions'
    }
    
    # Advanced security policies
    security_policies = {
        'AWSKeyManagementServicePowerUser': 'KMS encryption key management',
        'AWSCertificateManagerFullAccess': 'SSL/TLS certificate management',
        'AmazonGuardDutyFullAccess': 'Threat detection & monitoring',
        'AWSSecurityHubFullAccess': 'Centralized security findings',
        'AWSCloudTrailFullAccess': 'API audit trail for compliance'
    }
    
    # Medical AI specific policies
    medical_ai_policies = {
        'AmazonTextractFullAccess': 'OCR for medical documents',
        'AmazonComprehendMedicalFullAccess': 'PHI detection & medical NLP',
        'AmazonTranscribeMedicalFullAccess': 'Medical speech transcription',
        'SecretsManagerReadWrite': 'API key & secrets management'
    }
    
    try:
        # Try to create AWS client
        iam = boto3.client('iam')
        user_name = 'clinchat-github-actions'
        
        print(f"👤 Checking policies for user: {user_name}")
        print(f"🔑 Using AWS credentials from environment/config")
        
        # Test AWS connection
        try:
            caller_identity = boto3.client('sts').get_caller_identity()
            print(f"✅ Connected to AWS Account: {caller_identity['Account']}")
            print(f"✅ User ARN: {caller_identity['Arn']}")
        except Exception as e:
            print(f"⚠️  Could not get caller identity: {e}")
        
        # Get currently attached policies
        try:
            response = iam.list_attached_user_policies(UserName=user_name)
            attached_policies = {p['PolicyName']: p['PolicyArn'] for p in response['AttachedPolicies']}
            print(f"📊 Total policies currently attached: {len(attached_policies)}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"❌ User '{user_name}' not found!")
                return False
            else:
                print(f"❌ Error accessing user policies: {e}")
                return False
        
        print("\n" + "="*60)
        
        # Check each category
        def check_policy_category(category_name, policies, emoji):
            print(f"\n{emoji} {category_name.upper()}")
            print("-" * 50)
            
            attached_count = 0
            missing_count = 0
            
            for policy_name, description in policies.items():
                if policy_name in attached_policies:
                    print(f"  ✅ {policy_name}")
                    print(f"     └─ {description}")
                    attached_count += 1
                else:
                    print(f"  ❌ {policy_name} - MISSING")
                    print(f"     └─ {description}")
                    missing_count += 1
            
            print(f"\n  📊 Status: {attached_count}/{len(policies)} policies attached")
            if missing_count > 0:
                print(f"  🚨 Action needed: {missing_count} policies missing")
            else:
                print(f"  🎉 All {category_name} policies attached!")
                
            return attached_count, missing_count
        
        # Check all categories
        total_attached = 0
        total_missing = 0
        
        # Required policies (CRITICAL)
        attached, missing = check_policy_category("Required Core Policies", required_policies, "🎯")
        total_attached += attached
        total_missing += missing
        critical_missing = missing
        
        # Healthcare compliance policies
        attached, missing = check_policy_category("Healthcare Compliance", healthcare_policies, "🏥")
        total_attached += attached
        total_missing += missing
        
        # Infrastructure policies
        attached, missing = check_policy_category("Infrastructure Policies", infrastructure_policies, "🏗️")
        total_attached += attached
        total_missing += missing
        
        # Security policies
        attached, missing = check_policy_category("Security Policies", security_policies, "🔐")
        total_attached += attached
        total_missing += missing
        
        # Medical AI policies
        attached, missing = check_policy_category("Medical AI Policies", medical_ai_policies, "🤖")
        total_attached += attached
        total_missing += missing
        
        # Overall summary
        print("\n" + "="*60)
        print("📋 OVERALL POLICY STATUS SUMMARY")
        print("="*60)
        
        total_policies = total_attached + total_missing
        completion_percentage = (total_attached / total_policies * 100) if total_policies > 0 else 0
        
        print(f"📊 Total Policies Checked: {total_policies}")
        print(f"✅ Policies Attached: {total_attached}")
        print(f"❌ Policies Missing: {total_missing}")
        print(f"📈 Completion Rate: {completion_percentage:.1f}%")
        
        # Deployment readiness assessment
        print(f"\n🚀 DEPLOYMENT READINESS ASSESSMENT:")
        print("-" * 40)
        
        if critical_missing == 0:
            print("✅ READY: All critical policies attached!")
            print("   └─ Basic deployment can proceed")
        else:
            print(f"🚨 BLOCKED: {critical_missing} critical policies missing!")
            print("   └─ Deployment will fail without these policies")
        
        if total_missing == 0:
            print("🎉 COMPLETE: All recommended policies attached!")
            print("   └─ Production-ready with full compliance")
        elif total_missing <= 5:
            print(f"⚠️  PARTIAL: {total_missing} optional policies missing")
            print("   └─ Deployment possible but not fully optimized")
        else:
            print(f"📝 INCOMPLETE: {total_missing} policies missing")
            print("   └─ Significant setup work remaining")
        
        # Priority actions
        print(f"\n🎯 PRIORITY ACTIONS:")
        print("-" * 20)
        
        if 'AmazonDynamoDBFullAccess' not in attached_policies:
            print("1. 🚨 URGENT: Add AmazonDynamoDBFullAccess")
            print("   └─ Required for Terraform state locking")
        
        if 'AmazonS3FullAccess' in attached_policies:
            # Check if S3 access is working (not quarantined)
            try:
                s3 = boto3.client('s3')
                s3.list_buckets()
                print("2. ✅ S3 Access: Working normally")
            except ClientError as e:
                if 'quarantine' in str(e).lower():
                    print("2. 🚨 URGENT: S3 access quarantined - create new AWS credentials")
                else:
                    print(f"2. ⚠️  S3 Access Issue: {e}")
        else:
            print("2. 🚨 URGENT: Add AmazonS3FullAccess")
        
        if 'SecurityAudit' not in attached_policies:
            print("3. 📋 Recommended: Add SecurityAudit for HIPAA compliance")
        
        if 'CloudWatchFullAccess' not in attached_policies:
            print("4. 📋 Recommended: Add CloudWatchFullAccess for monitoring")
        
        # Quick fix commands
        print(f"\n🔧 QUICK FIX COMMANDS:")
        print("-" * 25)
        
        missing_required = [policy for policy in required_policies.keys() if policy not in attached_policies]
        if missing_required:
            print("# AWS CLI commands to add missing critical policies:")
            for policy in missing_required:
                print(f"aws iam attach-user-policy --user-name {user_name} --policy-arn arn:aws:iam::aws:policy/{policy}")
        
        # Environment-specific recommendations
        print(f"\n🌍 ENVIRONMENT RECOMMENDATIONS:")
        print("-" * 35)
        
        if critical_missing == 0:
            if total_missing == 0:
                print("🎯 PRODUCTION READY: All policies configured")
            elif total_missing <= 3:
                print("🎯 STAGING READY: Core + compliance policies active")
            else:
                print("🎯 DEVELOPMENT READY: Core policies sufficient for dev work")
        else:
            print("🎯 NOT READY: Add critical policies before any deployment")
        
        return critical_missing == 0
        
    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("   Configure AWS credentials using:")
        print("   - AWS CLI: aws configure")
        print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("   - IAM roles (if running on EC2)")
        return False
        
    except ClientError as e:
        print(f"❌ AWS API Error: {e}")
        if 'AccessDenied' in str(e):
            print("   Check if current credentials have IAM read permissions")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_github_secrets_status():
    """Check if GitHub secrets are properly configured"""
    print(f"\n🔐 GITHUB SECRETS STATUS:")
    print("-" * 30)
    
    required_secrets = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_DEFAULT_REGION',
        'TF_STATE_BUCKET'
    ]
    
    print("Required GitHub Secrets for CI/CD:")
    for secret in required_secrets:
        # Check if secret exists in environment (for testing)
        if os.environ.get(secret):
            print(f"  ✅ {secret} - Available in environment")
        else:
            print(f"  ❓ {secret} - Configure in GitHub repository")
    
    print(f"\n📍 Configure at:")
    print(f"   https://github.com/reddygautam98/clinchat-rag/settings/secrets/actions")

if __name__ == "__main__":
    print("Starting AWS Policy Status Check...\n")
    
    # Check AWS policies
    is_ready = check_policy_status()
    
    # Check GitHub secrets status
    check_github_secrets_status()
    
    # Final status
    print(f"\n" + "="*60)
    print("🏁 FINAL STATUS")
    print("="*60)
    
    if is_ready:
        print("✅ AWS POLICIES: Ready for deployment")
        print("🚀 Next step: Ensure GitHub secrets are configured")
        print("📝 Then: git push to trigger automated deployment")
    else:
        print("🚨 AWS POLICIES: Critical policies missing")
        print("⚠️  Deployment will fail until policies are attached")
        print("🔧 Add missing policies using AWS Console or CLI commands above")
    
    print(f"\n📅 Status checked on: October 21, 2025")
    print(f"🔄 Re-run this script after making changes")