# AI Video Processor - Local Development

This directory contains the AI Video Processor service for generating videos using AI models like Kling AI and OpenAI.

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.11+ (for running tests locally)
- [Git](https://git-scm.com/)

### 1. Local Development with Docker Compose

The easiest way to test the AI Video Processor locally is using Docker Compose with LocalStack (mock AWS services).

```bash
# Navigate to the video-processor directory
cd terraform/video-processor

# Start all services (LocalStack + Video Processor)
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f video-processor
```

This will start:

- **LocalStack** on `http://localhost:4566` (mock AWS services)
- **Video Processor API** on `http://localhost:8080`

### 2. Run Tests

Once the services are running, test the API:

```bash
# Install test dependencies
pip install requests

# Run the test script
python test_api.py
```

Expected output:

```
🚀 Starting AI Video Processor API Tests
============================================================

📝 Running: Health Check
🔍 Testing health check...
✅ Health check passed
   Status: healthy
   Environment: dev
   Using LocalStack: True
   Version: 1.0.0
✅ Health Check PASSED

📝 Running: List Projects
🔍 Testing project listing...
✅ Project listing passed
   Found 1 projects
✅ List Projects PASSED

📝 Running: Video Processing
🔍 Testing video processing with project ID: test-1705123456
✅ Video processing request submitted
⏳ Waiting for processing to complete...
   Attempt 1: Status = processing
   Message: Analyzing prompt and requirements
   Stage: analyzing
   ...
✅ Video processing completed successfully!
   Video URL: https://example.com/generated/test-1705123456.mp4
✅ Video Processing PASSED

🏁 Test Results: 4/4 tests passed
🎉 All tests passed! Your AI Video Processor is working correctly.
```

## 📋 API Endpoints

### Health Check

```bash
curl http://localhost:8080/health
```

### List All Projects

```bash
curl http://localhost:8080/projects
```

### Get Specific Project

```bash
curl http://localhost:8080/projects/test-project-123
```

### Submit Video Processing Request

```bash
curl -X POST http://localhost:8080/process-video \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-test-video-001",
    "prompt": "A beautiful sunset over mountains with flowing water",
    "duration": 5,
    "style": "realistic",
    "aspect_ratio": "16:9"
  }'
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `env.example`):

```bash
cp env.example .env
```

Key configuration options:

```env
# Application settings
ENVIRONMENT=dev
PROJECT_NAME=easy-video-share
LOG_LEVEL=DEBUG

# Use LocalStack for local development
USE_LOCALSTACK=true

# API Keys (add your real keys for testing)
KLING_API_KEY=your_kling_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Docker Compose Configuration

The `docker-compose.yml` file configures:

- **LocalStack**: Mock AWS services (DynamoDB, S3, EventBridge, Secrets Manager)
- **Video Processor**: FastAPI application
- **LocalStack Init**: Automatically creates tables and sample data

## 🗄️ Local AWS Resources

When you run `docker-compose up`, LocalStack automatically creates:

### DynamoDB Tables

- `easy-video-share-ai-projects-dev` - AI video projects
- `easy-video-share-video-assets-dev` - Video assets and components

### S3 Bucket

- `easy-video-share-silmari-dev` - Video storage

### EventBridge

- `easy-video-share-ai-video-bus-dev` - Event bus for processing events

### Secrets Manager

- `easy-video-share-ai-api-keys-dev` - API keys storage

### Sample Data

- Test project: `test-project-123`
- Test asset: `asset-test-789`

## 🧪 Testing Scenarios

### 1. Basic Health Check

Verifies the service is running and configured correctly.

### 2. Project Listing

Tests reading from DynamoDB tables with sample data.

### 3. Video Processing Simulation

Tests the complete video processing workflow:

1. Submit processing request
2. Monitor status changes through different stages
3. Verify completion with mock video URL

### 4. Error Handling

The service includes comprehensive error handling for:

- Missing projects (404 errors)
- Database connection issues
- Invalid request parameters

## 🔍 Monitoring and Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Just the video processor
docker-compose logs -f video-processor

# Just LocalStack
docker-compose logs -f localstack
```

### Access LocalStack Services

LocalStack provides a web interface and CLI tools:

```bash
# List DynamoDB tables
aws dynamodb list-tables --endpoint-url http://localhost:4566 --region us-east-1

# Scan projects table
aws dynamodb scan --table-name easy-video-share-ai-projects-dev --endpoint-url http://localhost:4566 --region us-east-1

# List S3 buckets
aws s3 ls --endpoint-url http://localhost:4566
```

### API Documentation

When the service is running, visit:

- **Interactive API docs**: http://localhost:8080/docs
- **ReDoc documentation**: http://localhost:8080/redoc

## 🛠️ Development Workflow

### Making Changes

1. **Edit the FastAPI app** (`app.py`)
2. **Rebuild the container**:
   ```bash
   docker-compose up --build video-processor
   ```
3. **Test your changes**:
   ```bash
   python test_api.py
   ```

### Adding New Features

1. **Update the Pydantic models** for new request/response schemas
2. **Add new endpoints** following the existing patterns
3. **Update the test script** with new test cases
4. **Test locally** before deploying

### Database Schema Changes

If you need to modify the DynamoDB schema:

1. **Update `init-localstack.sh`** with new table definitions
2. **Restart the stack**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 🚢 Production Deployment

Once local testing is complete, you can deploy to AWS:

1. **Update API keys** in terraform variables
2. **Deploy infrastructure**:
   ```bash
   cd ../  # Back to terraform directory
   terraform plan
   terraform apply
   ```
3. **Build and push Docker image**:
   ```bash
   ./build-and-push.sh
   ```

## 📞 Support

### Common Issues

**Service won't start:**

- Check Docker is running: `docker --version`
- Check ports aren't in use: `netstat -an | grep 8080`

**LocalStack connection errors:**

- Wait for LocalStack to fully start (can take 30-60 seconds)
- Check LocalStack health: `curl http://localhost:4566/health`

**API tests failing:**

- Verify services are healthy: `docker-compose ps`
- Check the logs: `docker-compose logs video-processor`

### Getting Help

1. Check the logs first: `docker-compose logs -f`
2. Verify the configuration in your `.env` file
3. Ensure all required ports are available (8080, 4566)
4. Try restarting: `docker-compose down && docker-compose up -d`

## 🎯 Next Steps

Once local testing is working:

1. **Phase 2**: Integrate real AI APIs (Kling AI, OpenAI)
2. **Phase 3**: Add video compilation and post-processing
3. **Phase 4**: Deploy to AWS ECS
4. **Phase 5**: Connect to Vue.js frontend

Your AI Video Processor foundation is now ready for development! 🎉
