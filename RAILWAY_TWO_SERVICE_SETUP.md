# Railway Two-Service Deployment Guide

## Overview

This project requires **two separate Railway services**:

1. **FastAPI Backend** - Handles API requests, file uploads, and dispatches Celery tasks
2. **Celery Worker** - Processes videos in the background

## Service 1: FastAPI Backend

### Setup Steps:

1. Go to [Railway.app](https://railway.app) and create a new project
2. Connect to your GitHub repository
3. **Important**: Set "Source Directory" to: `backend`
4. Railway will automatically detect `backend/railway.json` and use it
5. Add environment variables (see below)
6. Deploy

### Environment Variables for Backend:

```
AWS_REGION=your-aws-region
AWS_BUCKET_NAME=your-s3-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
DYNAMODB_TABLE_NAME=your-dynamodb-table
REDIS_URL=your-redis-url
GOOGLE_CLOUD_PROJECT=your-gcp-project (optional)
GOOGLE_CLOUD_LOCATION=your-gcp-location (optional)
RAILWAY_ENVIRONMENT=production
```

### Backend Service URL:

- Will be something like: `https://your-backend-service.up.railway.app`
- This is your **API_BASE_URL** for the frontend

## Service 2: Celery Worker

### Setup Steps:

1. In the same Railway project, click "New Service"
2. Choose "GitHub Repo" again
3. **Important**: Set "Source Directory" to: `backend`
4. **Critical**: Before deploying, rename the config file:
   ```bash
   # In the backend directory:
   mv railway.worker.json railway.json
   ```
5. Add the **same environment variables** as the backend
6. Deploy

### Environment Variables for Worker:

```
# Same as backend, plus:
PORT=8001  # Different port to avoid conflicts
```

### Worker Service URL:

- Will be something like: `https://your-worker-service.up.railway.app`
- Used for health checks only

## Deployment Scripts

### For Backend Deployment:

```bash
# Ensure backend config is active
cd backend
cp railway.json railway.backend.json
rm railway.json
cp railway.backend.json railway.json
```

### For Worker Deployment:

```bash
# Switch to worker config
cd backend
cp railway.worker.json railway.json
```

## Verification

### Test Backend:

```bash
curl https://your-backend-service.up.railway.app/health
```

### Test Worker:

```bash
curl https://your-worker-service.up.railway.app/health
```

### Test Video Processing:

1. Upload a video through the frontend
2. Check that the job gets queued (backend logs)
3. Check that the worker processes it (worker logs)
4. Verify SSE progress updates work

## Troubleshooting

### Common Issues:

1. **Worker not processing jobs**:

   - Check Redis connection in both services
   - Verify environment variables are identical
   - Check worker logs for errors

2. **SSE connection fails**:

   - Ensure backend service is running
   - Check CORS settings
   - Verify Redis is accessible

3. **Video processing fails**:
   - Check FFmpeg installation in worker
   - Verify AWS credentials in worker
   - Check S3 bucket permissions

### Logs to Monitor:

- **Backend logs**: API requests, task dispatching
- **Worker logs**: Video processing, progress updates
- **Redis logs**: Message queuing and delivery

## Service Communication

```
Frontend → Backend API → Redis → Celery Worker
                ↓
            SSE Stream ← Redis ← Worker Progress
```

The backend and worker communicate through Redis, so both services need the same Redis configuration.
