#!/bin/bash

# Get Auth Token Script for Git Bash
# This script helps you get an authentication token for testing

echo "🔑 Get Authentication Token for Testing"
echo ""

# Get API Gateway URL
PROJECT_ROOT=$(pwd)
API_URL=$(cd terraform && terraform output -raw api_gateway_endpoint 2>/dev/null)
cd "$PROJECT_ROOT"

if [ -z "$API_URL" ]; then
    echo "❌ Could not get API Gateway URL. Please deploy first."
    exit 1
fi

echo "🌐 API Gateway URL: $API_URL"
echo ""

# Check if user wants to use existing credentials
echo "Choose an option:"
echo "1. Use existing user credentials"
echo "2. Create a new test user"
echo "3. Get token from browser (manual)"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Enter existing user credentials:"
        read -p "Email: " email
        read -s -p "Password: " password
        echo ""
        
        echo ""
        echo "🔐 Attempting to get auth token..."
        
        # Create temporary JSON file
        cat > /tmp/login.json << EOF
{
    "email": "$email",
    "password": "$password"
}
EOF
        
        # Make login request
        response=$(curl -s -X POST "$API_URL/auth/login" \
            -H "Content-Type: application/json" \
            -d @/tmp/login.json)
        
        # Clean up temp file
        rm -f /tmp/login.json
        
        # Extract token
        token=$(echo "$response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$token" ]; then
            echo "$token" > .auth_token
            echo "✅ Auth token saved to .auth_token"
            echo "Token: ${token:0:50}..."
        else
            echo "❌ Login failed: $response"
        fi
        ;;
        
    2)
        echo ""
        echo "Creating a new test user..."
        read -p "Email for new user: " email
        read -s -p "Password for new user: " password
        echo ""
        
        echo ""
        echo "🔐 Creating user and getting auth token..."
        
        # Create temporary JSON file
        cat > /tmp/register.json << EOF
{
    "email": "$email",
    "password": "$password"
}
EOF
        
        # Make registration request
        response=$(curl -s -X POST "$API_URL/auth/register" \
            -H "Content-Type: application/json" \
            -d @/tmp/register.json)
        
        # Clean up temp file
        rm -f /tmp/register.json
        
        # Extract token
        token=$(echo "$response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$token" ]; then
            echo "$token" > .auth_token
            echo "✅ User created and auth token saved to .auth_token"
            echo "Token: ${token:0:50}..."
        else
            echo "❌ Registration failed: $response"
        fi
        ;;
        
    3)
        echo ""
        echo "📋 Manual token extraction instructions:"
        echo "1. Open your browser and go to the application"
        echo "2. Open Developer Tools (F12)"
        echo "3. Go to Network tab"
        echo "4. Log in to the application"
        echo "5. Look for the login request in the Network tab"
        echo "6. Copy the Authorization header value (starts with 'Bearer ')"
        echo "7. Remove 'Bearer ' prefix and save just the token"
        echo ""
        
        read -p "Paste the token here (without 'Bearer ' prefix): " manual_token
        if [ -n "$manual_token" ]; then
            echo "$manual_token" > .auth_token
            echo "✅ Auth token saved to .auth_token"
        fi
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Auth token setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Run the test script: ./scripts/test-ai-video-transcription.sh"
echo "2. Or test manually with curl" 