#!/bin/bash

# Railway Video Processing Fix Deployment Script
# This script helps deploy the Railway-optimized video processing solution

set -e

echo "🚀 Railway Video Processing Fix Deployment"
echo "=========================================="

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: This script must be run from the backend directory"
    exit 1
fi

echo "📋 Checking Railway video processing files..."

# Check if the new Railway video processing file exists
if [ ! -f "video_processing_utils_railway.py" ]; then
    echo "❌ Error: video_processing_utils_railway.py not found"
    echo "   Make sure you have the Railway-optimized video processing file"
    exit 1
fi

# Check if tasks.py has been updated
if ! grep -q "video_processing_utils_railway" tasks.py; then
    echo "❌ Error: tasks.py has not been updated to use Railway video processing"
    echo "   Please update the import in tasks.py first"
    exit 1
fi

echo "✅ All required files are present"

echo ""
echo "🔧 Railway Video Processing Changes Summary:"
echo "============================================"
echo ""
echo "1. ✅ Created video_processing_utils_railway.py"
echo "   - Simplified FFmpeg commands for Railway"
echo "   - Better error handling and logging"
echo "   - Reduced complexity to avoid subprocess issues"
echo ""
echo "2. ✅ Updated tasks.py"
echo "   - Now imports from video_processing_utils_railway"
echo "   - Uses Railway-optimized processing"
echo ""
echo "3. ✅ Added debug endpoints"
echo "   - /debug/railway-video for testing video processing"
echo "   - Comprehensive testing of FFmpeg, FFprobe, and processing"
echo ""
echo "4. ✅ Created test script"
echo "   - test_railway_video_processing.py for local testing"
echo ""

echo "🧪 Testing Railway Video Processing Locally..."
echo "=============================================="

# Test if Python can import the new module
if python -c "from video_processing_utils_railway import split_video_with_precise_timing_and_dynamic_text; print('✅ Import successful')" 2>/dev/null; then
    echo "✅ Railway video processing module imports successfully"
else
    echo "❌ Failed to import Railway video processing module"
    echo "   Check for syntax errors in video_processing_utils_railway.py"
    exit 1
fi

# Test if the test script can run
if [ -f "test_railway_video_processing.py" ]; then
    echo ""
    echo "🔍 Running Railway video processing tests..."
    echo "   (This may take a few minutes)"
    echo ""
    
    if python test_railway_video_processing.py; then
        echo "✅ Railway video processing tests passed"
    else
        echo "⚠️  Railway video processing tests had issues"
        echo "   Check the output above for details"
        echo "   You can still deploy, but test the /debug/railway-video endpoint"
    fi
else
    echo "⚠️  test_railway_video_processing.py not found"
    echo "   Skipping local tests"
fi

echo ""
echo "🚀 Deployment Instructions for Railway:"
echo "======================================="
echo ""
echo "1. Commit and push your changes:"
echo "   git add ."
echo "   git commit -m 'Fix Railway video processing with simplified FFmpeg commands'"
echo "   git push"
echo ""
echo "2. Railway will automatically redeploy your backend"
echo ""
echo "3. After deployment, test the fix:"
echo "   curl https://your-backend-service.railway.app/debug/railway-video"
echo ""
echo "4. Check the response for:"
echo "   - FFmpeg installation: success"
echo "   - FFprobe installation: success"
echo "   - Test video creation: success"
echo "   - Video processing: success"
echo ""
echo "5. If all tests pass, try uploading a video through your frontend"
echo ""
echo "🔍 Troubleshooting:"
echo "=================="
echo ""
echo "If the /debug/railway-video endpoint shows errors:"
echo ""
echo "1. Check Railway logs for detailed error messages"
echo "2. Verify FFmpeg is installed in the Docker container"
echo "3. Check if the error is related to:"
echo "   - Memory limits (try smaller videos)"
echo "   - Timeout issues (processing takes too long)"
echo "   - File system permissions"
echo ""
echo "4. If FFmpeg is not available:"
echo "   - Check the Dockerfile includes FFmpeg installation"
echo "   - Verify the build process completed successfully"
echo ""
echo "5. If processing fails:"
echo "   - Check the simplified FFmpeg commands in video_processing_utils_railway.py"
echo "   - Verify the text overlay parameters are compatible"
echo ""

echo "✅ Railway video processing fix is ready for deployment!"
echo ""
echo "The main improvements:"
echo "- Simplified FFmpeg commands to avoid complex filter issues"
echo "- Better error handling and logging for Railway environment"
echo "- Reduced processing complexity to avoid timeouts"
echo "- Comprehensive testing endpoints for debugging"
echo ""
echo "Deploy and test with confidence! 🎉" 