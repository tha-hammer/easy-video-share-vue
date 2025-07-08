# Railway Deployment Steps

This guide provides step-by-step instructions for deploying both frontend and backend to Railway.

## 🚀 **Step 1: Deploy Backend**

### 1.1 Create Backend Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. **Important**: Set **Source Directory** to: `backend`

### 1.2 Configure Backend Environment Variables

Add these variables in your Railway backend project:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# DynamoDB
DYNAMODB_TABLE_NAME=easy-video-share-video-metadata

# Redis Configuration (if using Railway Redis plugin)
REDIS_HOST=your-redis-host
REDIS_PORT=your-redis-port
REDIS_PASSWORD=your-redis-password

# Or use external Redis service
REDIS_URL=redis://your-redis-url:6379/0

# Google AI (optional)
GOOGLE_CLOUD_PROJECT=your-google-project
GOOGLE_CLOUD_LOCATION=us-central1

# Railway-specific (Railway sets these automatically)
RAILWAY_ENVIRONMENT=production
PORT=8000
```

### 1.3 Add Redis Plugin (Recommended)

1. In your backend project, go to "Variables" tab
2. Click "New Variable" → "Plugin"
3. Search for "Redis" and add it
4. Railway will automatically provide `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`

### 1.4 Deploy Backend

1. Click "Deploy" in your backend project
2. Wait for build to complete
3. Note the deployment URL (e.g., `https://your-backend-service.railway.app`)

### 1.5 Test Backend

```bash
# Test health endpoint
curl https://your-backend-service.railway.app/health

# Test AWS configuration
curl https://your-backend-service.railway.app/debug/aws

# Test Redis connection
curl https://your-backend-service.railway.app/debug/redis
```

## 🔄 **Step 1.5: Deploy Celery Worker**

### 1.5.1 Switch to Worker Configuration

**Before deploying the worker, you need to switch the Railway configuration**:

```bash
# Run this script to switch to worker configuration
./scripts/railway-worker.sh
```

This will:

- Backup the current `backend/railway.json`
- Copy `backend/railway.worker.json` to `backend/railway.json`
- Use the worker Dockerfile and configuration

### 1.5.2 Create Worker Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose the **same repository**
5. **Important**: Set **Source Directory** to: `backend`

### 1.5.3 Configure Worker Environment Variables

Add the **same environment variables** as the backend:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-s3-bucket-name
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# DynamoDB
DYNAMODB_TABLE_NAME=easy-video-share-video-metadata

# Redis Configuration (use the same Redis as backend)
REDIS_HOST=your-redis-host
REDIS_PORT=your-redis-port
REDIS_PASSWORD=your-redis-password

# Or use external Redis service
REDIS_URL=redis://your-redis-url:6379/0

# Google AI (optional)
GOOGLE_CLOUD_PROJECT=your-google-project
GOOGLE_CLOUD_LOCATION=us-central1

# Railway-specific
RAILWAY_ENVIRONMENT=production
PORT=8001
```

### 1.5.4 Deploy Worker

1. Click "Deploy" in your worker project
2. Wait for build to complete
3. Note the deployment URL (e.g., `https://your-worker-service.railway.app`)

### 1.5.5 Test Worker

```bash
# Test worker health
curl https://your-worker-service.railway.app/health

# Check worker logs for any errors
# The worker should be processing video tasks
```

### 1.5.6 Switch Back to Backend Configuration (for future deployments)

After deploying the worker, switch back to backend configuration for future backend deployments:

```bash
./scripts/railway-backend.sh
```

## 🎨 **Step 2: Deploy Frontend**

### 2.1 Create Frontend Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose the **same repository**
5. **Important**: Set **Source Directory** to: `.` (root directory)

### 2.2 Configure Frontend Environment Variables

Add these variables in your Railway frontend project:

```bash
# Railway Backend URL (use the URL from Step 1.4)
VITE_AI_VIDEO_BACKEND_URL=https://your-backend-service.railway.app

# AWS Configuration
VITE_AWS_REGION=us-east-1
VITE_AWS_BUCKET_NAME=your-s3-bucket-name
VITE_AWS_ACCESS_KEY_ID=your-aws-access-key
VITE_AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Cognito Configuration
VITE_COGNITO_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=your-user-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id

# Railway-specific
VITE_RAILWAY_ENVIRONMENT=production
VITE_RAILWAY_STATIC_URL=https://your-frontend-service.railway.app
```

### 2.3 Deploy Frontend

1. Click "Deploy" in your frontend project
2. Wait for build to complete
3. Note the deployment URL (e.g., `https://your-frontend-service.railway.app`)

### 2.4 Test Frontend

1. Visit your frontend URL
2. Check browser console for any errors
3. Try uploading a video to test the full pipeline

### 2.5 Alternative: Static File Server (if preview server fails)

If the Vite preview server continues to have issues, you can use the static file server approach:

1. Rename `railway.static.json` to `railway.json`
2. This will build the app and serve static files using `serve` package
3. Redeploy the frontend project

## 🔧 **Step 3: Configuration Management**

### 3.1 Check Current Configuration

To see which Railway configuration is currently active:

```bash
./scripts/railway-status.sh
```

This will show you whether the backend or worker configuration is currently active.

### 3.2 Switch Between Configurations

**For Backend Deployment**:

```bash
./scripts/railway-backend.sh
```

**For Worker Deployment**:

```bash
./scripts/railway-worker.sh
```

### 3.3 Configuration Files

- `backend/railway.json` - Active configuration (switched by scripts)
- `backend/railway.json.backup` - Backup of previous configuration
- `backend/railway.worker.json` - Worker configuration template

## 🔧 **Step 4: Configure CORS (if needed)**

If you encounter CORS errors, update your backend CORS settings in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-service.railway.app",
        "http://localhost:5174",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 **Troubleshooting**

### Backend Issues

- **Build fails**: Check that source directory is set to `backend`
- **Redis connection fails**: Verify Redis plugin is added and variables are set
- **AWS errors**: Check AWS credentials and bucket permissions

### Frontend Issues

- **Build fails**: Check that source directory is set to `.` (root)
- **API calls fail**: Verify `VITE_AI_VIDEO_BACKEND_URL` is correct
- **CORS errors**: Update backend CORS settings
- **Health check fails**: Use static file server approach (`railway.static.json`)

### General Issues

- **Environment variables**: Ensure all required variables are set
- **Port conflicts**: Railway automatically sets `PORT` environment variable
- **Memory issues**: Video processing requires sufficient memory allocation

## 📊 **Monitoring**

### Railway Dashboard

- Monitor CPU and memory usage
- Check deployment logs
- View build status

### Application Health

- Backend: `https://your-backend-service.railway.app/health`
- Frontend: Check browser console and network tab

## 🔄 **Updates**

To update your deployment:

1. Push changes to your GitHub repository
2. Railway will automatically redeploy
3. Monitor the deployment logs for any issues

## 📞 **Support**

- **Railway Issues**: Check Railway documentation and community
- **Application Issues**: Check deployment logs and health endpoints
- **Configuration Issues**: Verify environment variables and CORS settings
