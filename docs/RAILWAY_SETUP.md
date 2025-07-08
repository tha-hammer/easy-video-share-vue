# Railway Deployment Setup

## Environment Variables Required

You need to set the following environment variables in your Railway frontend project:

### Frontend Environment Variables (Railway Frontend Service)

```bash
# Railway Backend URL - Replace with your actual Railway backend URL
VITE_AI_VIDEO_BACKEND_URL=https://your-backend-service-name.railway.app

# AWS Configuration (if using AWS services)
VITE_AWS_REGION=us-east-1
VITE_AWS_BUCKET_NAME=your-s3-bucket-name
VITE_AWS_ACCESS_KEY_ID=your-access-key
VITE_AWS_SECRET_ACCESS_KEY=your-secret-key

# Cognito Configuration (if using AWS Cognito)
VITE_COGNITO_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=your-user-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id
```

## How to Set Environment Variables in Railway

1. Go to your Railway dashboard
2. Select your frontend project
3. Go to the "Variables" tab
4. Add each environment variable with its corresponding value

## Backend URL Format

Your Railway backend URL will typically be in this format:

```
https://your-service-name.railway.app
```

For example:

```
https://easy-video-share-backend.railway.app
```

## Testing the Connection

After setting the environment variables:

1. Deploy your frontend to Railway
2. Try uploading a video
3. Check the browser's developer console for any errors
4. The API calls should now go to your Railway backend instead of localhost

## Troubleshooting

If you still see the "Unexpected token '<'" error:

1. Check that `VITE_AI_VIDEO_BACKEND_URL` is set correctly
2. Verify your backend is running and accessible
3. Check that your backend endpoints match the expected paths:
   - `/api/upload/initiate`
   - `/api/upload/complete`
   - `/api/video/analyze-duration`
4. Ensure CORS is properly configured on your backend
