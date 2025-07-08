# Railway Deployment Guide - Three Service Setup

## Overview

This project has three separate services that need to be deployed to Railway:

1. **Frontend** (Vue.js) - Static web application
2. **Backend API** (FastAPI) - REST API service
3. **Worker** (Celery) - Background task processor

## Service Configurations

### 1. Frontend Service

- **Configuration File**: `railway.json` (root directory)
- **Build Method**: Nixpacks (automatic Node.js detection)
- **Start Command**: `npm run preview`
- **Health Check**: `/health.html`

### 2. Backend API Service

- **Configuration File**: `railway.backend.json` (root directory)
- **Build Method**: Docker using `backend/Dockerfile`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/health`

### 3. Worker Service

- **Configuration File**: `railway.worker.json` (root directory)
- **Build Method**: Docker using `backend/Dockerfile.worker`
- **Start Command**: `celery -A tasks worker --loglevel=info --pool=solo`
- **Health Check**: `/health`

## Deployment Steps

### Step 1: Deploy Frontend Service

```bash
# Navigate to project root
cd /path/to/easy-video-share-vue

# Deploy frontend service
railway link
railway up --service frontend
```

### Step 2: Deploy Backend API Service

```bash
# Deploy backend API service
railway up --service backend-api
```

### Step 3: Deploy Worker Service

```bash
# Deploy worker service
railway up --service worker
```

## Environment Variables

Each service needs specific environment variables. Set these in Railway dashboard:

### Frontend Service

- `VITE_API_URL` - URL of your backend API service
- `VITE_WS_URL` - WebSocket URL for real-time updates

### Backend API Service

- `REDIS_URL` - Redis connection string
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region
- `S3_BUCKET_NAME` - S3 bucket for video storage
- `DYNAMODB_TABLE_NAME` - DynamoDB table name

### Worker Service

- `REDIS_URL` - Redis connection string (same as backend)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region
- `S3_BUCKET_NAME` - S3 bucket for video storage
- `DYNAMODB_TABLE_NAME` - DynamoDB table name

## Service Communication

- **Frontend** → **Backend API**: HTTP requests for video uploads and status
- **Backend API** → **Worker**: Celery task queue via Redis
- **Worker** → **Frontend**: Server-Sent Events (SSE) for progress updates

## Troubleshooting

### Common Issues

1. **Dockerfile not found**: Ensure you're using the correct configuration file for each service
2. **Build failures**: Check that all dependencies are properly specified
3. **Service communication**: Verify environment variables are set correctly
4. **Health check failures**: Ensure health check endpoints are working

### Verification Commands

```bash
# Check service status
railway status

# View logs
railway logs --service frontend
railway logs --service backend-api
railway logs --service worker

# Test health endpoints
curl https://your-frontend-url.railway.app/health.html
curl https://your-backend-url.railway.app/health
curl https://your-worker-url.railway.app/health
```

## Important Notes

- Each service runs independently and can be scaled separately
- The worker service processes video uploads asynchronously
- Redis is used as the message broker between backend and worker
- All services should be deployed before testing the complete workflow
