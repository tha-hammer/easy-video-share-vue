#!/bin/bash
set -e

echo "🚀 Initializing LocalStack with AI Video Generation resources..."

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
until curl -f http://localstack:4566/health > /dev/null 2>&1; do
    echo "LocalStack not ready yet, waiting..."
    sleep 2
done

echo "✅ LocalStack is ready!"

# Set AWS CLI configuration for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Create DynamoDB tables
echo "📊 Creating DynamoDB tables..."

# AI Projects table with JSON format
echo "Creating AI Projects table..."
aws dynamodb create-table \
    --endpoint-url http://localstack:4566 \
    --table-name easy-video-share-ai-projects-dev \
    --cli-input-json '{
        "AttributeDefinitions": [
            {
                "AttributeName": "project_id",
                "AttributeType": "S"
            },
            {
                "AttributeName": "user_id", 
                "AttributeType": "S"
            },
            {
                "AttributeName": "created_at",
                "AttributeType": "S"
            }
        ],
        "KeySchema": [
            {
                "AttributeName": "project_id",
                "KeyType": "HASH"
            }
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "UserProjectsIndex",
                "KeySchema": [
                    {
                        "AttributeName": "user_id",
                        "KeyType": "HASH"
                    },
                    {
                        "AttributeName": "created_at",
                        "KeyType": "RANGE"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            }
        ],
        "BillingMode": "PAY_PER_REQUEST"
    }'

echo "✅ AI Projects table created"

# Video Assets table with JSON format  
echo "Creating Video Assets table..."
aws dynamodb create-table \
    --endpoint-url http://localstack:4566 \
    --table-name easy-video-share-video-assets-dev \
    --cli-input-json '{
        "AttributeDefinitions": [
            {
                "AttributeName": "asset_id",
                "AttributeType": "S"
            },
            {
                "AttributeName": "project_id",
                "AttributeType": "S"
            }
        ],
        "KeySchema": [
            {
                "AttributeName": "asset_id",
                "KeyType": "HASH"
            }
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "ProjectAssetsIndex",
                "KeySchema": [
                    {
                        "AttributeName": "project_id",
                        "KeyType": "HASH"
                    }
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            }
        ],
        "BillingMode": "PAY_PER_REQUEST"
    }'

echo "✅ Video Assets table created"

# Create S3 bucket for video storage
echo "🪣 Creating S3 bucket..."
aws s3api create-bucket \
    --endpoint-url http://localstack:4566 \
    --bucket easy-video-share-silmari-dev

echo "✅ S3 bucket created"

# Create EventBridge custom bus
echo "🎯 Creating EventBridge custom bus..."
aws events create-event-bus \
    --endpoint-url http://localstack:4566 \
    --name easy-video-share-ai-video-bus-dev

echo "✅ EventBridge bus created"

# Create Secrets Manager secret with API keys
echo "🔐 Creating Secrets Manager secret..."
aws secretsmanager create-secret \
    --endpoint-url http://localstack:4566 \
    --name easy-video-share-ai-api-keys-dev \
    --description "API keys for AI video generation services" \
    --secret-string '{"kling_api_key":"","openai_api_key":""}'

echo "✅ Secrets Manager secret created"

# Insert sample data for testing
echo "📝 Inserting sample data..."

# Sample AI project with JSON format
aws dynamodb put-item \
    --endpoint-url http://localstack:4566 \
    --table-name easy-video-share-ai-projects-dev \
    --cli-input-json '{
        "Item": {
            "project_id": {"S": "test-project-123"},
            "user_id": {"S": "test-user-456"},
            "title": {"S": "Test AI Video Project"},
            "prompt": {"S": "A beautiful sunset over mountains"},
            "status": {"S": "pending"},
            "created_at": {"S": "2024-01-15T10:00:00Z"},
            "updated_at": {"S": "2024-01-15T10:00:00Z"},
            "duration": {"N": "5"},
            "style": {"S": "realistic"},
            "aspect_ratio": {"S": "16:9"}
        }
    }'

echo "✅ Sample project data inserted"

# Sample video asset with JSON format
aws dynamodb put-item \
    --endpoint-url http://localstack:4566 \
    --table-name easy-video-share-video-assets-dev \
    --cli-input-json '{
        "Item": {
            "asset_id": {"S": "asset-test-789"},
            "project_id": {"S": "test-project-123"},
            "asset_type": {"S": "video"},
            "status": {"S": "pending"},
            "created_at": {"S": "2024-01-15T10:00:00Z"},
            "metadata": {
                "M": {
                    "prompt": {"S": "Mountain scene at sunset"},
                    "duration": {"N": "5"}
                }
            }
        }
    }'

echo "✅ Sample asset data inserted"

# Verify tables were created
echo "🔍 Verifying table creation..."
aws dynamodb list-tables --endpoint-url http://localstack:4566

echo "🎉 LocalStack initialization complete!"
echo ""
echo "📋 Available resources:"
echo "  🏗️  DynamoDB Tables:"
echo "     - easy-video-share-ai-projects-dev"
echo "     - easy-video-share-video-assets-dev"
echo "  🪣  S3 Bucket: easy-video-share-silmari-dev"
echo "  🎯  EventBridge Bus: easy-video-share-ai-video-bus-dev"
echo "  🔐  Secret: easy-video-share-ai-api-keys-dev"
echo ""
echo "🌐 You can now test the AI Video Processor at http://localhost:8080"
echo "📊 Health check: http://localhost:8080/health"
echo "📡 Process video: POST http://localhost:8080/process-video" 