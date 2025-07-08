#!/usr/bin/env python3
"""
Test Redis connectivity for Celery backend
"""
import sys
import redis
from config import settings

def test_redis_connection():
    """Test Redis connection using the configured settings"""
    try:
        # Parse Redis URL
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Test connection
        response = redis_client.ping()
        if response:
            print("✅ Redis connection successful!")
            print(f"Connected to: {settings.REDIS_URL}")
            
            # Test basic operations
            redis_client.set("test_key", "test_value", ex=10)
            value = redis_client.get("test_key")
            if value and value.decode() == "test_value":
                print("✅ Redis read/write test successful!")
            else:
                print("❌ Redis read/write test failed")
                return False
                
            # Clean up
            redis_client.delete("test_key")
            return True
        else:
            print("❌ Redis ping failed")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Redis connection error: {e}")
        print(f"Make sure Redis is running at: {settings.REDIS_URL}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Redis connection for Celery...")
    success = test_redis_connection()
    sys.exit(0 if success else 1)
