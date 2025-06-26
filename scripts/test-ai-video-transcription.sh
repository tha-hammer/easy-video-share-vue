#!/bin/bash

# Test script for AI Video Transcription functionality
# This script tests the real AWS Transcribe integration

echo "🧪 Testing AI Video Transcription Functionality"
echo ""

# Configuration
PROJECT_ROOT=$(pwd)
API_URL=$(cd terraform && terraform output -raw api_gateway_endpoint 2>/dev/null)

if [ -z "$API_URL" ]; then
    echo "❌ Could not get API Gateway URL. Please deploy first with:"
    echo "   ./scripts/deploy-ai-video.sh"
    exit 1
fi

echo "🌐 API Gateway URL: $API_URL"
echo "🎯 AI Video endpoint: $API_URL/ai-video"
echo ""

# Check if we have authentication token
if [ ! -f ".auth_token" ]; then
    echo "⚠️  No authentication token found."
    echo "   Please run: ./scripts/get-auth-token.sh"
    echo "   Or manually create a .auth_token file with your JWT token"
    exit 1
fi

# Read auth token
AUTH_TOKEN=$(cat .auth_token | tr -d '\n\r')
echo "✅ Using auth token: ${AUTH_TOKEN:0:50}..."
echo ""

# Test 1: Check if AI video endpoint is accessible
echo "🔍 Test 1: Checking AI video endpoint accessibility..."
OPTIONS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "$API_URL/ai-video" \
    -H "Content-Type: application/json")

if [ "$OPTIONS_RESPONSE" = "200" ] || [ "$OPTIONS_RESPONSE" = "204" ]; then
    echo "✅ AI video endpoint is accessible (CORS preflight successful)"
else
    echo "❌ AI video endpoint not accessible (HTTP $OPTIONS_RESPONSE)"
    echo "   This might indicate the Lambda function is not deployed correctly"
    exit 1
fi

# Test 2: Check for available audio files
echo ""
echo "🔍 Test 2: Checking for available audio files..."

# Get audio files
AUDIO_RESPONSE=$(curl -s -X GET "$API_URL/audio" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $AUTH_TOKEN")

if [ $? -eq 0 ]; then
    echo "✅ Audio endpoint is accessible"
    
    # Count audio files (simple grep approach without jq)
    AUDIO_COUNT=$(echo "$AUDIO_RESPONSE" | grep -o '"audio_id"' | wc -l)
    
    if [ "$AUDIO_COUNT" -gt 0 ]; then
        echo "📁 Found $AUDIO_COUNT audio files"
        
        # Get first audio ID (simple extraction without jq)
        FIRST_AUDIO_ID=$(echo "$AUDIO_RESPONSE" | grep -o '"audio_id":"[^"]*"' | head -1 | cut -d'"' -f4)
        
        if [ -n "$FIRST_AUDIO_ID" ]; then
            echo "🎵 Using audio ID: $FIRST_AUDIO_ID"
            
            # Test 3: Start AI video generation
            echo ""
            echo "🔍 Test 3: Starting AI video generation..."
            
            GENERATION_REQUEST=$(cat << EOF
{
    "audioId": "$FIRST_AUDIO_ID",
    "prompt": "Create a dynamic vertical video with urban backgrounds and modern aesthetics",
    "targetDuration": 30,
    "style": "cinematic"
}
EOF
)
            
            GENERATION_RESPONSE=$(curl -s -X POST "$API_URL/ai-video" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $AUTH_TOKEN" \
                -d "$GENERATION_REQUEST")
            
            if [ $? -eq 0 ]; then
                echo "✅ AI video generation request sent successfully"
                echo "📋 Response: $GENERATION_RESPONSE"
                
                # Extract video ID (simple extraction without jq)
                VIDEO_ID=$(echo "$GENERATION_RESPONSE" | grep -o '"videoId":"[^"]*"' | cut -d'"' -f4)
                
                if [ -n "$VIDEO_ID" ]; then
                    echo "🎬 Video ID: $VIDEO_ID"
                    
                    # Test 4: Check generation status
                    echo ""
                    echo "🔍 Test 4: Checking generation status..."
                    
                    STATUS_RESPONSE=$(curl -s -X GET "$API_URL/ai-video/$VIDEO_ID" \
                        -H "Content-Type: application/json" \
                        -H "Authorization: Bearer $AUTH_TOKEN")
                    
                    if [ $? -eq 0 ]; then
                        echo "✅ Status check successful"
                        echo "📋 Status response: $STATUS_RESPONSE"
                        
                        # Check if transcription is in progress
                        if echo "$STATUS_RESPONSE" | grep -q "transcription"; then
                            echo "🎤 Transcription step detected in processing"
                        fi
                        
                        if echo "$STATUS_RESPONSE" | grep -q "processing"; then
                            echo "⚡ AI processing is active"
                        fi
                        
                    else
                        echo "❌ Status check failed"
                    fi
                else
                    echo "❌ Could not extract video ID from response"
                fi
            else
                echo "❌ AI video generation request failed"
            fi
        else
            echo "❌ Could not extract audio ID from response"
        fi
    else
        echo "⚠️  No audio files found. Please upload an audio file first."
        echo "   You can do this through the web interface."
    fi
else
    echo "❌ Audio endpoint not accessible"
fi

echo ""
echo "🧪 Transcription test completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Check CloudWatch logs for detailed transcription progress"
echo "   2. Verify transcription results in DynamoDB"
echo "   3. Test with different audio file types"
echo "   4. Proceed to Step 2: Scene Planning with OpenAI GPT-4" 