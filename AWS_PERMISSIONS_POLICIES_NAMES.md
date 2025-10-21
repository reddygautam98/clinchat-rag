# 📋 AWS Permissions Policies Names for ClinChat-RAG

## 🎯 **REQUIRED CORE POLICIES (5 Essential)**

### **Container & Compute Services**
```yaml
1. AmazonECS_FullAccess
   ARN: arn:aws:iam::aws:policy/AmazonECS_FullAccess
   Purpose: ECS cluster management, task definitions, services

2. AmazonEC2ContainerRegistryFullAccess  
   ARN: arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
   Purpose: Docker image storage and retrieval (private repositories)

3. AmazonElasticContainerRegistryPublicFullAccess
   ARN: arn:aws:iam::aws:policy/AmazonElasticContainerRegistryPublicFullAccess
   Purpose: Public Docker image registry access, public repository management

4. EC2InstanceProfileForImageBuilder
   ARN: arn:aws:iam::aws:policy/EC2InstanceProfileForImageBuilder
   Purpose: Container image building and optimization

5. AmazonEC2ContainerRegistryReadOnly
   ARN: arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
   Purpose: Read-only access to private container repositories
```

### **Storage & Database Services**
```yaml
6. AmazonS3FullAccess
   ARN: arn:aws:iam::aws:policy/AmazonS3FullAccess
   Purpose: Terraform state storage, document uploads, configuration files

7. AmazonS3ReadOnlyAccess
   ARN: arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
   Purpose: Read-only access to S3 buckets for monitoring

8. AmazonDynamoDBFullAccess
   ARN: arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
   Purpose: Terraform state locking, session storage, audit data

9. AmazonDynamoDBReadOnlyAccess
   ARN: arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess
   Purpose: Read-only access to DynamoDB tables for monitoring

10. AmazonRDSFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonRDSFullAccess
    Purpose: PostgreSQL with pgvector, managed database services

11. AmazonRDSReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonRDSReadOnlyAccess
    Purpose: Read-only access to RDS instances for monitoring
```

### **Identity & Access Management**
```yaml
12. IAMReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/IAMReadOnlyAccess
    Purpose: User and role verification, permission auditing

13. IAMFullAccess
    ARN: arn:aws:iam::aws:policy/IAMFullAccess
    Purpose: Complete IAM management (use with caution)

14. IAMUserChangePassword
    ARN: arn:aws:iam::aws:policy/IAMUserChangePassword
    Purpose: Allow users to change their own passwords

15. IAMSelfManageServiceSpecificCredentials
    ARN: arn:aws:iam::aws:policy/IAMSelfManageServiceSpecificCredentials
    Purpose: Self-service credential management
```

---

## 🏥 **HEALTHCARE COMPLIANCE POLICIES (4 Recommended)**

### **Security & Monitoring**
```yaml
16. SecurityAudit
    ARN: arn:aws:iam::aws:policy/SecurityAudit
    Purpose: HIPAA compliance monitoring, security assessments

17. CloudWatchFullAccess
    ARN: arn:aws:iam::aws:policy/CloudWatchFullAccess
    Purpose: Performance monitoring, health checks, metrics

18. CloudWatchLogsFullAccess
    ARN: arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
    Purpose: Audit logging, compliance tracking, incident investigation

19. CloudWatchReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess
    Purpose: Read-only monitoring access for developers

20. CloudWatchAgentServerPolicy
    ARN: arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
    Purpose: CloudWatch agent permissions for EC2 instances

21. CloudWatchApplicationInsightsFullAccess
    ARN: arn:aws:iam::aws:policy/CloudWatchApplicationInsightsFullAccess
    Purpose: Application performance monitoring and insights
```

### **Configuration Management**
```yaml
22. AWSConfigServiceRolePolicy
    ARN: arn:aws:iam::aws:policy/service-role/AWS_ConfigRole
    Purpose: Configuration compliance monitoring, resource tracking

23. ConfigRole
    ARN: arn:aws:iam::aws:policy/service-role/ConfigRole
    Purpose: AWS Config service role for configuration recording

24. AWSConfigRole
    ARN: arn:aws:iam::aws:policy/service-role/AWSConfigRole
    Purpose: Enhanced AWS Config permissions for compliance

25. AWSConfigUserAccess
    ARN: arn:aws:iam::aws:policy/AWSConfigUserAccess
    Purpose: User access to AWS Config console and APIs
```

---

## 🌐 **INFRASTRUCTURE POLICIES (6 Optional)**

### **Networking & Load Balancing**
```yaml
26. AmazonVPCFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonVPCFullAccess
    Purpose: Network isolation, security groups, VPC management

27. AmazonVPCReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonVPCReadOnlyAccess
    Purpose: Read-only access to VPC resources for monitoring

28. ElasticLoadBalancingFullAccess
    ARN: arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
    Purpose: Application Load Balancer, SSL termination, traffic routing

29. ElasticLoadBalancingReadOnly
    ARN: arn:aws:iam::aws:policy/ElasticLoadBalancingReadOnly
    Purpose: Read-only access to load balancer configurations

30. AmazonEC2FullAccess
    ARN: arn:aws:iam::aws:policy/AmazonEC2FullAccess
    Purpose: Complete EC2 management for ECS instances

31. AmazonEC2ReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess
    Purpose: Read-only access to EC2 resources for monitoring
```

### **Additional Database Services**
```yaml
32. AmazonElastiCacheFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess
    Purpose: Redis cache management for session storage

33. AmazonElastiCacheReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonElastiCacheReadOnlyAccess
    Purpose: Read-only access to ElastiCache clusters

34. AmazonDocumentDBFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonDocumentDBFullAccess
    Purpose: Document database for unstructured clinical data

35. AmazonRedshiftFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonRedshiftFullAccess
    Purpose: Data warehouse for clinical analytics (if needed)

36. AmazonRedshiftReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonRedshiftReadOnlyAccess
    Purpose: Read-only access to Redshift for reporting
```

### **Security & Encryption**
```yaml
37. AWSKeyManagementServicePowerUser
    ARN: arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser
    Purpose: KMS key management, encryption at rest

38. AWSCertificateManagerFullAccess
    ARN: arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess
    Purpose: SSL/TLS certificate management for HTTPS

39. AWSCertificateManagerReadOnly
    ARN: arn:aws:iam::aws:policy/AWSCertificateManagerReadOnly
    Purpose: Read-only access to SSL certificates

40. SecretsManagerReadWrite
    ARN: arn:aws:iam::aws:policy/SecretsManagerReadWrite
    Purpose: Manage application secrets and API keys

41. AWSSecretsManagerReadWrite
    ARN: arn:aws:iam::aws:policy/AWSSecretsManagerReadWrite
    Purpose: Full access to AWS Secrets Manager

42. AWSWAFFullAccess
    ARN: arn:aws:iam::aws:policy/AWSWAFFullAccess
    Purpose: Web Application Firewall for API protection
```

---

## 🔍 **ADVANCED MONITORING POLICIES (4 Optional)**

### **Threat Detection & Security**
```yaml
43. AmazonGuardDutyFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonGuardDutyFullAccess
    Purpose: Threat detection, malicious activity monitoring

44. AmazonGuardDutyReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonGuardDutyReadOnlyAccess
    Purpose: Read-only access to GuardDuty findings

45. AWSSecurityHubFullAccess
    ARN: arn:aws:iam::aws:policy/AWSSecurityHubFullAccess
    Purpose: Centralized security findings, compliance dashboards

46. AWSSecurityHubReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AWSSecurityHubReadOnlyAccess
    Purpose: Read-only access to Security Hub findings

47. AWSCloudTrailFullAccess
    ARN: arn:aws:iam::aws:policy/AWSCloudTrailFullAccess
    Purpose: API call logging, audit trail for compliance

48. AWSCloudTrailReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AWSCloudTrailReadOnlyAccess
    Purpose: Read-only access to CloudTrail logs

49. AmazonInspector2FullAccess
    ARN: arn:aws:iam::aws:policy/AmazonInspector2FullAccess
    Purpose: Vulnerability assessments, security scanning

50. AmazonDetectiveFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonDetectiveFullAccess
    Purpose: Security investigation and forensics
```

### **Performance & Optimization**
```yaml
19. AmazonEC2ReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess
    Purpose: Instance monitoring, resource optimization
```

---

## 🌍 **DOMAIN & DNS POLICIES (2 Optional)**

### **DNS & Domain Management**
```yaml
51. AmazonRoute53FullAccess
    ARN: arn:aws:iam::aws:policy/AmazonRoute53FullAccess
    Purpose: DNS management, custom domain configuration

52. AmazonRoute53ReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonRoute53ReadOnlyAccess
    Purpose: Read-only access to Route53 configurations

53. AmazonRoute53DomainsFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonRoute53DomainsFullAccess
    Purpose: Domain registration and management

54. AmazonRoute53DomainsReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/AmazonRoute53DomainsReadOnlyAccess
    Purpose: Read-only access to registered domains

55. AmazonRoute53ResolverFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonRoute53ResolverFullAccess
    Purpose: DNS resolver configuration for VPCs
```

---

## 🤖 **AI/ML & ANALYTICS POLICIES**

### **Machine Learning Services**
```yaml
56. AmazonSageMakerFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
    Purpose: ML model training and deployment (if needed)

57. AmazonSageMakerReadOnly
    ARN: arn:aws:iam::aws:policy/AmazonSageMakerReadOnly
    Purpose: Read-only access to SageMaker resources

58. AmazonTextractFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonTextractFullAccess
    Purpose: OCR and document analysis for clinical documents

59. AmazonComprehendMedicalFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonComprehendMedicalFullAccess
    Purpose: Medical text analysis and PHI detection

60. AmazonTranscribeFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonTranscribeFullAccess
    Purpose: Speech-to-text for medical dictation

61. AmazonTranscribeMedicalFullAccess
    ARN: arn:aws:iam::aws:policy/AmazonTranscribeMedicalFullAccess
    Purpose: Medical speech recognition and transcription
```

### **Cost & Usage Monitoring**
```yaml
62. AWSBillingReadOnlyAccess
    ARN: arn:aws:iam::aws:policy/job-function/Billing
    Purpose: Cost monitoring, usage analytics

63. AWSSupportAccess
    ARN: arn:aws:iam::aws:policy/AWSSupportAccess
    Purpose: Technical support access, case management

64. AWSBillingConductorFullAccess
    ARN: arn:aws:iam::aws:policy/AWSBillingConductorFullAccess
    Purpose: Billing management and cost allocation

65. AWSCostAndUsageReportAutomationPolicy
    ARN: arn:aws:iam::aws:policy/AWSCostAndUsageReportAutomationPolicy
    Purpose: Automated cost reporting and analysis
```

---

## ⚡ **SERVERLESS & CONTAINER POLICIES**

### **Advanced Container Services**
```yaml
66. AmazonECSTaskExecutionRolePolicy
    ARN: arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    Purpose: ECS task execution permissions

67. AmazonECS_FullAccess
    ARN: arn:aws:iam::aws:policy/AmazonECS_FullAccess
    Purpose: Complete ECS management (alternative name format)

68. AmazonElasticContainerRegistryPublicReadOnly
    ARN: arn:aws:iam::aws:policy/AmazonElasticContainerRegistryPublicReadOnly
    Purpose: Read-only access to public container images

69. AWSBatchServiceRole
    ARN: arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole
    Purpose: Batch job processing for large datasets

70. AmazonEKSClusterPolicy
    ARN: arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
    Purpose: EKS cluster management (if using Kubernetes)

71. AmazonEKSWorkerNodePolicy
    ARN: arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
    Purpose: EKS worker node permissions

72. AmazonEKS_CNI_Policy
    ARN: arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
    Purpose: EKS networking configuration
```

### **Serverless & Lambda**
```yaml
73. AWSLambdaFullAccess
    ARN: arn:aws:iam::aws:policy/AWSLambdaFullAccess
    Purpose: Serverless functions for API processing

74. AWSLambdaExecute
    ARN: arn:aws:iam::aws:policy/AWSLambdaExecute
    Purpose: Basic Lambda execution permissions

75. AWSLambdaRole
    ARN: arn:aws:iam::aws:policy/service-role/AWSLambdaRole
    Purpose: Lambda service role permissions

76. AWSLambdaVPCAccessExecutionRole
    ARN: arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
    Purpose: Lambda VPC access for database connections

77. AmazonAPIGatewayAdministrator
    ARN: arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator
    Purpose: API Gateway management for REST APIs

78. AmazonAPIGatewayPushToCloudWatchLogs
    ARN: arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs
    Purpose: API Gateway logging permissions
```

## 🎯 **ENVIRONMENT-SPECIFIC POLICY SETS**

### **Development Environment (12 Policies)**
```yaml
Required Core:
✅ AmazonECS_FullAccess
✅ AmazonEC2ContainerRegistryFullAccess
✅ AmazonElasticContainerRegistryPublicFullAccess  
✅ AmazonS3FullAccess
✅ AmazonDynamoDBFullAccess
✅ IAMReadOnlyAccess

Recommended Development:
⭐ CloudWatchFullAccess
⭐ AmazonVPCFullAccess
⭐ SecurityAudit
⭐ AmazonRDSFullAccess
⭐ AmazonElastiCacheFullAccess
⭐ AWSLambdaFullAccess
```

### **Staging Environment (18 Policies)**
```yaml
All Development Policies +
✅ CloudWatchLogsFullAccess
✅ AWSConfigServiceRolePolicy
✅ ElasticLoadBalancingFullAccess
✅ AmazonGuardDutyReadOnlyAccess
✅ AWSSecurityHubReadOnlyAccess
✅ AWSCloudTrailReadOnlyAccess
```

### **Production Environment (25+ Policies)**
```yaml
All Staging Policies +
✅ AWSKeyManagementServicePowerUser
✅ AWSCertificateManagerFullAccess
✅ AmazonGuardDutyFullAccess
✅ AWSSecurityHubFullAccess
✅ AWSCloudTrailFullAccess
✅ AmazonInspector2FullAccess
✅ SecretsManagerReadWrite
✅ AWSWAFFullAccess
✅ AmazonDetectiveFullAccess

Optional Production:
⭐ AmazonRoute53FullAccess
⭐ AmazonComprehendMedicalFullAccess
⭐ AmazonTextractFullAccess
⭐ AmazonTranscribeMedicalFullAccess
⭐ AmazonEKSClusterPolicy (if using Kubernetes)
⭐ AWSBillingReadOnlyAccess
```

---

## 🚨 **POLICIES TO AVOID (Security Risk)**

### **Overly Broad Permissions**
```yaml
❌ AdministratorAccess
   ARN: arn:aws:iam::aws:policy/AdministratorAccess
   Risk: Full AWS account access, HIPAA compliance violation

❌ PowerUserAccess  
   ARN: arn:aws:iam::aws:policy/PowerUserAccess
   Risk: Excessive permissions, potential privilege escalation

❌ IAMFullAccess
   ARN: arn:aws:iam::aws:policy/IAMFullAccess
   Risk: Can modify any IAM permissions, security breach risk

❌ ReadOnlyAccess
   ARN: arn:aws:iam::aws:policy/ReadOnlyAccess
   Risk: Too broad for production, potential data exposure
```

---

## 📋 **POLICY ATTACHMENT CHECKLIST**

### **Current Status Check for clinchat-github-actions User:**
```yaml
✅ Currently Attached (from previous setup):
   - AmazonECS_FullAccess
   - AmazonEC2ContainerRegistryFullAccess
   - AmazonS3FullAccess (quarantined - needs new credentials)
   - IAMReadOnlyAccess

❌ Missing Critical Policy:
   - AmazonDynamoDBFullAccess (REQUIRED - add immediately)

⚠️ Recommended Additions:
   - SecurityAudit
   - CloudWatchFullAccess
   - CloudWatchLogsFullAccess
```

---

## 🔧 **QUICK POLICY ATTACHMENT COMMANDS**

### **AWS Console Method:**
```yaml
1. Navigate to: AWS Console → IAM → Users
2. Click: clinchat-github-actions
3. Click: Permissions tab → Add permissions
4. Select: Attach policies directly
5. Search and select policies from the list above
6. Click: Add permissions
```

### **AWS CLI Method:**
```bash
# Set user name variable
USER_NAME="clinchat-github-actions"

# Attach missing DynamoDB policy (CRITICAL)
aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Attach recommended healthcare policies
aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/SecurityAudit

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

# Verify attachment
aws iam list-attached-user-policies --user-name $USER_NAME
```

---

## 🔍 **POLICY VALIDATION SCRIPT**

### **Python Validation Script:**
```python
import boto3
from botocore.exceptions import ClientError

def check_policy_attachments():
    """Check if required policies are attached to the user"""
    
    # Required policies for ClinChat-RAG
    required_policies = [
        'AmazonECS_FullAccess',
        'AmazonEC2ContainerRegistryFullAccess', 
        'AmazonS3FullAccess',
        'AmazonDynamoDBFullAccess',  # Currently missing!
        'IAMReadOnlyAccess'
    ]
    
    # Recommended healthcare policies
    recommended_policies = [
        'SecurityAudit',
        'CloudWatchFullAccess',
        'CloudWatchLogsFullAccess'
    ]
    
    try:
        iam = boto3.client('iam')
        user_name = 'clinchat-github-actions'
        
        # Get attached policies
        response = iam.list_attached_user_policies(UserName=user_name)
        attached_policies = [p['PolicyName'] for p in response['AttachedPolicies']]
        
        print("🔍 POLICY ATTACHMENT VALIDATION")
        print("=" * 40)
        
        # Check required policies
        print("\n✅ REQUIRED POLICIES:")
        missing_required = []
        for policy in required_policies:
            if policy in attached_policies:
                print(f"  ✅ {policy}")
            else:
                print(f"  ❌ {policy} - MISSING!")
                missing_required.append(policy)
        
        # Check recommended policies  
        print("\n⭐ RECOMMENDED POLICIES:")
        missing_recommended = []
        for policy in recommended_policies:
            if policy in attached_policies:
                print(f"  ✅ {policy}")
            else:
                print(f"  ⚠️  {policy} - Not attached")
                missing_recommended.append(policy)
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"  Total Attached: {len(attached_policies)}")
        print(f"  Required Missing: {len(missing_required)}")
        print(f"  Recommended Missing: {len(missing_recommended)}")
        
        if missing_required:
            print(f"\n🚨 ACTION REQUIRED: Attach missing policies immediately!")
            return False
        else:
            print(f"\n✅ All required policies attached!")
            return True
            
    except ClientError as e:
        print(f"❌ Error checking policies: {e}")
        return False

# Run validation
if __name__ == "__main__":
    check_policy_attachments()
```

---

## 📊 **POLICY MAPPING BY SERVICE**

### **Based on Your .env.example Configuration:**

#### **Database Services (PostgreSQL + Redis):**
```yaml
Required:
- AmazonRDSFullAccess (PostgreSQL with pgvector)
- AmazonElastiCacheFullAccess (Redis caching)
- AmazonDynamoDBFullAccess (Session storage, Terraform state)
```

#### **AI/ML Services (Google Gemini + Groq):**
```yaml
Note: External AI services (Google, Groq, OpenAI) don't require AWS policies
AWS Policies Needed:
- AmazonS3FullAccess (Model artifacts, if stored in S3)
- CloudWatchFullAccess (API call monitoring)
```

#### **File Processing (OCR, Document Upload):**
```yaml
Required:
- AmazonS3FullAccess (Document storage)
- AmazonTextractFullAccess (OCR processing, if using AWS Textract)
```

#### **Security & Compliance (HIPAA, Audit):**
```yaml
Required:
- SecurityAudit (HIPAA compliance monitoring)
- CloudWatchLogsFullAccess (7-year audit retention)
- AWSCloudTrailFullAccess (API audit trail)
- AWSConfigServiceRolePolicy (Configuration compliance)
```

#### **Monitoring & Observability (Prometheus, Health Checks):**
```yaml
Required:
- CloudWatchFullAccess (Metrics and monitoring)
- AmazonEC2ReadOnlyAccess (Instance monitoring)
```

---

## 🎯 **IMMEDIATE ACTION PLAN**

### **Step 1: Add Missing Critical Policy (2 minutes)**
```bash
# This is BLOCKING your deployment right now!
Policy to Add: AmazonDynamoDBFullAccess
AWS Console Path: IAM → Users → clinchat-github-actions → Add permissions
```

### **Step 2: Create New AWS Credentials (5 minutes)**
```bash
# Your current S3 access is quarantined
Actions:
1. Remove AWSCompromisedKeyQuarantineV3 policy
2. Create new access key pair
3. Delete old compromised keys (AKIAY24YPLC7UTG7RIU2)
4. Update GitHub secrets with new keys
```

### **Step 3: Add Recommended Healthcare Policies (5 minutes)**
```bash
# For HIPAA compliance and monitoring
Policies to Add:
- SecurityAudit
- CloudWatchFullAccess  
- CloudWatchLogsFullAccess
```

### **Step 4: Deploy and Validate (10 minutes)**
```bash
# Push changes to trigger deployment
git add .
git commit -m "feat: added required AWS policies for production deployment"
git push origin main
```

---

## 📞 **Support Resources**

### **Policy Documentation:**
- [AWS IAM Policy Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)
- [ECS Security Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/security.html)
- [HIPAA Compliance on AWS](https://aws.amazon.com/compliance/hipaa-compliance/)

### **Project-Specific Guides:**
- [`AWS_POLICY_SELECTION_GUIDE.md`](./AWS_POLICY_SELECTION_GUIDE.md) - Detailed policy selection
- [`PERMISSIONS_REQUIREMENTS.md`](./PERMISSIONS_REQUIREMENTS.md) - Complete permissions overview
- [`HIPAA_COMPLIANCE.md`](./docs/medical-compliance/HIPAA_COMPLIANCE.md) - Healthcare compliance

---

**📅 Document Information**
- **Created**: October 21, 2025
- **Version**: 1.0  
- **Purpose**: AWS Policy Names Reference for ClinChat-RAG
- **Next Review**: December 21, 2025
- **Classification**: Internal Use - Technical Reference

**⚠️ Security Note**: This list provides standard AWS managed policy names. Always verify policy permissions match your security requirements before production deployment.