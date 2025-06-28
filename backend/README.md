# Easy Video Share - Backend API

FastAPI backend for AI-powered video processing and sharing platform.

## Features

- **Video Upload**: Direct S3 upload with presigned URLs
- **Video Processing**: Automated video segmentation and text overlay
- **AI Integration**: Google Gemini AI for text generation
- **Task Queue**: Celery with Redis for background processing
- **AWS Integration**: S3 storage and DynamoDB for metadata

## Quick Start

### Prerequisites

- Python 3.8+
- Redis server
- AWS credentials configured
- Google AI API key

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your AWS and Google AI credentials
```

### Development

1. Start Redis server:

```bash
redis-server
```

2. Start the FastAPI development server:

```bash
python run_server.py
```

3. Start Celery worker (in another terminal):

```bash
celery -A backend.tasks worker --loglevel=info
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## API Endpoints

### Sprint 1 - Core Upload

- `POST /api/upload/initiate` - Generate S3 presigned URL for upload
- `POST /api/upload/complete` - Complete upload and start processing
- `GET /api/health` - Health check

## Project Structure

```
backend/
├── __init__.py          # Package initialization
├── main.py             # FastAPI application
├── models.py           # Pydantic data models
├── config.py           # Configuration settings
├── s3_utils.py         # S3 operations
├── tasks.py            # Celery tasks
├── run_server.py       # Development server script
├── run_worker.py       # Celery worker script
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

## Development Notes

This backend is designed to be developed in focused "function chains" as outlined in the project plan. Sprint 1 implements core upload functionality, with subsequent sprints adding video processing, AI features, and status tracking.
