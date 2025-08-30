#!/usr/bin/env python3
"""
Comprehensive API testing script for the emotion tracking backend.
Tests all endpoints and functionality without requiring Redis.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test an API endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "data": None
        }

def print_test_result(test_name, result):
    """Print formatted test result"""
    status = "✅ PASS" if result["success"] else "❌ FAIL"
    print(f"{status} {test_name}")
    print(f"   Status: {result['status_code']}")
    if not result["success"]:
        print(f"   Error: {result.get('error', result.get('data', 'Unknown error'))}")
    elif isinstance(result["data"], dict):
        print(f"   Response: {json.dumps(result['data'], indent=2)[:200]}...")
    print()

def main():
    print("🧪 API Testing Suite")
    print("=" * 50)
    
    # Test basic endpoints without authentication first
    print("\n📡 Testing Basic Endpoints")
    print("-" * 30)
    
    # Test collective emotions
    result = test_endpoint("GET", "/emotions/api/collective/")
    print_test_result("Collective Emotions", result)
    
    # Test system health
    result = test_endpoint("GET", "/emotions/api/system/")
    print_test_result("System Health", result)
    
    print("\n🔐 Testing Authentication")
    print("-" * 30)
    
    # Test user registration
    user_data = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpassword123"
    }
    
    result = test_endpoint("POST", "/emotions/auth/register/", user_data)
    print_test_result("User Registration", result)
    
    token = None
    if result["success"] and "token" in result["data"]:
        token = result["data"]["token"]
        print(f"   🔑 Received token: {token[:20]}...")
    
    # Test login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    result = test_endpoint("POST", "/emotions/auth/login/", login_data)
    print_test_result("User Login", result)
    
    if result["success"] and "token" in result["data"]:
        token = result["data"]["token"]
        print(f"   🔑 Login token: {token[:20]}...")
    
    if not token:
        print("❌ No authentication token available. Skipping authenticated tests.")
        return
    
    # Set up headers for authenticated requests
    auth_headers = {"Authorization": f"Token {token}"}
    
    print("\n📊 Testing Emotion Tracking (Authenticated)")
    print("-" * 40)
    
    # Test emotion reading creation
    emotion_data = {
        "session_id": f"test_session_{int(time.time())}",
        "joy": 0.8,
        "sadness": 0.1,
        "anger": 0.05,
        "fear": 0.05,
        "surprise": 0.0,
        "disgust": 0.0,
        "valence": 0.75,
        "arousal": 0.6,
        "environment_data": {
            "lighting": "bright",
            "noise_level": "quiet",
            "temperature": 22.5,
            "social_context": "alone"
        }
    }
    
    result = test_endpoint("POST", "/emotions/api/readings/", emotion_data, auth_headers)
    print_test_result("Create Emotion Reading", result)
    
    reading_id = None
    if result["success"] and "id" in result["data"]:
        reading_id = result["data"]["id"]
        print(f"   📝 Created reading ID: {reading_id}")
    
    # Test emotion readings list
    result = test_endpoint("GET", "/emotions/api/readings/", headers=auth_headers)
    print_test_result("List Emotion Readings", result)
    
    # Test emotion reading detail
    if reading_id:
        result = test_endpoint("GET", f"/emotions/api/readings/{reading_id}/", headers=auth_headers)
        print_test_result("Get Emotion Reading Detail", result)
    
    # Test environment responses
    result = test_endpoint("GET", "/emotions/api/environment/", headers=auth_headers)
    print_test_result("List Environment Responses", result)
    
    # Test emotion sessions
    result = test_endpoint("GET", "/emotions/api/sessions/", headers=auth_headers)
    print_test_result("List Emotion Sessions", result)
    
    print("\n📈 Testing Analytics (Authenticated)")
    print("-" * 35)
    
    # Test system analytics
    result = test_endpoint("GET", "/emotions/api/system/analytics/", headers=auth_headers)
    print_test_result("System Analytics", result)
    
    print("\n🌍 Testing Public Endpoints")
    print("-" * 30)
    
    # Test public collective emotions (should work without auth)
    result = test_endpoint("GET", "/emotions/api/collective/")
    print_test_result("Public Collective Emotions", result)
    
    # Test public system health
    result = test_endpoint("GET", "/emotions/api/system/")
    print_test_result("Public System Health", result)
    
    print("\n🎉 API Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()
