# 🔧 DynamoDB Permission Fix Required

## 🚨 **Issue Identified:**
Your AWS user `clinchat-github-actions` lacks DynamoDB permissions needed for Terraform state locking.

## ❌ **Current Error:**
```
AccessDeniedException: User is not authorized to perform: dynamodb:ListTables
```

## 🎯 **Required Fix:**

### **Option 1: Add DynamoDB Policy (Recommended)**

**Go to AWS Console:**
1. Navigate: https://console.aws.amazon.com/iam/
2. Click: **Users** → **clinchat-github-actions**
3. Click: **Permissions** → **Add permissions** → **Attach policies directly**
4. Search: `AmazonDynamoDBFullAccess`
5. Select and **Add permissions**

### **Option 2: Create Custom Policy (More Secure)**

**Create custom policy with minimal permissions:**

1. **IAM Console** → **Policies** → **Create policy**
2. **JSON tab** and paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:DeleteTable",
                "dynamodb:DescribeTable",
                "dynamodb:ListTables",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:UpdateItem",
                "dynamodb:CreateGlobalTable",
                "dynamodb:ListTagsOfResource",
                "dynamodb:TagResource"
            ],
            "Resource": [
                "arn:aws:dynamodb:us-east-1:607520774335:table/terraform-state-lock*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:ListTables"
            ],
            "Resource": "*"
        }
    ]
}
```

3. **Policy name**: `ClinChat-DynamoDB-TerraformLock`
4. **Attach** to `clinchat-github-actions` user

## ⚡ **Quick AWS CLI Fix (If you have admin access):**

```bash
# Attach AWS managed policy
aws iam attach-user-policy \
  --user-name clinchat-github-actions \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Verify attachment
aws iam list-attached-user-policies --user-name clinchat-github-actions
```

## ✅ **Current Status:**
- ✅ **S3 Bucket**: `clinchat-terraform-state-bucket` (working)
- ❌ **DynamoDB Table**: Permissions needed
- ⚠️ **S3 Versioning**: Disabled (recommend enabling)

## 🎯 **After Adding DynamoDB Permissions:**

Run the check script again:
```bash
python check_terraform_backend.py
```

**Expected result:**
```
✅ DynamoDB State Locking: READY
✅ S3 State Storage: READY
🎉 Terraform backend fully configured!
```

## 📊 **Updated AWS Policies Needed:**
1. ✅ AmazonECS_FullAccess
2. ✅ AmazonEC2ContainerRegistryFullAccess
3. ✅ IAMReadOnlyAccess  
4. ✅ AmazonS3FullAccess
5. 🎯 **AmazonDynamoDBFullAccess** ← **ADD THIS**

**This completes your AWS permissions setup for full Terraform functionality!**
