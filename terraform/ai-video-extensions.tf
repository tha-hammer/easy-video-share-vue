# AI Video Generation Infrastructure Extensions

# Secrets Manager for AI service credentials
resource "aws_secretsmanager_secret" "ai_video_secrets" {
  name        = "${var.project_name}-ai-video-secrets"
  description = "API keys and secrets for AI video generation"

  tags = {
    Name        = "AI Video Secrets"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Store AI service credentials
resource "aws_secretsmanager_secret_version" "ai_video_secrets" {
  secret_id = aws_secretsmanager_secret.ai_video_secrets.id
  secret_string = jsonencode({
    openai_api_key = var.openai_api_key
    google_cloud_project_id = var.google_cloud_project_id
    google_cloud_location = var.google_cloud_location
    google_cloud_service_account_email = var.google_cloud_service_account_email
  })
}

# Lambda Layer for AI video dependencies
resource "aws_lambda_layer_version" "ai_video_layer" {
  filename        = "ai_video_layer.zip"
  layer_name      = "${var.project_name}-ai-video-layer"
  compatible_runtimes = ["nodejs18.x"]
  description     = "AI video generation dependencies (Google Cloud SDK, OpenAI SDK)"

  # This will be created by the build process
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# Lambda function for AI video processing
resource "aws_lambda_function" "ai_video_processor" {
  filename         = "ai_video_lambda.zip"
  function_name    = "${var.project_name}-ai-video-processor"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "ai-video.handler"
  runtime         = "nodejs18.x"
  timeout         = 900  # 15 minutes for AI processing
  memory_size     = 2048 # Increased for video processing

  layers = [aws_lambda_layer_version.ai_video_layer.arn]

  environment {
    variables = {
      DYNAMODB_TABLE      = aws_dynamodb_table.video_metadata.name
      SECRETS_MANAGER_ARN = aws_secretsmanager_secret.ai_video_secrets.arn
      S3_BUCKET          = aws_s3_bucket.video_bucket.bucket
      AUDIO_BUCKET       = aws_s3_bucket.audio_bucket.bucket
      CORS_ORIGIN        = "*"
      GOOGLE_CLOUD_PROJECT_ID = var.google_cloud_project_id
      GOOGLE_CLOUD_LOCATION = var.google_cloud_location
      GOOGLE_CLOUD_SERVICE_ACCOUNT_EMAIL = var.google_cloud_service_account_email
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    # aws_cloudwatch_log_group.ai_video_logs,  # Temporarily commented out
  ]

  # Ignore changes to source code hash during development
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# CloudWatch Log Group for AI video processing
resource "aws_cloudwatch_log_group" "ai_video_logs" {
  name              = "/aws/lambda/${var.project_name}-ai-video-processor"
  retention_in_days = 14

  tags = {
    Name        = "AI Video Processing Logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# API Gateway resource for AI video endpoints
resource "aws_api_gateway_resource" "ai_video_resource" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  parent_id   = aws_api_gateway_rest_api.video_api.root_resource_id
  path_part   = "ai-video"
}

# API Gateway resource for individual AI video status (path parameter)
resource "aws_api_gateway_resource" "ai_video_id_resource" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  parent_id   = aws_api_gateway_resource.ai_video_resource.id
  path_part   = "{videoId}"
}

# POST method for starting AI video generation
resource "aws_api_gateway_method" "ai_video_post" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.ai_video_resource.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

# GET method for checking AI video status
resource "aws_api_gateway_method" "ai_video_get" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.ai_video_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

# GET method for checking individual AI video status
resource "aws_api_gateway_method" "ai_video_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.ai_video_id_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

# OPTIONS method for CORS
resource "aws_api_gateway_method" "ai_video_options" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.ai_video_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# OPTIONS method for CORS (individual AI video)
resource "aws_api_gateway_method" "ai_video_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.ai_video_id_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Integration for POST method
resource "aws_api_gateway_integration" "ai_video_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.ai_video_resource.id
  http_method             = aws_api_gateway_method.ai_video_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_video_processor.invoke_arn
}

# Integration for GET method
resource "aws_api_gateway_integration" "ai_video_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.ai_video_resource.id
  http_method             = aws_api_gateway_method.ai_video_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_video_processor.invoke_arn
}

# Integration for individual AI video GET method
resource "aws_api_gateway_integration" "ai_video_id_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.ai_video_id_resource.id
  http_method             = aws_api_gateway_method.ai_video_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_video_processor.invoke_arn
}

# Integration for OPTIONS method
resource "aws_api_gateway_integration" "ai_video_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.ai_video_resource.id
  http_method             = aws_api_gateway_method.ai_video_options.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_video_processor.invoke_arn
}

# Integration for individual AI video OPTIONS method
resource "aws_api_gateway_integration" "ai_video_id_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.ai_video_id_resource.id
  http_method             = aws_api_gateway_method.ai_video_id_options.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.ai_video_processor.invoke_arn
}

# Method responses for AI video endpoints
resource "aws_api_gateway_method_response" "ai_video_post_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "ai_video_get_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "ai_video_options_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

# Method responses for individual AI video endpoints
resource "aws_api_gateway_method_response" "ai_video_id_get_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_id_resource.id
  http_method = aws_api_gateway_method.ai_video_id_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "ai_video_id_options_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_id_resource.id
  http_method = aws_api_gateway_method.ai_video_id_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

# Integration responses for AI video endpoints
resource "aws_api_gateway_integration_response" "ai_video_post_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_post.http_method
  status_code = aws_api_gateway_method_response.ai_video_post_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.ai_video_post_integration]
}

resource "aws_api_gateway_integration_response" "ai_video_get_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_get.http_method
  status_code = aws_api_gateway_method_response.ai_video_get_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.ai_video_get_integration]
}

resource "aws_api_gateway_integration_response" "ai_video_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_resource.id
  http_method = aws_api_gateway_method.ai_video_options.http_method
  status_code = aws_api_gateway_method_response.ai_video_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token'"
  }

  depends_on = [aws_api_gateway_integration.ai_video_options_integration]
}

# Integration responses for individual AI video endpoints
resource "aws_api_gateway_integration_response" "ai_video_id_get_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_id_resource.id
  http_method = aws_api_gateway_method.ai_video_id_get.http_method
  status_code = aws_api_gateway_method_response.ai_video_id_get_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.ai_video_id_get_integration]
}

resource "aws_api_gateway_integration_response" "ai_video_id_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.ai_video_id_resource.id
  http_method = aws_api_gateway_method.ai_video_id_options.http_method
  status_code = aws_api_gateway_method_response.ai_video_id_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Amz-Security-Token'"
  }

  depends_on = [aws_api_gateway_integration.ai_video_id_options_integration]
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "ai_video_api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_video_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.video_api.execution_arn}/*/*"
}

# API Gateway resource for audio endpoints
resource "aws_api_gateway_resource" "audio_resource" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  parent_id   = aws_api_gateway_rest_api.video_api.root_resource_id
  path_part   = "audio"
}

# POST method for audio uploads
resource "aws_api_gateway_method" "audio_post" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.audio_resource.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

# GET method for listing audio files
resource "aws_api_gateway_method" "audio_get" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.audio_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

# OPTIONS method for CORS (audio)
resource "aws_api_gateway_method" "audio_options" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.audio_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Audio upload-url subresource
resource "aws_api_gateway_resource" "audio_upload_url_resource" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  parent_id   = aws_api_gateway_resource.audio_resource.id
  path_part   = "upload-url"
}

# POST method for getting audio upload URLs
resource "aws_api_gateway_method" "audio_upload_url_post" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

# OPTIONS method for CORS (audio upload-url)
resource "aws_api_gateway_method" "audio_upload_url_options" {
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  resource_id   = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Method responses for audio endpoints
resource "aws_api_gateway_method_response" "audio_post_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_resource.id
  http_method = aws_api_gateway_method.audio_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "audio_get_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_resource.id
  http_method = aws_api_gateway_method.audio_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "audio_options_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_resource.id
  http_method = aws_api_gateway_method.audio_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_method_response" "audio_upload_url_post_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method = aws_api_gateway_method.audio_upload_url_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "audio_upload_url_options_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method = aws_api_gateway_method.audio_upload_url_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

# Integrations for audio endpoints
resource "aws_api_gateway_integration" "audio_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.audio_resource.id
  http_method             = aws_api_gateway_method.audio_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.video_metadata_api.invoke_arn
}

resource "aws_api_gateway_integration" "audio_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.audio_resource.id
  http_method             = aws_api_gateway_method.audio_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.video_metadata_api.invoke_arn
}

resource "aws_api_gateway_integration" "audio_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.audio_resource.id
  http_method             = aws_api_gateway_method.audio_options.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.video_metadata_api.invoke_arn
}

resource "aws_api_gateway_integration" "audio_upload_url_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method             = aws_api_gateway_method.audio_upload_url_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.video_metadata_api.invoke_arn
}

resource "aws_api_gateway_integration" "audio_upload_url_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.video_api.id
  resource_id             = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method             = aws_api_gateway_method.audio_upload_url_options.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.video_metadata_api.invoke_arn
}

# Integration responses for audio endpoints (required for CORS headers)
resource "aws_api_gateway_integration_response" "audio_post_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_resource.id
  http_method = aws_api_gateway_method.audio_post.http_method
  status_code = aws_api_gateway_method_response.audio_post_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.audio_post_integration]
}

resource "aws_api_gateway_integration_response" "audio_get_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_resource.id
  http_method = aws_api_gateway_method.audio_get.http_method
  status_code = aws_api_gateway_method_response.audio_get_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.audio_get_integration]
}

resource "aws_api_gateway_integration_response" "audio_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_resource.id
  http_method = aws_api_gateway_method.audio_options.http_method
  status_code = aws_api_gateway_method_response.audio_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  }

  depends_on = [aws_api_gateway_integration.audio_options_integration]
}

resource "aws_api_gateway_integration_response" "audio_upload_url_post_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method = aws_api_gateway_method.audio_upload_url_post.http_method
  status_code = aws_api_gateway_method_response.audio_upload_url_post_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [aws_api_gateway_integration.audio_upload_url_post_integration]
}

resource "aws_api_gateway_integration_response" "audio_upload_url_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.video_api.id
  resource_id = aws_api_gateway_resource.audio_upload_url_resource.id
  http_method = aws_api_gateway_method.audio_upload_url_options.http_method
  status_code = aws_api_gateway_method_response.audio_upload_url_options_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
  }

  depends_on = [aws_api_gateway_integration.audio_upload_url_options_integration]
}

# Update IAM role policy for AI video capabilities
resource "aws_iam_role_policy" "ai_video_lambda_policy" {
  name  = "${var.project_name}-ai-video-lambda-policy"
  role  = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.ai_video_secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.video_bucket.arn}/ai-generated/*",
          "${aws_s3_bucket.video_bucket.arn}/ai-temp/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.audio_bucket.arn,
          "${aws_s3_bucket.audio_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ]
        Resource = "*"
      }
    ]
  })
}

# API Gateway deployment for AI video resources
resource "aws_api_gateway_deployment" "ai_video_deployment" {
  depends_on = [
    aws_api_gateway_integration.ai_video_post_integration,
    aws_api_gateway_integration.ai_video_get_integration,
    aws_api_gateway_integration.ai_video_options_integration,
    aws_api_gateway_integration.ai_video_id_get_integration,
    aws_api_gateway_integration.ai_video_id_options_integration,
    aws_api_gateway_integration_response.ai_video_post_integration_response,
    aws_api_gateway_integration_response.ai_video_get_integration_response,
    aws_api_gateway_integration_response.ai_video_options_integration_response,
    aws_api_gateway_integration_response.ai_video_id_get_integration_response,
    aws_api_gateway_integration_response.ai_video_id_options_integration_response,
  ]

  rest_api_id = aws_api_gateway_rest_api.video_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.ai_video_resource.id,
      aws_api_gateway_resource.ai_video_id_resource.id,
      aws_api_gateway_method.ai_video_post.id,
      aws_api_gateway_method.ai_video_get.id,
      aws_api_gateway_method.ai_video_options.id,
      aws_api_gateway_method.ai_video_id_get.id,
      aws_api_gateway_method.ai_video_id_options.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Update the existing stage to use the new deployment
resource "aws_api_gateway_stage" "video_api_stage" {
  deployment_id = aws_api_gateway_deployment.ai_video_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.video_api.id
  stage_name    = var.environment

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
} 