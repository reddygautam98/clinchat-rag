# 🔐 ClinChat-RAG Project - Complete Permissions Requirements

## 📋 Overview

This document outlines **ALL** permissions required to deploy, operate, and maintain the ClinChat-RAG medical AI system across different environments and use cases.

---

## 🏗️ **AWS Infrastructure Permissions**

### **Core AWS IAM Policies Required**

#### **1. Amazon ECS Full Access** 🔄
```json
{
  "PolicyName": "AmazonECS_FullAccess",
  "Purpose": "Container orchestration and service management",
  "Resources": [
    "ecs:*",
    "application-autoscaling:*",
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ]
}
```

#### **2. Amazon ECR Full Access** 📦
```json
{
  "PolicyName": "AmazonEC2ContainerRegistryFullAccess", 
  "Purpose": "Docker image storage and management",
  "Resources": [
    "ecr:*",
    "ecr-public:*"
  ]
}
```

#### **3. Amazon S3 Full Access** 🗂️
```json
{
  "PolicyName": "AmazonS3FullAccess",
  "Purpose": "Terraform state storage and document uploads",
  "Resources": [
    "s3:*",
    "s3-object-lambda:*"
  ]
}
```

#### **4. DynamoDB Full Access** 🔒
```json
{
  "PolicyName": "AmazonDynamoDBFullAccess",
  "Purpose": "Terraform state locking and application data",
  "Resources": [
    "dynamodb:*",
    "dax:*",
    "application-autoscaling:DeleteScalingPolicy",
    "application-autoscaling:DeregisterScalableTarget"
  ]
}
```

#### **5. IAM Read Only Access** 👥
```json
{
  "PolicyName": "IAMReadOnlyAccess",
  "Purpose": "User and role management verification",
  "Resources": [
    "iam:Get*",
    "iam:List*",
    "iam:GenerateCredentialReport",
    "iam:GenerateServiceLastAccessedDetails",
    "iam:SimulateCustomPolicy",
    "iam:SimulatePrincipalPolicy"
  ]
}
```

### **Additional AWS Permissions for Full Deployment**

#### **6. Application Load Balancer Management** ⚖️
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:*",
        "ec2:CreateVpc",
        "ec2:CreateSubnet",
        "ec2:CreateInternetGateway",
        "ec2:CreateRouteTable",
        "ec2:CreateRoute",
        "ec2:CreateSecurityGroup",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeAvailabilityZones",
        "ec2:AttachInternetGateway",
        "ec2:AssociateRouteTable"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **7. CloudWatch Logging and Monitoring** 📊
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **8. Route53 DNS Management** 🌐 *(Optional)*
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:*",
        "route53domains:*",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🔐 **GitHub Actions Secrets Configuration**

### **Required GitHub Repository Secrets**

```yaml
# AWS Authentication
AWS_ACCESS_KEY_ID: "AKIAY24YPLC7UTG7RIU2"
AWS_SECRET_ACCESS_KEY: "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"
AWS_DEFAULT_REGION: "us-east-1"

# Terraform Configuration  
TF_STATE_BUCKET: "clinchat-terraform-state-bucket"

# Optional: Environment-specific secrets
ENVIRONMENT: "staging"  # or "production"
```

### **GitHub Repository Permissions**
- **Actions**: Read and write permissions
- **Contents**: Read and write permissions  
- **Metadata**: Read permissions
- **Secrets**: Write permissions (for admin users)
- **Packages**: Write permissions (for Docker images)

---

## 🏥 **Medical/Healthcare Compliance Permissions**

### **HIPAA Compliance Requirements**

#### **Administrative Safeguards**
```yaml
Required_Roles:
  - HIPAA_Security_Officer: "Assigned and trained"
  - Privacy_Officer: "PHI handling oversight" 
  - Compliance_Team: "Regular audits and assessments"
  - System_Administrator: "Technical security implementation"

Access_Management:
  - Role_Based_Access_Control: "RBAC implemented"
  - Principle_of_Least_Privilege: "Minimum necessary access"
  - Regular_Access_Reviews: "Quarterly assessments"
  - Automatic_Revocation: "Inactive user management"
```

#### **Physical Safeguards**
```yaml
Data_Protection:
  - Encryption_At_Rest: "AES-256 encryption"
  - Encryption_In_Transit: "TLS 1.3 minimum"
  - Secure_Cloud_Storage: "AWS with access controls"
  - No_Local_PHI_Storage: "Endpoints secured"

Facility_Controls:
  - Data_Center_Security: "AWS facility compliance"
  - Access_Controls: "Multi-factor authentication"
  - Workstation_Restrictions: "Authorized access only"
```

#### **Technical Safeguards**
```yaml
Authentication_Authorization:
  - Multi_Factor_Authentication: "Required for PHI access"
  - Session_Management: "Timeout and secure sessions"
  - User_Authentication: "Strong password policies"

Audit_Controls:
  - Comprehensive_Logging: "All PHI access logged"
  - Real_Time_Monitoring: "Suspicious activity detection"
  - Audit_Reports: "Regular compliance reporting"
  - Log_Retention: "7+ years for medical compliance"

Data_Integrity:
  - PHI_Protection: "Real-time scanning and masking"
  - Backup_Verification: "Regular backup testing"
  - Recovery_Procedures: "Documented and tested"
```

### **Business Associate Agreements (BAAs)**
```yaml
Required_BAAs:
  - AWS: "HIPAA BAA executed"
  - Google_Cloud: "For Gemini AI services (if used)"
  - Third_Party_Vendors: "All services handling PHI"
  
BAA_Requirements:
  - Permitted_Uses: "Clinical decision support only"
  - Prohibited_Uses: "No marketing or re-identification"
  - Safeguards: "Administrative, physical, technical"
  - Breach_Notification: "Within 60 days"
```

---

## 🤖 **AI/ML Service Permissions**

### **Google Gemini AI** (Primary LLM)
```yaml
API_Access:
  - Service: "Google AI Studio / Vertex AI"
  - API_Key: "AIzaSyDud_JXcH9wHEhCixMfqcloQ1kench84Bg"
  - Model_Access: "gemini-2.0-flash"
  - Embedding_Model: "text-embedding-004"
  - Rate_Limits: "Standard tier limits"
  
Compliance:
  - Data_Processing: "BAA required for PHI"
  - Data_Location: "US-based processing preferred" 
  - Audit_Logging: "All API calls logged"
```

### **Groq Cloud** (High-Speed Inference)
```yaml
API_Access:
  - Service: "Groq Cloud Platform"
  - API_Key: "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"
  - Model_Access: "llama-3.1-8b-instant"
  - Performance: "Ultra-fast inference speeds"
  
Security:
  - PHI_Masking: "Required before API calls"
  - No_Data_Retention: "Groq policy compliance"
  - Audit_Trail: "All requests logged"
```

### **OpenAI** (Optional/Fallback)
```yaml
API_Access:
  - Service: "OpenAI API or Azure OpenAI"
  - Model_Access: "gpt-4-1106-preview"
  - Embedding_Model: "text-embedding-ada-002"
  
HIPAA_Compliance:
  - Azure_OpenAI_Required: "For HIPAA compliance"
  - BAA_Available: "Azure OpenAI BAA execution"
  - PHI_Protection: "Pre-processing required"
```

---

## 💾 **Database and Storage Permissions**

### **PostgreSQL with pgvector** 
```yaml
Database_Permissions:
  - CREATE: "Database and schema creation"
  - ALTER: "Schema modifications"
  - SELECT: "Data querying"  
  - INSERT: "Data ingestion"
  - UPDATE: "Data modifications"
  - DELETE: "Data cleanup"
  - CONNECT: "Database connections"

Vector_Extensions:
  - pgvector: "Vector similarity search"
  - pg_trgm: "Text similarity"
  - uuid_ossp: "UUID generation"
```

### **Redis Cache**
```yaml
Redis_Permissions:
  - READ: "Cache retrieval"
  - WRITE: "Cache storage" 
  - DELETE: "Cache invalidation"
  - ADMIN: "Configuration management"
  
Connection_Security:
  - Authentication: "Password protected"
  - TLS_Encryption: "In-transit security"
  - Network_Isolation: "VPC deployment"
```

### **Vector Store Options**
```yaml
Chroma_DB:
  - Local_Deployment: "Self-hosted option"
  - File_System_Access: "Persistent storage"
  - HTTP_API_Access: "RESTful interface"

Pinecone:
  - API_Access: "Managed vector database"
  - Index_Management: "Vector index operations"
  - Query_Permissions: "Similarity search"

Weaviate:
  - GraphQL_Access: "Query interface"
  - Schema_Management: "Vector schema definition"
  - Batch_Operations: "Bulk data ingestion"
```

---

## 🛡️ **Security and Monitoring Permissions**

### **AWS Security Services**
```yaml
GuardDuty:
  - Threat_Detection: "Malicious activity monitoring"
  - Finding_Management: "Security event handling"
  - Service_Management: "Enable/disable controls"

Security_Hub:
  - Compliance_Monitoring: "Multi-standard compliance"
  - Finding_Aggregation: "Centralized security view"
  - Custom_Insights: "Security metric creation"

AWS_Config:
  - Configuration_Monitoring: "Resource compliance tracking"
  - Rule_Management: "Compliance rule definition"
  - Remediation: "Automatic compliance fixes"
```

### **Network Security**
```yaml
VPC_Permissions:
  - VPC_Creation: "Network isolation"
  - Subnet_Management: "Network segmentation"
  - Security_Groups: "Firewall rule management"
  - NACLs: "Network access control"

SSL_TLS:
  - Certificate_Management: "AWS Certificate Manager"
  - Load_Balancer_SSL: "HTTPS termination"
  - Internal_Encryption: "Service-to-service TLS"
```

---

## 📊 **Monitoring and Observability Permissions**

### **CloudWatch**
```yaml
Metrics:
  - Custom_Metrics: "Application performance tracking"
  - Alarms: "Threshold-based alerting"  
  - Dashboards: "Visual monitoring"

Logs:
  - Log_Groups: "Service log aggregation"
  - Log_Streams: "Real-time log viewing"
  - Log_Insights: "Advanced log querying"
```

### **Application Monitoring**
```yaml
Health_Checks:
  - Endpoint_Monitoring: "Service availability"
  - Database_Health: "Connection monitoring"
  - AI_Service_Health: "API availability monitoring"

Performance_Monitoring:
  - Response_Time: "Latency tracking"
  - Throughput: "Request volume monitoring"
  - Error_Rates: "Failure rate tracking"
```

---

## 🔧 **Development and CI/CD Permissions**

### **Local Development**
```yaml
Required_Tools:
  - Docker: "Container runtime permissions"
  - Docker_Compose: "Multi-service orchestration"
  - Git: "Version control access"
  - Python_Virtual_Env: "Dependency isolation"

File_System_Access:
  - Project_Directory: "Read/write access"
  - Docker_Volume_Mounts: "Container data persistence"
  - Log_Directory: "Application logging"
  - Config_Files: "Environment configuration"
```

### **CI/CD Pipeline**
```yaml
GitHub_Actions:
  - Workflow_Execution: "Automated deployment"
  - Secret_Access: "Secure credential handling"
  - Artifact_Storage: "Build artifact management"
  - Environment_Deployment: "Multi-stage deployment"

Docker_Registry:
  - Image_Push: "Container image publishing"
  - Image_Pull: "Container image deployment"
  - Tag_Management: "Version control"
  - Security_Scanning: "Vulnerability assessment"
```

---

## 📋 **Environment-Specific Permissions**

### **Development Environment**
```yaml
Relaxed_Permissions:
  - Debug_Access: "Full application debugging"
  - Log_Level_Control: "Verbose logging enabled"
  - Hot_Reloading: "Development productivity features"
  - Test_Data_Access: "Synthetic data for testing"
```

### **Staging Environment**
```yaml
Production_Like_Security:
  - Limited_Debug_Access: "Restricted debugging"
  - Audit_Logging: "Full compliance logging"
  - Performance_Testing: "Load testing capabilities"
  - Security_Scanning: "Automated vulnerability scans"
```

### **Production Environment**
```yaml
Maximum_Security:
  - No_Debug_Access: "Debug features disabled"
  - Full_Audit_Logging: "Complete activity tracking"
  - Encrypted_Communication: "All traffic encrypted"
  - Real_PHI_Protection: "Full HIPAA compliance"
  - Backup_Permissions: "Automated backup systems"
  - Monitoring_Access: "24/7 system monitoring"
```

---

## 🚨 **Emergency and Incident Response Permissions**

### **Incident Response Team**
```yaml
Emergency_Access:
  - System_Override: "Critical system access"
  - Log_Analysis: "Forensic investigation capabilities"
  - Service_Restart: "Emergency service recovery"
  - Communication_Tools: "Incident notification systems"

Breach_Response:
  - Data_Isolation: "Contaminated data quarantine"
  - Audit_Trail_Preservation: "Evidence collection"
  - Regulatory_Reporting: "Compliance notification"
  - Recovery_Operations: "System restoration"
```

---

## 🔍 **Audit and Compliance Permissions**

### **Internal Audit Team**
```yaml
Read_Only_Access:
  - System_Logs: "Complete audit trail access"
  - Configuration_Review: "Security setting verification"
  - User_Activity: "Access pattern analysis"
  - Compliance_Reports: "Automated compliance checking"

Documentation_Access:
  - Policy_Documents: "Procedure verification"
  - Training_Records: "Staff compliance verification"
  - Incident_Reports: "Historical issue analysis"
```

### **External Auditors**
```yaml
Controlled_Access:
  - Guided_System_Tours: "Supervised system access"
  - Anonymized_Data_Samples: "De-identified data review"
  - Policy_Documentation: "Compliance framework review"
  - Interview_Access: "Staff compliance verification"
```

---

## ✅ **Permission Validation Checklist**

### **Pre-Deployment Validation**
- [ ] All AWS IAM policies attached and verified
- [ ] GitHub secrets configured and tested
- [ ] HIPAA compliance documentation complete
- [ ] BAAs executed with all third-party services
- [ ] Security controls tested and operational
- [ ] Audit logging enabled and functional
- [ ] Backup and recovery procedures tested
- [ ] Incident response plan documented and rehearsed

### **Post-Deployment Validation**
- [ ] All services accessible with granted permissions
- [ ] No permission-related errors in logs
- [ ] Security monitoring active and alerting
- [ ] Compliance reports generating successfully
- [ ] Backup systems operational
- [ ] Performance monitoring functional

---

## 📞 **Support and Escalation**

### **Permission Issues Contact**
- **AWS Support**: For AWS-related permission problems
- **GitHub Support**: For repository and Actions issues  
- **HIPAA Officer**: For compliance-related concerns
- **System Administrator**: For technical access issues
- **Security Team**: For security policy violations

### **Emergency Contacts**
- **On-Call Engineer**: 24/7 technical support
- **Compliance Officer**: HIPAA breach notification
- **Legal Team**: Regulatory compliance issues
- **Executive Team**: Critical system failures

---

**📅 Document Information**
- **Created**: October 21, 2025
- **Version**: 1.0
- **Next Review**: January 21, 2026
- **Owner**: ClinChat-RAG Project Team
- **Classification**: Internal Use - Security Sensitive

**⚠️ Important Note**: This document contains sensitive security information. Access should be restricted to authorized personnel only. Regular review and updates are required to maintain security posture and compliance standards.