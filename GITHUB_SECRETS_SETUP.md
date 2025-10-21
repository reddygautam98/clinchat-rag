# 🔐 GitHub Actions Secrets Setup Guide
**ClinChat-RAG CI/CD Pipeline Configuration**

## 📋 **Required Secrets Overview**

Your ClinChat-RAG project requires these GitHub secrets for automated CI/CD deployment:

| Secret Name | Purpose | Priority | Example Value |
|-------------|---------|----------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS deployment access | HIGH | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS deployment secret | HIGH | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `TF_STATE_BUCKET` | Terraform state storage | MEDIUM | `clinchat-terraform-state` |
| `SLACK_WEBHOOK` | Build notifications | LOW | `https://hooks.slack.com/services/...` |

---

## 🚀 **Step-by-Step Setup Instructions**

### **Step 1: Access GitHub Repository Settings**

1. **Navigate to your repository**: Go to your ClinChat-RAG GitHub repository
2. **Open Settings**: Click on the "Settings" tab (requires admin access)
3. **Find Secrets**: In the left sidebar, click "Secrets and variables" → "Actions"

### **Step 2: Create AWS Credentials**

#### **Option A: Create New AWS User (Recommended)**
```bash
# 1. Log into AWS Console
# 2. Go to IAM → Users → Create User
# 3. User name: clinchat-github-actions
# 4. Attach policies:
#    - AmazonECS_FullAccess
#    - AmazonEC2ContainerRegistryFullAccess
#    - IAMReadOnlyAccess
# 5. Create access key → Command Line Interface (CLI)
# 6. Save the Access Key ID and Secret Access Key
```

#### **Option B: Use Existing AWS Credentials**
If you already have AWS CLI configured:
```bash
# Check existing credentials
aws configure list

# Get access key (if needed)
aws iam list-access-keys --user-name YOUR_USERNAME
```

### **Step 3: Add Secrets to GitHub**

For each secret, follow these steps:

1. **Click "New repository secret"**
2. **Enter the secret name** (exactly as shown above)
3. **Paste the secret value**
4. **Click "Add secret"**

#### **AWS_ACCESS_KEY_ID**
```
Name: AWS_ACCESS_KEY_ID
Value: AKIAIOSFODNN7EXAMPLE
```

#### **AWS_SECRET_ACCESS_KEY**  
```
Name: AWS_SECRET_ACCESS_KEY
Value: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### **TF_STATE_BUCKET**
```
Name: TF_STATE_BUCKET
Value: clinchat-terraform-state-bucket
```

#### **SLACK_WEBHOOK** (Optional)
```
Name: SLACK_WEBHOOK
Value: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 🏗️ **Terraform State Bucket Setup**

### **Create S3 Bucket for Terraform State**
```bash
# 1. Create S3 bucket
aws s3 mb s3://clinchat-terraform-state-bucket --region us-east-1

# 2. Enable versioning
aws s3api put-bucket-versioning \
  --bucket clinchat-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# 3. Enable encryption
aws s3api put-bucket-encryption \
  --bucket clinchat-terraform-state-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

---

## 💬 **Slack Webhook Setup** (Optional)

### **Create Slack Webhook for Build Notifications**

1. **Go to Slack API**: https://api.slack.com/apps
2. **Create New App**: "From scratch"
3. **App Name**: "ClinChat-RAG CI/CD"
4. **Workspace**: Select your workspace
5. **Incoming Webhooks**: Enable and create webhook
6. **Copy webhook URL**: Use as `SLACK_WEBHOOK` secret

### **Test Slack Integration**
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🚀 ClinChat-RAG deployment test!"}' \
  YOUR_SLACK_WEBHOOK_URL
```

---

## ✅ **Verification Steps**

### **1. Check Secrets are Added**
Go to your repository → Settings → Secrets and variables → Actions

You should see:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY  
- ✅ TF_STATE_BUCKET
- ✅ SLACK_WEBHOOK (optional)

### **2. Test GitHub Actions**
```bash
# Trigger a workflow manually or push a commit
git add .
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

### **3. Monitor Workflow**
1. Go to "Actions" tab in your repository
2. Check the latest workflow run
3. Verify no secret-related errors

---

## 🔒 **Security Best Practices**

### **AWS IAM Policy (Minimal Permissions)**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "iam:PassRole",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::clinchat-terraform-state-bucket",
        "arn:aws:s3:::clinchat-terraform-state-bucket/*"
      ]
    }
  ]
}
```

### **Secret Rotation Schedule**
- **AWS Keys**: Rotate every 90 days
- **Slack Webhook**: Rotate if compromised
- **Terraform State**: Backup regularly

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **AWS Authentication Errors**
```bash
# Check credentials format
echo $AWS_ACCESS_KEY_ID | wc -c  # Should be 20 characters
echo $AWS_SECRET_ACCESS_KEY | wc -c  # Should be 40 characters
```

#### **Terraform State Access**
```bash
# Test S3 bucket access
aws s3 ls s3://clinchat-terraform-state-bucket
```

#### **Slack Webhook Not Working**
- Verify webhook URL format
- Check Slack app permissions
- Test with curl command above

### **GitHub Actions Debugging**
```yaml
# Add to workflow for debugging
- name: Debug Secrets
  run: |
    echo "AWS_ACCESS_KEY_ID length: ${#AWS_ACCESS_KEY_ID}"
    echo "TF_STATE_BUCKET: $TF_STATE_BUCKET"
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    TF_STATE_BUCKET: ${{ secrets.TF_STATE_BUCKET }}
```

---

## 🎯 **Next Steps After Setup**

### **1. Test CI/CD Pipeline**
- Push a small change to trigger workflow
- Monitor deployment process
- Verify successful deployment

### **2. Enable Auto-Deployment**
- Set up branch protection rules
- Configure deployment environments
- Add approval workflows for production

### **3. Monitor and Maintain**
- Set up CloudWatch alerts
- Regular secret rotation
- Monitor deployment metrics

---

## 📞 **Quick Reference Commands**

```bash
# Check AWS credentials
aws sts get-caller-identity

# List S3 buckets
aws s3 ls

# Test Terraform
terraform --version

# Check GitHub CLI
gh auth status
```

---

## 🏆 **Completion Checklist**

- [ ] AWS IAM user created with minimal permissions
- [ ] AWS_ACCESS_KEY_ID secret added to GitHub
- [ ] AWS_SECRET_ACCESS_KEY secret added to GitHub
- [ ] S3 bucket created for Terraform state
- [ ] TF_STATE_BUCKET secret added to GitHub
- [ ] Slack webhook created (optional)
- [ ] SLACK_WEBHOOK secret added to GitHub (optional)
- [ ] Test workflow run successful
- [ ] CI/CD pipeline functional

**Once completed, your ClinChat-RAG system will have full automated deployment capabilities!** 🚀