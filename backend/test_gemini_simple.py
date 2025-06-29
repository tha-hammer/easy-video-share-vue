"""
Simple Vertex AI Connection Test Script
Quick verification of Vertex AI Gemini setup without full Sprint 4 testing
"""

import os
import sys

def test_vertexai_simple():
    """Simple test of Vertex AI connection"""
    
    print("Simple Vertex AI Connection Test")
    print("=" * 40)
    
    # Check environment variables
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT environment variable not found")
        print("Please add GOOGLE_CLOUD_PROJECT to your .env file")
        return False
    
    print(f"✅ Project ID found: {project_id}")
    print(f"✅ Location: {location}")
    
    try:
        # Import and configure Vertex AI
        from google import genai
        from google.genai.types import HttpOptions
        
        client = genai.Client(
            project=project_id,
            location=location,
            vertexai=True,
            http_options=HttpOptions(api_version="v1")
        )
        
        print("✅ Vertex AI client configured successfully")
        
        # Simple test call
        print("🔄 Testing API call...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say exactly: 'API test successful'"
        )
        
        if response.text and "API test successful" in response.text:
            print("✅ API call successful!")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.text}")
            return False
            
    except ImportError as e:
        print(f"❌ google-genai package not installed: {str(e)}")
        print("Run: pip install google-genai")
        return False
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        
        # Check if this is an authentication error
        if "authentication" in str(e).lower() or "credentials" in str(e).lower():
            print("\n🔧 Authentication Setup Required:")
            print("1. Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install")
            print("2. Run: gcloud auth application-default login")
            print("3. Or set up service account credentials")
            print("4. Ensure your user has 'Vertex AI User' role")
        elif "permission" in str(e).lower() or "access" in str(e).lower():
            print("\n🔧 Permission Setup Required:")
            print("1. Enable Vertex AI API in your Google Cloud project")
            print("2. Ensure your user has 'Vertex AI User' role")
            print("3. Check if Vertex AI is available in your region")
        
        return False


if __name__ == "__main__":
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    success = test_vertexai_simple()
    
    if success:
        print("\n🚀 Ready for Sprint 4 LLM integration with Vertex AI!")
        sys.exit(0)
    else:
        print("\n❌ Fix the issues above before proceeding with Sprint 4")
        sys.exit(1)
