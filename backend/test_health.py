#!/usr/bin/env python3
"""
Test script to verify the health endpoint works correctly.
Run this after starting the server: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import requests
import sys
import time

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test the health endpoint responds correctly."""
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        print(f"Health endpoint test:")
        print(f"  URL: {base_url}/health")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Time: {response_time:.2f}s")
        print(f"  Response: {response.json()}")
        
        if response.status_code == 200:
            print("  ✓ Health endpoint is working correctly")
            if response_time < 2:
                print("  ✓ Response time is within 2 seconds")
                return True
            else:
                print("  ✗ Response time exceeds 2 seconds")
                return False
        else:
            print("  ✗ Health endpoint returned non-200 status")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Could not connect to {base_url}")
        print("  Make sure the server is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"  ✗ Error testing health endpoint: {e}")
        return False

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = test_health_endpoint(base_url)
    sys.exit(0 if success else 1)