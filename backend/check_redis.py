#!/usr/bin/env python3
"""
Check Redis connection and setup script
"""

import redis
import subprocess
import sys
import os

def check_redis():
    """Check if Redis is running and accessible"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
        r.ping()
        print("✅ Redis is running and accessible")
        return True
    except redis.ConnectionError:
        print("❌ Redis is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Redis: {e}")
        return False

def install_redis_windows():
    """Instructions for installing Redis on Windows"""
    print("\n📋 To install Redis on Windows:")
    print("1. Download Redis from: https://github.com/microsoftarchive/redis/releases")
    print("2. Or use Chocolatey: choco install redis-64")
    print("3. Or use WSL: wsl --install then sudo apt install redis-server")
    print("4. Or use Docker: docker run -d -p 6379:6379 redis:alpine")

def main():
    print("🔍 Checking Redis connection...")
    
    if check_redis():
        print("🎉 Redis is ready!")
        return True
    else:
        print("\n⚠️  Redis is not running. You have several options:")
        print("\nOption 1 - Docker (Recommended):")
        print("docker run -d -p 6379:6379 --name redis redis:alpine")
        
        print("\nOption 2 - Windows Subsystem for Linux (WSL):")
        print("wsl --install")
        print("sudo apt update && sudo apt install redis-server")
        print("sudo service redis-server start")
        
        print("\nOption 3 - Chocolatey:")
        print("choco install redis-64")
        
        print("\nOption 4 - Manual Download:")
        print("Download from: https://github.com/microsoftarchive/redis/releases")
        
        return False

if __name__ == "__main__":
    main()
