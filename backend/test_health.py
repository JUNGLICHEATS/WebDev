#!/usr/bin/env python3
"""
Simple script to test the health endpoint
"""
import requests
import sys
import os

def test_health_endpoint():
    port = os.getenv("PORT", 8000)
    url = f"http://localhost:{port}/health"
    
    try:
        print(f"Testing health endpoint at: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to health endpoint: {e}")
        return False

if __name__ == "__main__":
    success = test_health_endpoint()
    sys.exit(0 if success else 1)
