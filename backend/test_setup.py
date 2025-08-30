#!/usr/bin/env python
"""
Test script to verify the Mood Mirror backend setup
"""
import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mood_mirror.settings')
django.setup()

from emotions.models import EmotionReading, EmotionSession, EnvironmentResponse

def test_models():
    """Test that models work correctly"""
    print("Testing models...")
    
    # Create a test emotion reading
    reading = EmotionReading.objects.create(
        session_id='test_session_001',
        joy=0.8,
        calm=0.6,
        energy=0.9,
        melancholy=0.2
    )
    
    print(f"✅ Created emotion reading: {reading}")
    print(f"   Dominant emotion: {reading.dominant_emotion}")
    print(f"   Emotion intensity: {reading.emotion_intensity}")
    
    # Test session creation and updates
    session = EmotionSession.objects.create(
        session_id='test_session_001'
    )
    session.update_averages()
    
    print(f"✅ Created session: {session}")
    print(f"   Average joy: {session.average_joy}")
    
    return True

def test_api_endpoints():
    """Test API endpoints (requires server to be running)"""
    print("\nTesting API endpoints...")
    base_url = "http://localhost:8000"
    
    # Test data
    test_emotion = {
        "session_id": "api_test_001",
        "joy": 0.7,
        "calm": 0.5,
        "energy": 0.8,
        "melancholy": 0.3
    }
    
    try:
        # Test creating emotion reading
        response = requests.post(
            f"{base_url}/emotions/api/readings/",
            json=test_emotion,
            timeout=5
        )
        
        if response.status_code == 201:
            print("✅ API endpoint working - emotion reading created")
            return True
        else:
            print(f"❌ API test failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  API test skipped - server not running")
        print("   Start server with: python manage.py runserver")
        return None

if __name__ == "__main__":
    print("🧪 Mood Mirror Backend Test Suite")
    print("=" * 40)
    
    # Test models
    try:
        test_models()
        print("✅ Model tests passed!")
    except Exception as e:
        print(f"❌ Model tests failed: {e}")
        sys.exit(1)
    
    # Test API
    api_result = test_api_endpoints()
    
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    print("✅ Models: Working")
    if api_result is True:
        print("✅ API: Working")
    elif api_result is None:
        print("⚠️  API: Not tested (server not running)")
    else:
        print("❌ API: Failed")
    
    print("\n🚀 Next steps:")
    print("1. Start the server: python manage.py runserver")
    print("2. Test WebSocket: Connect to ws://localhost:8000/ws/emotions/test_session/")
    print("3. Create frontend to interact with the API")
    print("4. Test environment responses and collective emotions")
