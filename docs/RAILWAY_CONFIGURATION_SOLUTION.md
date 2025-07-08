# Railway Configuration Solution

## The Problem You Identified

You correctly identified that having both the FastAPI backend and Celery worker use the same `railway.json` file would create confusion about which service is being deployed.

## The Solution: Configuration Management Scripts

We've created a system that allows you to **switch between configurations** before deploying each service.

### How It Works

1. **Two Configuration Files**:

   - `backend/railway.json` - FastAPI Backend configuration
   - `backend/railway.worker.json` - Celery Worker configuration

2. **Active Configuration**:

   - Only `backend/railway.json` is used by Railway
   - The scripts copy the appropriate configuration to this file

3. **Management Scripts**:
   - `./scripts/railway-status.sh` - Check which configuration is active
   - `./scripts/railway-backend.sh` - Switch to backend configuration
   - `./scripts/railway-worker.sh` - Switch to worker configuration

## Deployment Workflow

### Step 1: Deploy Backend

```bash
# 1. Switch to backend configuration
./scripts/railway-backend.sh

# 2. Deploy to Railway with Source Directory: backend
# 3. Railway uses backend/railway.json (FastAPI config)
```

### Step 2: Deploy Worker

```bash
# 1. Switch to worker configuration
./scripts/railway-worker.sh

# 2. Deploy to Railway with Source Directory: backend
# 3. Railway uses backend/railway.json (Worker config)
```

### Step 3: Switch Back (for future deployments)

```bash
# Switch back to backend configuration for future backend updates
./scripts/railway-backend.sh
```

## Configuration Files Explained

### Backend Configuration (`backend/railway.json`)

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```

### Worker Configuration (`backend/railway.worker.json`)

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.worker"
  },
  "deploy": {
    "startCommand": "python worker_health.py",
    "healthcheckPath": "/health"
  }
}
```

## Key Benefits

1. **Clear Separation**: No confusion about which service is being deployed
2. **Easy Management**: Simple scripts to switch configurations
3. **Backup Safety**: Previous configuration is backed up automatically
4. **Status Checking**: Always know which configuration is active

## Verification

### Check Current Configuration

```bash
./scripts/railway-status.sh
```

Output examples:

```
✅ Current configuration: FastAPI Backend
   - Handles API requests and dispatches Celery tasks
   - Uses Dockerfile (not Dockerfile.worker)
   - Start command: uvicorn main:app
```

```
✅ Current configuration: Celery Worker
   - Processes videos in the background
   - Uses Dockerfile.worker
   - Start command: python worker_health.py
```

## Service Communication

```
Frontend → Backend API → Redis → Celery Worker
                ↓
            SSE Stream ← Redis ← Worker Progress
```

Both services need the same environment variables (especially Redis configuration) to communicate properly.

## Environment Variables

Both services need identical environment variables:

```bash
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

**Worker-specific**:

```bash
PORT=8001  # Different port to avoid conflicts
```

This solution ensures you always know which service you're deploying and eliminates configuration confusion.
