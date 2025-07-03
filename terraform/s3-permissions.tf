# IAM user for application access (for multi-part uploads)
resource "aws_iam_user" "video_app_user" {
  name = "${var.project_name}-app-user"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for application user with multi-part upload permissions
resource "aws_iam_user_policy" "video_app_user_policy" {
  name = "${var.project_name}-app-policy"
  user = aws_iam_user.video_app_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:CreateMultipartUpload",
          "s3:UploadPart",
          "s3:CompleteMultipartUpload",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          aws_s3_bucket.video_bucket.arn,
          "${aws_s3_bucket.video_bucket.arn}/*"
        ]
      }
    ]
  })
}

# Access keys for the application user
resource "aws_iam_access_key" "video_app_user_key" {
  user = aws_iam_user.video_app_user.name
}

# Outputs are defined in outputs.tf 