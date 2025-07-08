# Railway Deployment Guide

This guide covers deploying the Easy Video Share application to Railway, including both frontend and backend services.

## 🚀 **Quick Start**

### 1. **Backend Deployment (FastAPI)**

1. **Create a new Railway project**
2. **Connect your GitHub repository**
3. **Set the source directory to `backend`**
4. **Configure environment variables (see below)**
5. **Deploy**

### 2. **Frontend Deployment (Vue.js)**

1. **Create a separate Railway project for frontend**
2. **Connect the same GitHub repository**
3. **Set the source directory to root (`.`)**
4. **Configure environment variables (see below)**
5. **Deploy**

## 🔧 **Environment Variables**

### **Backend Environment Variables**

Set these in your Railway backend project:

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

# Google AI (for text generation)
GOOGLE_CLOUD_PROJECT=your-google-project
GOOGLE_CLOUD_LOCATION=us-central1

# Railway-specific
RAILWAY_ENVIRONMENT=production
PORT=8000
```

### **Frontend Environment Variables**

Set these in your Railway frontend project:

```bash
# Railway Backend URL (get this from your backend deployment)
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

## 🗄️ **Redis Setup**

### **Option 1: Railway Redis Plugin (Recommended)**

1. Add the Redis plugin to your backend project
2. Railway will automatically provide `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`
3. The backend will automatically construct the `REDIS_URL`

### **Option 2: External Redis Service**

Use a service like Upstash, Redis Cloud, or AWS ElastiCache:

```bash
REDIS_URL=redis://username:password@host:port/0
```

### **Option 3: Railway Redis Service**

Create a separate Railway project for Redis:

1. Create a new Railway project
2. Add the Redis plugin
3. Get the connection details and add them to your backend project

## 🔍 **Health Checks**

The backend includes health check endpoints:

- `GET /health` - Basic health check
- `GET /debug/aws` - AWS configuration test
- `GET /debug/redis` - Redis connection test
- `GET /debug/ffmpeg` - FFmpeg installation test

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Redis Connection Failed**

   - Ensure Redis is properly configured
   - Check `REDIS_URL` or `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`
   - Test with `/debug/redis` endpoint

2. **AWS Credentials Invalid**

   - Verify AWS credentials are set correctly
   - Check S3 bucket permissions
   - Test with `/debug/aws` endpoint

3. **FFmpeg Not Available**

   - The Dockerfile includes FFmpeg installation
   - Test with `/debug/ffmpeg` endpoint
   - Check build logs for installation errors

4. **CORS Issues**

   - Ensure frontend URL is allowed in backend CORS settings
   - Check browser console for CORS errors

5. **Video Processing Fails**
   - Check Celery worker logs
   - Verify Redis connection
   - Ensure sufficient memory allocation

### **Logs and Debugging**

1. **Backend Logs**: Check Railway deployment logs
2. **Frontend Logs**: Check browser console
3. **Redis Logs**: Check Redis service logs
4. **Build Logs**: Check Railway build process

## 📊 **Resource Allocation**

### **Backend Requirements**

- **Memory**: Minimum 2GB (4GB recommended for video processing)
- **CPU**: 2 vCPU minimum
- **Storage**: 10GB minimum for temporary video files

### **Frontend Requirements**

- **Memory**: 512MB minimum
- **CPU**: 1 vCPU minimum
- **Storage**: 1GB minimum

## 🔄 **CI/CD Setup**

### **Automatic Deployments**

Railway automatically deploys on:

- Push to main branch
- Pull request creation/updates
- Manual deployment trigger

### **Environment-Specific Deployments**

1. **Development**: Deploy from `develop` branch
2. **Staging**: Deploy from `staging` branch
3. **Production**: Deploy from `main` branch

## 🔒 **Security Considerations**

1. **Environment Variables**: Never commit sensitive data
2. **AWS Credentials**: Use IAM roles with minimal permissions
3. **Redis Security**: Use password-protected Redis instances
4. **CORS**: Restrict to specific domains in production

## 📈 **Monitoring**

### **Railway Metrics**

- CPU usage
- Memory usage
- Network traffic
- Response times

### **Application Metrics**

- Video processing success rate
- API response times
- Error rates
- User activity

## 🚀 **Production Checklist**

- [ ] All environment variables configured
- [ ] Redis service running and accessible
- [ ] AWS credentials with proper permissions
- [ ] CORS settings configured for production domains
- [ ] Health checks passing
- [ ] Video processing tested
- [ ] Frontend-backend communication verified
- [ ] Error monitoring configured
- [ ] Backup strategy in place

## 📞 **Support**

For Railway-specific issues:

- Check Railway documentation
- Review Railway community forums
- Contact Railway support

For application-specific issues:

- Check application logs
- Review error messages
- Test with debug endpoints
