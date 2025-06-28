# EventBridge rule for AWS Transcribe job state changes
resource "aws_cloudwatch_event_rule" "transcribe_job_state_change" {
  name        = "${var.project_name}-transcribe-job-state-change"
  description = "Capture AWS Transcribe job state changes"

  event_pattern = jsonencode({
    source      = ["aws.transcribe"]
    detail-type = ["Transcribe Job State Change"]
    detail = {
      TranscriptionJobStatus = ["COMPLETED", "FAILED"]
    }
  })

  tags = {
    Name        = "${var.project_name}-transcribe-events"
    Environment = var.environment
    Project     = var.project_name
  }
}

# EventBridge target for transcription completion
resource "aws_cloudwatch_event_target" "transcribe_lambda_target" {
  rule      = aws_cloudwatch_event_rule.transcribe_job_state_change.name
  target_id = "TranscribeLambdaTarget"
  arn       = aws_lambda_function.transcription_processor.arn
}

# Lambda function to process transcription completion events
resource "aws_lambda_function" "transcription_processor" {
  filename         = "transcription_processor.zip"
  function_name    = "${var.project_name}-transcription-processor"
  role            = aws_iam_role.transcription_processor_role.arn
  handler         = "transcription-processor.handler"
  runtime         = "nodejs18.x"
  timeout         = 300  # 5 minutes
  memory_size     = 512

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.video_metadata.name
      AUDIO_BUCKET   = aws_s3_bucket.audio_bucket.bucket
    }
  }

  depends_on = [
    aws_iam_role_policy.transcription_processor_policy,
    aws_cloudwatch_log_group.transcription_processor_logs
  ]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = {
    Name        = "${var.project_name}-transcription-processor"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM role for transcription processor Lambda
resource "aws_iam_role" "transcription_processor_role" {
  name = "${var.project_name}-transcription-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-transcription-processor-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for transcription processor
resource "aws_iam_role_policy" "transcription_processor_policy" {
  name = "${var.project_name}-transcription-processor-policy"
  role = aws_iam_role.transcription_processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.video_metadata.arn,
          "${aws_dynamodb_table.video_metadata.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:GetTranscriptionJob"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.audio_bucket.arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group for transcription processor
resource "aws_cloudwatch_log_group" "transcription_processor_logs" {
  name              = "/aws/lambda/${var.project_name}-transcription-processor"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-transcription-processor-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Lambda permission for EventBridge to invoke transcription processor
resource "aws_lambda_permission" "allow_eventbridge_transcription" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transcription_processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.transcribe_job_state_change.arn
}

# WebSocket API for real-time updates (optional - for better UX)
resource "aws_apigatewayv2_api" "websocket_api" {
  name                       = "${var.project_name}-websocket-api"
  protocol_type             = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  tags = {
    Name        = "${var.project_name}-websocket-api"
    Environment = var.environment
    Project     = var.project_name
  }
}

# WebSocket deployment
resource "aws_apigatewayv2_deployment" "websocket_deployment" {
  api_id      = aws_apigatewayv2_api.websocket_api.id
  description = "WebSocket deployment for real-time transcription updates"

  depends_on = [
    aws_apigatewayv2_route.websocket_connect,
    aws_apigatewayv2_route.websocket_disconnect,
    aws_apigatewayv2_route.websocket_default
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# WebSocket stage
resource "aws_apigatewayv2_stage" "websocket_stage" {
  api_id        = aws_apigatewayv2_api.websocket_api.id
  deployment_id = aws_apigatewayv2_deployment.websocket_deployment.id
  name          = var.environment

  tags = {
    Name        = "${var.project_name}-websocket-stage"
    Environment = var.environment
    Project     = var.project_name
  }
}

# WebSocket routes
resource "aws_apigatewayv2_route" "websocket_connect" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_integration.id}"
}

resource "aws_apigatewayv2_route" "websocket_disconnect" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_integration.id}"
}

resource "aws_apigatewayv2_route" "websocket_default" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_integration.id}"
}

# WebSocket integration
resource "aws_apigatewayv2_integration" "websocket_integration" {
  api_id             = aws_apigatewayv2_api.websocket_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.websocket_handler.invoke_arn
  integration_method = "POST"
}

# WebSocket handler Lambda
resource "aws_lambda_function" "websocket_handler" {
  filename         = "websocket_handler.zip"
  function_name    = "${var.project_name}-websocket-handler"
  role            = aws_iam_role.websocket_handler_role.arn
  handler         = "websocket-handler.handler"
  runtime         = "nodejs18.x"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.video_metadata.name
    }
  }

  depends_on = [
    aws_iam_role_policy.websocket_handler_policy,
    aws_cloudwatch_log_group.websocket_handler_logs
  ]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = {
    Name        = "${var.project_name}-websocket-handler"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM role for WebSocket handler
resource "aws_iam_role" "websocket_handler_role" {
  name = "${var.project_name}-websocket-handler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-websocket-handler-role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for WebSocket handler
resource "aws_iam_role_policy" "websocket_handler_policy" {
  name = "${var.project_name}-websocket-handler-policy"
  role = aws_iam_role.websocket_handler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.video_metadata.arn,
          "${aws_dynamodb_table.video_metadata.arn}/index/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group for WebSocket handler
resource "aws_cloudwatch_log_group" "websocket_handler_logs" {
  name              = "/aws/lambda/${var.project_name}-websocket-handler"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-websocket-handler-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Lambda permission for WebSocket API Gateway
resource "aws_lambda_permission" "websocket_api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/*"
}

# DynamoDB table for WebSocket connections (to track which users are connected)
resource "aws_dynamodb_table" "websocket_connections" {
  name           = "${var.project_name}-websocket-connections"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "connectionId"

  attribute {
    name = "connectionId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  global_secondary_index {
    name            = "userId-index"
    hash_key        = "userId"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-websocket-connections"
    Environment = var.environment
    Project     = var.project_name
  }
}
