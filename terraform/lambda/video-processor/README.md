# Enhanced Lambda Video Processor with Text Overlay Support

This Lambda function provides comprehensive video processing capabilities with support for text overlays, two-phase processing, and thumbnail generation for the Easy Video Share application.

## Features

### 🎯 Two-Phase Processing Architecture

- **Phase 1**: Process video segments WITHOUT text overlays for fast initial processing
- **Phase 2**: Apply text overlays to processed segments with pixel-perfect positioning
- **Smart Timeout Management**: Automatically switches between Lambda temp storage and S3 storage

### 🎨 Text Overlay Capabilities

- **Fabric.js Integration**: Seamless translation from canvas coordinates to FFmpeg filters
- **Multi-text Support**: Apply multiple text overlays per segment
- **Advanced Styling**: Support for fonts, colors, shadows, and outlines
- **Dynamic Positioning**: Precise coordinate translation for any video resolution

### 🖼️ Thumbnail Generation

- **Design Preview**: Generate thumbnails for text overlay design interface
- **Midpoint Extraction**: Extract frames at segment midpoints for optimal representation
- **S3 Storage**: Automatic thumbnail upload and management

### 🔧 Enhanced Processing Types

- `full_video_processing`: Legacy compatibility for existing workflows
- `segments_without_text`: Phase 1 processing (segments only)
- `apply_text_overlays`: Phase 2 processing (text overlay application)
- `generate_thumbnail`: Thumbnail generation for design interface

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Lambda Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │  Phase 1        │  │  Phase 2        │  │  Thumbnail      │   │
│  │  Segments       │  │  Text Overlays  │  │  Generation     │   │
│  │  Without Text   │  │  Application    │  │                 │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  DynamoDB       │  │  S3 Storage     │  │  FFmpeg         │
│  Segments       │  │  Temp/Final     │  │  Processing     │
│  Metadata       │  │  Videos         │  │  Engine         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Deployment Methods

### Method 1: Terraform Deployment (Recommended)

1. **Prerequisites**:

   ```bash
   # Install Terraform
   terraform --version

   # Configure AWS credentials
   aws configure
   ```

2. **Deploy Infrastructure**:

   ```bash
   cd terraform/
   terraform init
   terraform plan
   terraform apply
   ```

3. **Verify Deployment**:

   ```bash
   # Check Lambda function
   aws lambda get-function --function-name easy-video-share-video-processor

   # Check DynamoDB tables
   aws dynamodb list-tables
   ```

### Method 2: CLI Deployment

1. **Prerequisites**:

   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Install 7-Zip for packaging
   # Windows: Download from https://www.7-zip.org/
   ```

2. **Deploy Function**:

   ```bash
   cd terraform/lambda/video-processor/
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Verify Deployment**:
   The script will automatically run tests for all processing types.

## Configuration

### Environment Variables

```bash
# Required
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=easy-video-share-bucket

# Lambda Processing
USE_LAMBDA_PROCESSING=true
LAMBDA_FUNCTION_NAME=easy-video-share-video-processor

# DynamoDB Tables
DYNAMODB_VIDEO_METADATA_TABLE=easy-video-share-video-metadata
DYNAMODB_VIDEO_SEGMENTS_TABLE=easy-video-share-video-segments
```

### DynamoDB Tables

#### Video Segments Table

```json
{
  "TableName": "easy-video-share-video-segments",
  "KeySchema": [
    {
      "AttributeName": "segment_id",
      "KeyType": "HASH"
    }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "VideoIndex",
      "KeySchema": [
        { "AttributeName": "video_id", "KeyType": "HASH" },
        { "AttributeName": "segment_number", "KeyType": "RANGE" }
      ]
    }
  ]
}
```

## Usage Examples

### Phase 1: Process Segments Without Text

```python
# Backend endpoint
POST /videos/{video_id}/process-segments-without-text

# Request
{
  "segments": [
    {"start": 0, "end": 30},
    {"start": 30, "end": 60}
  ],
  "textData": {
    "strategy": "ONE_FOR_ALL",
    "content": {"oneForAll": "Subscribe Now!"}
  }
}

# Lambda payload
{
  "processing_type": "segments_without_text",
  "video_id": "video_123",
  "video_s3_key": "uploads/video_123.mp4",
  "segments": [
    {"start": 0, "end": 30},
    {"start": 30, "end": 60}
  ]
}
```

### Phase 2: Apply Text Overlays

```python
# Backend endpoint
POST /segments/{segment_id}/process-with-text-overlays

# Request
{
  "overlays": [
    {
      "text": "Subscribe Now!",
      "x": 100,
      "y": 100,
      "fontSize": 32,
      "color": "#ffffff",
      "fontFamily": "Arial"
    }
  ]
}

# Lambda payload
{
  "processing_type": "apply_text_overlays",
  "video_id": "video_123",
  "text_overlays": [
    {
      "segment_id": "seg_video_123_001",
      "text": "Subscribe Now!",
      "x": 100,
      "y": 100,
      "fontSize": 32,
      "color": "#ffffff"
    }
  ]
}
```

### Thumbnail Generation

```python
# Backend endpoint
POST /segments/{segment_id}/generate-thumbnail

# Lambda payload
{
  "processing_type": "generate_thumbnail",
  "video_id": "video_123",
  "segment_id": "seg_video_123_001"
}
```

## API Endpoints

### Enhanced Backend Endpoints

| Endpoint                                            | Method | Description                            |
| --------------------------------------------------- | ------ | -------------------------------------- |
| `/videos/{video_id}/process-segments-without-text`  | POST   | Phase 1: Process segments without text |
| `/segments/{segment_id}/process-with-text-overlays` | POST   | Phase 2: Apply text overlays           |
| `/segments/{segment_id}/generate-thumbnail`         | POST   | Generate segment thumbnail             |
| `/videos/{video_id}/segments-status`                | GET    | Check segment processing status        |
| `/videos/{video_id}/save-text-data`                 | POST   | Save text data for later use           |
| `/videos/{video_id}/text-data`                      | GET    | Retrieve saved text data               |

### Lambda Processing Types

| Processing Type         | Description                       | Invocation |
| ----------------------- | --------------------------------- | ---------- |
| `full_video_processing` | Legacy full video processing      | Async      |
| `segments_without_text` | Phase 1: Segment generation       | Async      |
| `apply_text_overlays`   | Phase 2: Text overlay application | Async      |
| `generate_thumbnail`    | Thumbnail generation              | Sync       |

## Testing

### Automated Tests

```bash
# Run all tests
cd terraform/lambda/video-processor/
./deploy.sh

# The script will run:
# - Basic connectivity test
# - Segments without text test
# - Thumbnail generation test
```

### Manual Testing

1. **Test Phase 1 Processing**:

   ```bash
   aws lambda invoke \
     --function-name easy-video-share-video-processor \
     --payload '{"processing_type":"segments_without_text","video_id":"test","video_s3_key":"test.mp4","segments":[{"start":0,"end":30}]}' \
     test-response.json
   ```

2. **Test Thumbnail Generation**:

   ```bash
   aws lambda invoke \
     --function-name easy-video-share-video-processor \
     --payload '{"processing_type":"generate_thumbnail","video_id":"test","segment_id":"seg_test_001"}' \
     thumbnail-response.json
   ```

3. **Test Text Overlay Application**:
   ```bash
   aws lambda invoke \
     --function-name easy-video-share-video-processor \
     --payload '{"processing_type":"apply_text_overlays","video_id":"test","text_overlays":[{"segment_id":"seg_test_001","text":"Hello","x":100,"y":100}]}' \
     overlay-response.json
   ```

## Monitoring

### CloudWatch Logs

```bash
# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/easy-video-share-video-processor"

# Stream logs
aws logs tail /aws/lambda/easy-video-share-video-processor --follow
```

### DynamoDB Monitoring

```bash
# Check segments table
aws dynamodb scan --table-name easy-video-share-video-segments --max-items 10

# Query segments by video ID
aws dynamodb query \
  --table-name easy-video-share-video-segments \
  --index-name VideoIndex \
  --key-condition-expression "video_id = :vid" \
  --expression-attribute-values '{":vid":{"S":"video_123"}}'
```

## Troubleshooting

### Common Issues

1. **Lambda Timeout**: Check processing duration and adjust timeout settings
2. **Memory Issues**: Increase Lambda memory allocation for large videos
3. **S3 Permissions**: Ensure Lambda has proper S3 read/write permissions
4. **DynamoDB Access**: Verify DynamoDB table permissions

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export DEBUG_LAMBDA_PROCESSING=true
```

## Development

### Local Development

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run Tests**:

   ```bash
   python test_lambda_function.py
   ```

3. **Package for Deployment**:
   ```bash
   zip -r lambda-function.zip lambda_function.py utils/
   ```

### Contributing

1. Make changes to `lambda_function.py`
2. Test locally with sample events
3. Deploy using either Terraform or CLI method
4. Verify all processing types work correctly
5. Update documentation as needed

## Performance Optimization

### Memory and Timeout Settings

- **Memory**: 3008 MB (maximum for optimal performance)
- **Timeout**: 900 seconds (15 minutes)
- **Ephemeral Storage**: 10 GB for large video processing

### Best Practices

1. **Segment Size**: Optimize for 30-60 second segments
2. **Concurrent Processing**: Use async invocations for multiple segments
3. **Temp Storage**: Monitor Lambda storage usage for long processing
4. **S3 Lifecycle**: Configure S3 lifecycle rules for temp files

## Security

### IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::easy-video-share-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/easy-video-share-video-segments",
        "arn:aws:dynamodb:*:*:table/easy-video-share-video-segments/*"
      ]
    }
  ]
}
```

## Support

For issues, questions, or feature requests, please refer to the main project documentation or create an issue in the repository.

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**Compatibility**: AWS Lambda Python 3.11, FFmpeg 4.4+
