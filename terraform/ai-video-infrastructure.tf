# =============================================================================
# AI Video Generation Infrastructure
# Terraform configuration for Bedrock Nova Reel integration
# =============================================================================

# Conditionally create AI video generation resources
locals {
  create_ai_resources = var.enable_ai_video_pipeline
}

# =============================================================================
# DynamoDB Tables for AI Video Generation
# =============================================================================

# AI Projects Table
resource "aws_dynamodb_table" "ai_projects" {
  count = local.create_ai_resources ? 1 : 0
  
  name           = "${var.project_name}-ai-projects-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "project_id"

  attribute {
    name = "project_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name     = "user-projects-index"
    hash_key = "user_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name     = "status-index"
    hash_key = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "AI Projects"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Video Assets Table (for generated content)
resource "aws_dynamodb_table" "video_assets" {
  count = local.create_ai_resources ? 1 : 0
  
  name           = "${var.project_name}-video-assets-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "asset_id"

  attribute {
    name = "asset_id"
    type = "S"
  }

  attribute {
    name = "project_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name     = "project-assets-index"
    hash_key = "project_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name     = "status-index"
    hash_key = "status"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Video Assets"
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# Secrets Manager for API Keys
# =============================================================================

resource "aws_secretsmanager_secret" "ai_api_keys" {
  count = local.create_ai_resources ? 1 : 0
  
  name        = "${var.project_name}-ai-api-keys-${var.environment}"
  description = "API keys for AI services (OpenAI, etc.)"

  tags = {
    Name        = "AI API Keys"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "ai_api_keys" {
  count = local.create_ai_resources ? 1 : 0
  
  secret_id = aws_secretsmanager_secret.ai_api_keys[0].id
  secret_string = jsonencode({
    openai_api_key = var.openai_api_key
    # Add other API keys as needed
  })
}

# =============================================================================
# EventBridge for Async Processing
# =============================================================================

resource "aws_cloudwatch_event_bus" "ai_video_bus" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-ai-video-bus-${var.environment}"

  tags = {
    Name        = "AI Video Generation Event Bus"
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# VPC and Networking for ECS
# =============================================================================

# VPC for ECS (create if needed)
resource "aws_vpc" "main" {
  count = local.create_ai_resources && var.create_vpc ? 1 : 0
  
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-vpc-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = local.create_ai_resources && var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name        = "${var.project_name}-igw-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Public Subnets
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public" {
  count = local.create_ai_resources && var.create_vpc ? 2 : 0
  
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-public-subnet-${count.index + 1}-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  count = local.create_ai_resources && var.create_vpc ? 1 : 0
  
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = {
    Name        = "${var.project_name}-public-rt-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = local.create_ai_resources && var.create_vpc ? 2 : 0
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  count = local.create_ai_resources ? 1 : 0
  
  name_prefix = "${var.project_name}-ecs-tasks-${var.environment}"
  vpc_id      = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 8080
    to_port     = 8080
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-ecs-tasks-sg-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# ECR Repository for Video Processor
# =============================================================================

resource "aws_ecr_repository" "video_processor" {
  count = local.create_ai_resources ? 1 : 0
  
  name                 = "${var.project_name}-video-processor-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "Video Processor Repository"
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "video_processor" {
  count = local.create_ai_resources ? 1 : 0
  
  repository = aws_ecr_repository.video_processor[0].name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# ECS Cluster and Task Definition
# =============================================================================

resource "aws_ecs_cluster" "video_processor" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-video-processor-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "Video Processing Cluster"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "video_processor" {
  count = local.create_ai_resources ? 1 : 0
  
  name              = "/ecs/${var.project_name}-video-processor-${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "Video Processor Logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# IAM Roles for ECS and Bedrock Access
# =============================================================================

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-ecs-task-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "ECS Task Execution Role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach ECS Task Execution Role Policy
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  count = local.create_ai_resources ? 1 : 0
  
  role       = aws_iam_role.ecs_task_execution_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (for application permissions)
resource "aws_iam_role" "ecs_task_role" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-ecs-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "ECS Task Role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Custom policy for ECS task (S3, DynamoDB, Bedrock, Secrets Manager)
resource "aws_iam_role_policy" "ecs_task_policy" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-ecs-task-policy-${var.environment}"
  role = aws_iam_role.ecs_task_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # S3 permissions
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.video_bucket.arn,
          "${aws_s3_bucket.video_bucket.arn}/*"
        ]
      },
      # DynamoDB permissions
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.ai_projects[0].arn,
          "${aws_dynamodb_table.ai_projects[0].arn}/index/*",
          aws_dynamodb_table.video_assets[0].arn,
          "${aws_dynamodb_table.video_assets[0].arn}/index/*"
        ]
      },
      # Bedrock permissions
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel"
        ]
        Resource = "*"
      },
      # Secrets Manager permissions
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.ai_api_keys[0].arn
      },
      # EventBridge permissions
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = aws_cloudwatch_event_bus.ai_video_bus[0].arn
      },
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      }
    ]
  })
}

# =============================================================================
# ECS Task Definition
# =============================================================================

resource "aws_ecs_task_definition" "video_processor" {
  count = local.create_ai_resources ? 1 : 0
  
  family                   = "${var.project_name}-video-processor-${var.environment}"
  network_mode            = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                     = 2048   # 2 vCPU
  memory                  = 8192   # 8GB RAM
  execution_role_arn      = aws_iam_role.ecs_task_execution_role[0].arn
  task_role_arn          = aws_iam_role.ecs_task_role[0].arn

  container_definitions = jsonencode([
    {
      name  = "video-processor"
      image = "${aws_ecr_repository.video_processor[0].repository_url}:latest"

      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "ENVIRONMENT", value = var.environment },
        { name = "PROJECT_NAME", value = var.project_name },
        { name = "S3_BUCKET", value = aws_s3_bucket.video_bucket.bucket },
        { name = "AI_PROJECTS_TABLE", value = aws_dynamodb_table.ai_projects[0].name },
        { name = "VIDEO_ASSETS_TABLE", value = aws_dynamodb_table.video_assets[0].name },
        { name = "EVENT_BUS_NAME", value = aws_cloudwatch_event_bus.ai_video_bus[0].name },
        { name = "SECRETS_NAME", value = aws_secretsmanager_secret.ai_api_keys[0].name },
        { name = "USE_LOCALSTACK", value = "false" },
        { name = "LOG_LEVEL", value = "INFO" }
      ]

      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.video_processor[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name        = "Video Processor Task"
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# ECS Service
# =============================================================================

resource "aws_ecs_service" "video_processor" {
  count = local.create_ai_resources ? 1 : 0
  
  name            = "${var.project_name}-video-processor-${var.environment}"
  cluster         = aws_ecs_cluster.video_processor[0].id
  task_definition = aws_ecs_task_definition.video_processor[0].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.create_vpc ? aws_subnet.public[*].id : [var.vpc_id]
    security_groups  = [aws_security_group.ecs_tasks[0].id]
    assign_public_ip = true
  }

  # Enable service discovery (optional)
  # service_registries {
  #   registry_arn = aws_service_discovery_service.video_processor[0].arn
  # }

  tags = {
    Name        = "Video Processor Service"
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# Lambda Function for Video Processing Orchestration
# =============================================================================

resource "aws_lambda_function" "video_processor_orchestrator" {
  count = local.create_ai_resources ? 1 : 0
  
  filename         = "video_processor_orchestrator.zip"
  function_name    = "${var.project_name}-video-processor-orchestrator-${var.environment}"
  role            = aws_iam_role.lambda_orchestrator_role[0].arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      ECS_CLUSTER_ARN = aws_ecs_cluster.video_processor[0].arn
      ECS_TASK_DEFINITION = aws_ecs_task_definition.video_processor[0].arn
      SUBNET_IDS = join(",", var.create_vpc ? aws_subnet.public[*].id : [var.vpc_id])
      SECURITY_GROUP_ID = aws_security_group.ecs_tasks[0].id
      AI_PROJECTS_TABLE = aws_dynamodb_table.ai_projects[0].name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_orchestrator_policy,
    aws_cloudwatch_log_group.lambda_orchestrator_logs,
  ]

  tags = {
    Name        = "Video Processor Orchestrator"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Lambda Orchestrator
resource "aws_iam_role" "lambda_orchestrator_role" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-lambda-orchestrator-role-${var.environment}"

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
    Name        = "Lambda Orchestrator Role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Policy for Lambda Orchestrator
resource "aws_iam_role_policy" "lambda_orchestrator_policy" {
  count = local.create_ai_resources ? 1 : 0
  
  name = "${var.project_name}-lambda-orchestrator-policy-${var.environment}"
  role = aws_iam_role.lambda_orchestrator_role[0].id

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
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:DescribeTasks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution_role[0].arn,
          aws_iam_role.ecs_task_role[0].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.ai_projects[0].arn
      }
    ]
  })
}

# Attach basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_orchestrator_policy" {
  count = local.create_ai_resources ? 1 : 0
  
  role       = aws_iam_role.lambda_orchestrator_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_orchestrator_logs" {
  count = local.create_ai_resources ? 1 : 0
  
  name              = "/aws/lambda/${var.project_name}-video-processor-orchestrator-${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "Lambda Orchestrator Logs"
    Environment = var.environment
    Project     = var.project_name
  }
} 