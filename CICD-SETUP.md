# CI/CD Setup Guide for Easy Video Share

This guide will help you set up continuous integration and deployment (CI/CD) for your Easy Video Share project using GitHub Actions and AWS IAM roles with OIDC (no AWS access keys needed).

## 📋 Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **AWS Account**: With permissions to create IAM roles and OIDC providers
3. **Terraform**: For infrastructure management

## 🔧 Step-by-Step Setup

### Step 1: Update Terraform Configuration

1. **Edit `terraform/terraform.tfvars`** and add your GitHub repository:

   ```hcl
   # Your existing variables
   bucket_name = "easy-video-share-yourname-dev"
   aws_region = "us-east-1"
   environment = "dev"

   # Add this line with your actual GitHub username/repository
   github_repository = "your-username/easy-video-share-vue"
   ```

2. **Deploy the OIDC provider and IAM role**:

   ```bash
   cd terraform
   terraform plan
   terraform apply
   ```

3. **Get the GitHub Actions role ARN**:
   ```bash
   terraform output github_actions_role_arn
   ```
   Copy this ARN - you'll need it for GitHub secrets.

### Step 2: Configure GitHub Repository Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add a new repository secret:
   - **Name**: `AWS_ROLE_TO_ASSUME`
   - **Value**: The role ARN from Step 1 (e.g., `arn:aws:iam::123456789012:role/easy-video-share-github-actions-role`)

### Step 3: Test the CI/CD Pipeline

1. **Commit and push your changes**:

   ```bash
   git add .
   git commit -m "Add CI/CD pipeline with GitHub Actions"
   git push origin main
   ```

2. **Check GitHub Actions**:
   - Go to your repository on GitHub
   - Click on the **Actions** tab
   - You should see the workflows running

### Step 4: Understanding the Workflows

#### Backend Deployment (`backend-deploy.yml`)

- **Triggers**: Changes to `terraform/` directory
- **On Pull Requests**: Runs `terraform plan` and comments the plan on the PR
- **On Main Branch**: Runs `terraform apply` to deploy infrastructure changes

#### Frontend Deployment (`frontend-deploy.yml`)

- **Triggers**: Changes to frontend code (`src/`, `package.json`, etc.)
- **Dependencies**: Runs after backend deployment if needed
- **Process**:
  1. Builds the Vue.js application
  2. Runs tests and linting
  3. Deploys to S3 automatically
  4. Sets proper caching headers
  5. Invalidates CloudFront (if configured)

## 🔒 Security Features

### What Makes This Secure?

1. **No AWS Access Keys**: Uses OIDC to assume IAM roles temporarily
2. **Repository-Specific**: Only your specific GitHub repository can assume the role
3. **Branch-Specific**: Only `main`/`master` branch can deploy to production
4. **Least Privilege**: IAM role has only the minimum permissions needed
5. **Temporary Credentials**: GitHub gets temporary credentials that expire quickly

### Trust Policy Explanation

The IAM role trusts:

- **GitHub's OIDC Provider**: `token.actions.githubusercontent.com`
- **Your Repository Only**: `repo:your-username/your-repo:ref:refs/heads/main`
- **Specific Branches**: Only main/master branches can assume the role

## 🚀 Deployment Flow

### Development Workflow

1. **Feature Development**:

   ```bash
   git checkout -b feature/new-feature
   # Make your changes
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **Create Pull Request**:

   - GitHub Actions runs tests and terraform plan
   - Review the plan in the PR comments
   - Merge when ready

3. **Automatic Deployment**:
   - When you merge to `main`, GitHub Actions automatically:
     - Deploys infrastructure changes (if any)
     - Builds and deploys the frontend
     - Updates your live application

### Manual Testing

You can also trigger workflows manually:

1. Go to **Actions** tab in GitHub
2. Select a workflow
3. Click **Run workflow**

## 🎯 Benefits for Cloud Resume Challenge

This setup demonstrates several key DevOps and cloud skills:

1. **Infrastructure as Code**: Using Terraform for reproducible infrastructure
2. **CI/CD Pipelines**: Automated testing and deployment
3. **Security Best Practices**: No hardcoded credentials, OIDC authentication
4. **Modern Git Workflow**: Feature branches, pull requests, automated deployment
5. **Cloud-Native Architecture**: Serverless, managed services, scalable design

## 🐛 Troubleshooting

### Common Issues

1. **"Unable to assume role"**:

   - Check that `github_repository` variable matches your actual repository
   - Verify the repository secret `AWS_ROLE_TO_ASSUME` is correct
   - Ensure you're pushing to `main` or `master` branch

2. **Terraform state issues**:

   - Make sure your local Terraform state is pushed to the repository
   - Consider using remote state storage (S3 + DynamoDB) for team environments

3. **Build failures**:

   - Check the Actions logs for specific error messages
   - Ensure all required environment variables are available
   - Verify Node.js version compatibility

4. **Permission denied**:
   - Check IAM role permissions in `github-oidc.tf`
   - Verify AWS region matches your resources

### Useful Commands

```bash
# Check workflow status
gh run list

# View workflow logs
gh run view --log

# Test terraform locally
cd terraform
terraform plan

# Test frontend build locally
npm run build-only
```

## 📚 Next Steps

1. **Add Tests**: Expand the test suite for better CI validation
2. **Environment Promotion**: Set up dev/staging/prod environments
3. **Monitoring**: Add CloudWatch dashboards and alerts
4. **Performance**: Add CloudFront CDN for better performance
5. **Security**: Add security scanning to the CI pipeline

## 🔗 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS OIDC with GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [Cloud Resume Challenge](https://cloudresumechallenge.dev/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

🎉 **Congratulations!** You now have a fully automated, secure CI/CD pipeline for your Easy Video Share application!
