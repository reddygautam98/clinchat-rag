# 🔐 AWS Policy Selection Guide for ClinChat-RAG

## 📋 Overview

This guide helps you select the **exact AWS IAM policies** needed for your ClinChat-RAG medical AI system from the 1,392+ available AWS managed policies. We'll focus on the **minimum required permissions** while ensuring **HIPAA compliance** and **production readiness**.

---

## 🎯 **REQUIRED POLICIES (Must Have)**

### **1. Container Services** 🐳

#### **AmazonECS_FullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/AmazonECS_FullAccess
Purpose: Complete ECS cluster and service management
Why Required: 
  - Deploy containerized ClinChat-RAG application
  - Manage ECS tasks, services, and clusters
  - Auto-scaling and load balancing
  - Service discovery and networking
```

#### **AmazonEC2ContainerRegistryFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
Purpose: Docker image repository management
Why Required:
  - Store and retrieve Docker images
  - Push new application versions
  - Manage image lifecycle and security scanning
  - Private repository for healthcare applications
```

### **2. Storage & State Management** 💾

#### **AmazonS3FullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/AmazonS3FullAccess
Purpose: Object storage and Terraform state management
Why Required:
  - Store Terraform state files securely
  - Document upload and processing storage
  - Application configuration and backup storage
  - Encrypted storage for PHI-adjacent data
```

#### **AmazonDynamoDBFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess  
Purpose: NoSQL database and state locking
Why Required:
  - Terraform state locking (prevents concurrent modifications)
  - Application session storage
  - User preference and audit data
  - High-performance medical data queries
```

### **3. Identity & Access Management** 👥

#### **IAMReadOnlyAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/IAMReadOnlyAccess
Purpose: User and role verification (read-only)
Why Required:
  - Validate deployment user permissions
  - Check service role configurations
  - Audit access patterns for compliance
  - Troubleshoot authentication issues
```

---

## 🏥 **HEALTHCARE-SPECIFIC POLICIES (Recommended)**

### **Security & Compliance**

#### **SecurityAudit**
```yaml
Policy ARN: arn:aws:iam::aws:policy/SecurityAudit
Purpose: Security posture assessment and compliance
Healthcare Value:
  - HIPAA compliance monitoring
  - Security configuration validation
  - Risk assessment capabilities
  - Audit trail verification
```

#### **AWSConfigRole**
```yaml
Policy ARN: arn:aws:iam::aws:policy/service-role/ConfigRole
Purpose: Configuration compliance monitoring
Healthcare Value:
  - Track resource configuration changes
  - Ensure encryption compliance
  - Monitor network security settings
  - Automated compliance reporting
```

### **Monitoring & Logging**

#### **CloudWatchFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/CloudWatchFullAccess
Purpose: Comprehensive monitoring and alerting
Healthcare Value:
  - PHI access monitoring
  - Performance metrics tracking
  - Security event alerting
  - Audit log management
```

#### **CloudWatchLogsFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/logs:*
Purpose: Centralized logging management
Healthcare Value:
  - Audit trail maintenance
  - Security incident investigation
  - Compliance log retention
  - Real-time monitoring
```

---

## 🔧 **INFRASTRUCTURE POLICIES (Optional but Useful)**

### **Networking & Security**

#### **AmazonVPCFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/AmazonVPCFullAccess
Purpose: Network isolation and security
Use Case:
  - Private network setup for PHI handling
  - Security group management
  - Network access control lists
  - VPC endpoint configuration
```

#### **ElasticLoadBalancingFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
Purpose: Load balancer management for high availability
Use Case:
  - Application Load Balancer setup
  - SSL/TLS termination
  - Health check configuration
  - Traffic distribution
```

### **Database Services**

#### **AmazonRDSFullAccess**
```yaml
Policy ARN: arn:aws:iam::aws:policy/AmazonRDSFullAccess
Purpose: Managed database services
Use Case:
  - PostgreSQL with pgvector setup
  - Automated backups and encryption
  - Multi-AZ deployment for HA
  - Performance monitoring
```

---

## 🚫 **POLICIES TO AVOID**

### **Overly Broad Permissions**

#### **AdministratorAccess**
```yaml
❌ AVOID: arn:aws:iam::aws:policy/AdministratorAccess
Why Dangerous:
  - Violates principle of least privilege
  - HIPAA compliance risk
  - Security audit failures
  - Regulatory violations
```

#### **PowerUserAccess**
```yaml
❌ AVOID: arn:aws:iam::aws:policy/PowerUserAccess
Why Dangerous:
  - Excessive IAM permissions
  - Potential for privilege escalation
  - Compliance audit issues
```

### **Unnecessary Services**

```yaml
❌ AVOID These Unless Specifically Needed:
  - AmazonWorkSpacesAdmin
  - AmazonSageMakerFullAccess (unless using ML training)
  - AmazonRedshiftFullAccess (unless using data warehouse)
  - AmazonLexFullAccess (unless building chatbots)
  - GameLiftFullAccess (gaming-specific)
```

---

## 🎯 **POLICY SELECTION BY ENVIRONMENT**

### **Development Environment**
```yaml
Core Policies (5):
  ✅ AmazonECS_FullAccess
  ✅ AmazonEC2ContainerRegistryFullAccess
  ✅ AmazonS3FullAccess
  ✅ AmazonDynamoDBFullAccess
  ✅ IAMReadOnlyAccess

Optional Policies (3):
  ⭐ CloudWatchFullAccess
  ⭐ AmazonVPCFullAccess
  ⭐ SecurityAudit
```

### **Staging Environment**
```yaml
Core Policies (5):
  ✅ AmazonECS_FullAccess
  ✅ AmazonEC2ContainerRegistryFullAccess
  ✅ AmazonS3FullAccess
  ✅ AmazonDynamoDBFullAccess
  ✅ IAMReadOnlyAccess

Healthcare Policies (4):
  ✅ SecurityAudit
  ✅ AWSConfigRole
  ✅ CloudWatchFullAccess
  ✅ CloudWatchLogsFullAccess

Infrastructure Policies (2):
  ✅ AmazonVPCFullAccess
  ✅ ElasticLoadBalancingFullAccess
```

### **Production Environment**
```yaml
All Required Policies (11):
  ✅ AmazonECS_FullAccess
  ✅ AmazonEC2ContainerRegistryFullAccess
  ✅ AmazonS3FullAccess
  ✅ AmazonDynamoDBFullAccess
  ✅ IAMReadOnlyAccess
  ✅ SecurityAudit
  ✅ AWSConfigRole
  ✅ CloudWatchFullAccess
  ✅ CloudWatchLogsFullAccess
  ✅ AmazonVPCFullAccess
  ✅ ElasticLoadBalancingFullAccess

Additional Production Policies:
  ✅ AmazonRDSFullAccess (if using RDS)
  ✅ AWSKeyManagementServicePowerUser (KMS encryption)
  ✅ AmazonRoute53FullAccess (if using custom domains)
```

---

## 📊 **POLICY ATTACHMENT PRIORITY**

### **Phase 1: Core Infrastructure (Deploy First)**
```bash
1. AmazonECS_FullAccess                    # Container orchestration
2. AmazonEC2ContainerRegistryFullAccess    # Docker images
3. AmazonS3FullAccess                      # State storage
4. AmazonDynamoDBFullAccess               # State locking
5. IAMReadOnlyAccess                       # Permission validation
```

### **Phase 2: Healthcare Compliance (Deploy Second)**
```bash
6. SecurityAudit                           # Security monitoring
7. CloudWatchFullAccess                    # Monitoring & metrics
8. CloudWatchLogsFullAccess               # Audit logging
9. AWSConfigRole                          # Compliance tracking
```

### **Phase 3: Advanced Infrastructure (Deploy Last)**
```bash
10. AmazonVPCFullAccess                    # Network isolation
11. ElasticLoadBalancingFullAccess         # Load balancing
12. AmazonRDSFullAccess                    # Managed database
```

---

## 🔍 **POLICY VALIDATION COMMANDS**

### **Check Current User Policies**
```bash
# List attached policies
aws iam list-attached-user-policies --user-name clinchat-github-actions

# Get policy details
aws iam get-policy --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

# Simulate policy permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::607520774335:user/clinchat-github-actions \
  --action-names ecs:CreateCluster \
  --resource-arns "*"
```

### **Validate Minimum Required Access**
```python
# Python script to validate core permissions
import boto3

def validate_required_policies():
    iam = boto3.client('iam')
    user_name = 'clinchat-github-actions'
    
    required_policies = [
        'AmazonECS_FullAccess',
        'AmazonEC2ContainerRegistryFullAccess', 
        'AmazonS3FullAccess',
        'AmazonDynamoDBFullAccess',
        'IAMReadOnlyAccess'
    ]
    
    # Get user's attached policies
    response = iam.list_attached_user_policies(UserName=user_name)
    attached_policies = [p['PolicyName'] for p in response['AttachedPolicies']]
    
    # Check coverage
    missing_policies = []
    for policy in required_policies:
        if policy not in attached_policies:
            missing_policies.append(policy)
    
    if missing_policies:
        print(f"❌ Missing required policies: {missing_policies}")
        return False
    else:
        print("✅ All required policies attached!")
        return True

# Run validation
validate_required_policies()
```

---

## 🚨 **COMMON POLICY SELECTION MISTAKES**

### **1. Over-Permissioning**
```yaml
❌ Wrong Approach:
  - Attaching AdministratorAccess "to make things work"
  - Using PowerUserAccess for simplicity
  - Granting broad permissions without review

✅ Correct Approach:
  - Start with minimum required policies
  - Add permissions incrementally as needed
  - Regular access reviews and cleanups
```

### **2. Missing Healthcare-Specific Policies**
```yaml
❌ Wrong Approach:
  - Only core infrastructure policies
  - No security monitoring policies
  - Missing compliance audit policies

✅ Correct Approach:
  - Include SecurityAudit for HIPAA compliance
  - Add CloudWatch for monitoring
  - Enable AWS Config for compliance tracking
```

### **3. Development vs Production Confusion**
```yaml
❌ Wrong Approach:
  - Same policies across all environments
  - No environment-specific restrictions
  - Debug permissions in production

✅ Correct Approach:
  - Environment-appropriate policy sets
  - Stricter policies in production
  - Clear separation of concerns
```

---

## 📋 **POLICY SELECTION CHECKLIST**

### **Pre-Selection Validation**
- [ ] Identified specific AWS services your application uses
- [ ] Determined environment (dev/staging/production)
- [ ] Reviewed HIPAA compliance requirements
- [ ] Confirmed minimum viable permissions approach

### **Policy Selection Process**
- [ ] Selected core infrastructure policies (5 required)
- [ ] Added healthcare-specific policies for compliance
- [ ] Included monitoring and logging policies
- [ ] Avoided overly broad administrative policies
- [ ] Validated against principle of least privilege

### **Post-Selection Testing**
- [ ] Tested infrastructure deployment with selected policies
- [ ] Verified application can access required services
- [ ] Confirmed monitoring and logging work correctly
- [ ] Validated compliance audit capabilities
- [ ] Documented policy selection rationale

---

## 🎯 **QUICK POLICY SETUP COMMANDS**

### **Attach Required Policies (AWS CLI)**
```bash
# Set variables
USER_NAME="clinchat-github-actions"
ACCOUNT_ID="607520774335"

# Attach core policies
aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-user-policy \
  --user-name $USER_NAME \
  --policy-arn arn:aws:iam::aws:policy/IAMReadOnlyAccess

echo "✅ Core policies attached successfully!"
```

### **Verify Policy Attachment**
```bash
# List all attached policies
aws iam list-attached-user-policies --user-name $USER_NAME

# Expected output should show 5+ policies
echo "✅ Policy verification complete!"
```

---

## 📊 **POLICY COST IMPLICATIONS**

### **Free Tier Compatible Policies**
```yaml
No Additional Costs:
  ✅ IAM policies (free)
  ✅ CloudWatch basic monitoring (free tier)
  ✅ S3 storage (free tier: 5GB)
  ✅ DynamoDB (free tier: 25GB)

Potential Costs:
  💰 ECS tasks (EC2 or Fargate compute)
  💰 Load Balancer ($18/month minimum)
  💰 RDS instances ($15+/month)
  💰 VPC NAT Gateway ($45/month)
```

### **Cost Optimization Tips**
```yaml
Development:
  - Use Fargate Spot for cost savings
  - Single-AZ deployments
  - Smaller instance sizes
  - Scheduled scaling

Production:  
  - Reserved instances for predictable workloads
  - Multi-AZ for high availability
  - Auto-scaling for efficiency
  - CloudWatch cost monitoring
```

---

## 🔗 **RELATED RESOURCES**

### **AWS Documentation**
- [IAM Policy Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)
- [ECS Security Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/security.html)
- [HIPAA on AWS](https://aws.amazon.com/compliance/hipaa-compliance/)

### **ClinChat-RAG Project Files**
- [`PERMISSIONS_REQUIREMENTS.md`](./PERMISSIONS_REQUIREMENTS.md) - Complete permissions overview
- [`infrastructure/main.tf`](./infrastructure/main.tf) - Terraform infrastructure code
- [`HIPAA_COMPLIANCE.md`](./docs/medical-compliance/HIPAA_COMPLIANCE.md) - Healthcare compliance guide

---

## 📞 **Support & Troubleshooting**

### **Common Issues**
1. **Policy Not Found**: Ensure policy ARN is correct for your AWS region
2. **Access Denied**: Check policy attachment and propagation (may take 2-3 minutes)
3. **Compliance Failures**: Verify healthcare-specific policies are attached
4. **Cost Overruns**: Review resource usage and optimize instance types

### **Getting Help**
- **AWS Support**: For policy-specific questions
- **GitHub Issues**: For project-specific problems
- **HIPAA Compliance**: Consult with healthcare compliance experts
- **Security Review**: Engage AWS security consultants for production deployments

---

**📅 Document Information**
- **Created**: October 21, 2025
- **Version**: 1.0
- **Next Review**: December 21, 2025
- **Owner**: ClinChat-RAG Development Team
- **Classification**: Internal Use - Technical Documentation

**⚠️ Security Note**: This guide provides policy recommendations based on common use cases. Always perform a security review and compliance assessment before production deployment in healthcare environments.