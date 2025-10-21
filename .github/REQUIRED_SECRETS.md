# Required GitHub Secrets Configuration

To resolve the "Context access might be invalid" warnings in GitHub Actions workflows, the following secrets must be configured in your GitHub repository settings:

## Go to: Repository Settings → Secrets and variables → Actions

### Required Secrets for CI/CD Pipeline (`ci-cd.yml`):

- `SLACK_WEBHOOK`: Slack webhook URL for notifications
- `AWS_ACCESS_KEY_ID`: AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key for deployment

### Required Secrets for Infrastructure Pipeline (`infrastructure.yml`):

- `AWS_ACCESS_KEY_ID`: AWS access key for staging environment
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key for staging environment  
- `TF_STATE_BUCKET`: S3 bucket name for Terraform state (staging)
- `AWS_ACCESS_KEY_ID_PROD`: AWS access key for production environment
- `AWS_SECRET_ACCESS_KEY_PROD`: AWS secret access key for production environment
- `TF_STATE_BUCKET_PROD`: S3 bucket name for Terraform state (production)
- `SLACK_WEBHOOK`: Slack webhook URL for notifications

## How to Add Secrets:

1. Navigate to your GitHub repository
2. Go to Settings → Security → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the secret name and value
5. Repeat for all required secrets

## Security Notes:

- Never commit actual secret values to code
- Use least-privilege IAM policies for AWS keys
- Rotate secrets regularly
- Consider using GitHub OIDC for AWS authentication instead of long-lived keys

The workflow files are correctly configured to use these secrets - they just need to be added to the repository settings to resolve the linting warnings.