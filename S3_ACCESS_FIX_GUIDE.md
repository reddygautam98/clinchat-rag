# 🔧 S3 Access Fix Guide
**Resolving S3 AccessDenied Error for ClinChat-RAG**

## 🎯 **Problem Summary**
Your AWS user `clinchat-github-actions` cannot access S3 buckets, showing "AccessDenied" error.

## 🚀 **Solution 1: Add S3 Policy via AWS Console (Recommended)**

### **Step 1: Login to AWS Console**
1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Navigate to **Users** → **clinchat-github-actions**

### **Step 2: Attach S3 Policy**
1. Click on **Permissions** tab
2. Click **Add permissions** → **Attach policies directly**
3. Search and select **one of these policies**:

#### **Option A: Full S3 Access (Easiest)**
- Policy Name: `AmazonS3FullAccess`
- ✅ Pros: Complete S3 access
- ⚠️ Cons: Broad permissions

#### **Option B: Custom S3 Policy (Recommended)**
- Click **Create policy** → **JSON** tab
- Paste this custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ClinChatS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:CreateBucket"
            ],
            "Resource": [
                "arn:aws:s3:::clinchat-*",
                "arn:aws:s3:::clinchat-*/*",
                "arn:aws:s3:::*terraform-state*",
                "arn:aws:s3:::*terraform-state*/*"
            ]
        },
        {
            "Sid": "ClinChatS3List",
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation"
            ],
            "Resource": "*"
        }
    ]
}
```

### **Step 3: Save and Name Policy**
- Policy name: `ClinChat-S3-Access`
- Description: `S3 access for ClinChat-RAG deployment`
- Click **Create policy**

### **Step 4: Attach to User**
- Go back to user **clinchat-github-actions**
- **Add permissions** → **Attach policies directly**
- Search for `ClinChat-S3-Access`
- Select and **Add permissions**

---

## 🚀 **Solution 2: AWS CLI Method (If you have admin access)**

### **Step 1: Create Policy File**
```bash
# Create policy file
cat > clinchat-s3-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:CreateBucket",
                "s3:ListAllMyBuckets"
            ],
            "Resource": [
                "arn:aws:s3:::clinchat-*",
                "arn:aws:s3:::clinchat-*/*",
                "arn:aws:s3:::*terraform-state*",
                "arn:aws:s3:::*terraform-state*/*",
                "*"
            ]
        }
    ]
}
EOF
```

### **Step 2: Create and Attach Policy**
```bash
# Create policy
aws iam create-policy \
  --policy-name ClinChat-S3-Access \
  --policy-document file://clinchat-s3-policy.json

# Get policy ARN (replace ACCOUNT-ID with your account: 607520774335)
POLICY_ARN="arn:aws:iam::607520774335:policy/ClinChat-S3-Access"

# Attach policy to user
aws iam attach-user-policy \
  --user-name clinchat-github-actions \
  --policy-arn $POLICY_ARN
```

---

## 🚀 **Solution 3: Quick Fix - Attach AWS Managed Policy**

If you need immediate access, attach AWS managed S3 policy:

```bash
# Attach AWS managed S3 read/write policy
aws iam attach-user-policy \
  --user-name clinchat-github-actions \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

---

## ✅ **Verification Steps**

After applying any solution above, test S3 access:

### **Method 1: Test with AWS CLI**
```bash
# Test bucket listing
aws s3 ls

# Test bucket creation
aws s3 mb s3://clinchat-terraform-state-test

# Test file upload
echo "test" > test.txt
aws s3 cp test.txt s3://clinchat-terraform-state-test/
aws s3 rm s3://clinchat-terraform-state-test/test.txt
```

### **Method 2: Test with Python Script**
I can create a test script to verify S3 access after you apply the fix.

---

## 🎯 **What Each Solution Gives You**

| Solution | Scope | Security | Ease |
|----------|--------|----------|------|
| **Custom Policy** | ClinChat buckets only | ✅ Secure | ⭐⭐⭐ |
| **Full S3 Access** | All S3 buckets | ⚠️ Broad | ⭐⭐⭐⭐⭐ |
| **CLI Method** | Programmable | ✅ Configurable | ⭐⭐ |

---

## 🔒 **Recommended Approach**

1. **Use Solution 1, Option B** (Custom Policy) for production
2. **Use Solution 3** (Full Access) for quick testing
3. **Test verification** after applying changes

---

## 📞 **Need Help?**

If you encounter issues:
1. Check your AWS account permissions
2. Verify the user name is exactly `clinchat-github-actions`
3. Wait 2-3 minutes for IAM changes to propagate
4. Run verification tests

---

## 🎉 **After Fix Benefits**

Once S3 access is working:
- ✅ Terraform state storage
- ✅ Application artifact storage  
- ✅ Backup and logging capabilities
- ✅ Full CI/CD pipeline functionality