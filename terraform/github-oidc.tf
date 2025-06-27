# GitHub Actions OIDC Provider and IAM Role for CI/CD
# This enables GitHub Actions to assume AWS roles without storing AWS access keys

# Data source for GitHub's OIDC provider thumbprint
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# OIDC Identity Provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    data.tls_certificate.github.certificates[0].sha1_fingerprint,
    # GitHub's current thumbprint (as of 2024)
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    # Backup thumbprint
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "${var.project_name}-github-oidc"
    Environment = var.environment
    Purpose     = "GitHub Actions OIDC"
  }
}

# Trust policy for GitHub Actions to assume the role
data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      # Replace YOUR_GITHUB_USERNAME/YOUR_REPO_NAME with your actual repository
      # Format: repo:username/repository:ref:refs/heads/main
      values = [
        "repo:${var.github_repository}:ref:refs/heads/main",
        "repo:${var.github_repository}:ref:refs/heads/master"
      ]
    }
  }
}

# IAM policy for GitHub Actions deployment permissions
data "aws_iam_policy_document" "github_actions_policy" {
  # S3 permissions for frontend deployment
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:GetObjectVersion",
      "s3:PutObjectAcl"
    ]
    resources = [
      aws_s3_bucket.video_bucket.arn,
      "${aws_s3_bucket.video_bucket.arn}/*",
      aws_s3_bucket.audio_bucket.arn,
      "${aws_s3_bucket.audio_bucket.arn}/*"
    ]
  }

  # Terraform state and configuration
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::terraform-state-*",
      "arn:aws:s3:::terraform-state-*/*"
    ]
  }

  # DynamoDB for Terraform state locking (if used)
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem"
    ]
    resources = [
      "arn:aws:dynamodb:*:*:table/terraform-state-lock*"
    ]
  }

  # Lambda permissions for backend updates
  statement {
    effect = "Allow"
    actions = [
      "lambda:GetFunction",
      "lambda:UpdateFunctionCode",
      "lambda:UpdateFunctionConfiguration",
      "lambda:PublishVersion",
      "lambda:CreateAlias",
      "lambda:UpdateAlias",
      "lambda:GetAlias",
      "lambda:ListVersionsByFunction"
    ]
    resources = [
      aws_lambda_function.video_metadata_api.arn,
      "${aws_lambda_function.video_metadata_api.arn}:*",
      aws_lambda_function.admin_api.arn,
      "${aws_lambda_function.admin_api.arn}:*",
      aws_lambda_function.ai_video_processor.arn,
      "${aws_lambda_function.ai_video_processor.arn}:*"
    ]
  }

  # API Gateway permissions
  statement {
    effect = "Allow"
    actions = [
      "apigateway:GET",
      "apigateway:POST",
      "apigateway:PUT",
      "apigateway:DELETE",
      "apigateway:PATCH"
    ]
    resources = [
      "arn:aws:apigateway:${var.aws_region}::/restapis/${aws_api_gateway_rest_api.video_api.id}/*"
    ]
  }

  # CloudFront invalidation (if using CloudFront)
  statement {
    effect = "Allow"
    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:ListDistributions",
      "cloudfront:GetDistribution"
    ]
    resources = ["*"]
  }

  # Terraform provider permissions
  statement {
    effect = "Allow"
    actions = [
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:GetPolicy",
      "iam:GetPolicyVersion",
      "iam:ListAttachedRolePolicies",
      "iam:ListRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "sts:GetCallerIdentity"
    ]
    resources = ["*"]
  }

  # DynamoDB permissions for application
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [
      aws_dynamodb_table.video_metadata.arn,
      "${aws_dynamodb_table.video_metadata.arn}/index/*"
    ]
  }

  # Cognito permissions
  statement {
    effect = "Allow"
    actions = [
      "cognito-idp:DescribeUserPool",
      "cognito-idp:DescribeUserPoolClient",
      "cognito-idp:ListUsers",
      "cognito-idp:AdminGetUser"
    ]
    resources = [
      aws_cognito_user_pool.video_app_users.arn
    ]
  }
}

# IAM role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name               = "${var.project_name}-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = {
    Name        = "${var.project_name}-github-actions-role"
    Environment = var.environment
    Purpose     = "GitHub Actions CI/CD"
  }
}

# Attach the policy to the role
resource "aws_iam_role_policy" "github_actions" {
  name   = "${var.project_name}-github-actions-policy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_policy.json
}

# Output the role ARN for GitHub secrets
output "github_actions_role_arn" {
  description = "ARN of the IAM role for GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github.arn
}
