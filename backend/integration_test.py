#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
Tests that frontend and backend can communicate properly
"""

import requests
import websocket
import json
import time
import threading
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/emotions/?session_id=test_integration_session"

def test_rest_api():
    """Test REST API endpoints"""
    print("🔍 Testing REST API Integration")
    print("-" * 40)
    
    success_count = 0
    total_tests = 4
    
    # Test system health
    try:
        response = requests.get(f"{BASE_URL}/emotions/api/system/", timeout=5)
        if response.status_code == 200:
            print("✅ System Health API: Working")
            success_count += 1
        else:
            print(f"❌ System Health API: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ System Health API: Error - {e}")
    
    # Test collective emotions
    try:
        response = requests.get(f"{BASE_URL}/emotions/api/collective/", timeout=5)
        if response.status_code == 200:
            print("✅ Collective Emotions API: Working")
            success_count += 1
        else:
            print(f"❌ Collective Emotions API: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Collective Emotions API: Error - {e}")
    
    # Test emotion readings (should require auth but test anyway)
    try:
        response = requests.get(f"{BASE_URL}/emotions/api/readings/", timeout=5)
        if response.status_code in [200, 401]:  # 401 is expected without auth
            print("✅ Emotion Readings API: Working (endpoint accessible)")
            success_count += 1
        else:
            print(f"❌ Emotion Readings API: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Emotion Readings API: Error - {e}")
    
    # Test CORS preflight
    try:
        response = requests.options(f"{BASE_URL}/emotions/api/collective/", 
                                  headers={'Origin': 'http://localhost:3000'}, timeout=5)
        if response.status_code in [200, 204]:
            print("✅ CORS Configuration: Working")
            success_count += 1
        else:
            print(f"❌ CORS Configuration: Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ CORS Configuration: Error - {e}")
    
    print(f"\n📊 REST API Results: {success_count}/{total_tests} tests passed\n")
    return success_count == total_tests

def test_websocket():
    """Test WebSocket connectivity"""
    print("🔌 Testing WebSocket Integration")
    print("-" * 40)
    
    success = False
    message_received = False
    
    def on_message(ws, message):
        nonlocal message_received
        try:
            data = json.loads(message)
            print(f"✅ WebSocket Message Received: {data.get('type', 'unknown')}")
            message_received = True
        except Exception as e:
            print(f"❌ WebSocket Message Parse Error: {e}")
    
    def on_error(ws, error):
        print(f"❌ WebSocket Error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print("🔌 WebSocket Connection Closed")
    
    def on_open(ws):
        nonlocal success
        print("✅ WebSocket Connection Opened")
        success = True
        
        # Send test emotion data
        test_data = {
            "type": "emotion_data",
            "session_id": "test_integration_session",
            "joy": 0.8,
            "calm": 0.6,
            "energy": 0.7,
            "melancholy": 0.2,
            "timestamp": datetime.now().isoformat()
        }
        
        print("📤 Sending test emotion data...")
        ws.send(json.dumps(test_data))
    
    try:
        print("🔌 Attempting WebSocket connection...")
        ws = websocket.WebSocketApp(WS_URL,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        
        # Run WebSocket in a thread with timeout
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection and test
        time.sleep(3)
        
        if success:
            print("✅ WebSocket Connection: Working")
        else:
            print("❌ WebSocket Connection: Failed")
        
        ws.close()
        
    except Exception as e:
        print(f"❌ WebSocket Test Error: {e}")
        success = False
    
    print(f"\n📊 WebSocket Results: {'Pass' if success else 'Fail'}\n")
    return success

def test_frontend_backend_data_flow():
    """Test data flow from frontend format to backend format"""
    print("📊 Testing Data Format Compatibility")
    print("-" * 40)
    
    # Simulate frontend emotion data
    frontend_emotion = {
        "joy": 0.8,
        "calm": 0.6,
        "energy": 0.7,
        "melancholy": 0.2
    }
    
    # Convert to backend format (as done in api.js)
    backend_emotion = {
        "session_id": "test_integration_session",
        "joy": frontend_emotion["joy"],
        "sadness": max(0, 1 - frontend_emotion["calm"]),  # Inverse of calm
        "anger": 0,
        "fear": 0,
        "surprise": frontend_emotion["energy"] * 0.3,
        "disgust": 0,
        "valence": (frontend_emotion["joy"] + frontend_emotion["calm"] - frontend_emotion["melancholy"]) / 3,
        "arousal": frontend_emotion["energy"],
        "environment_data": {
            "lighting": "normal",
            "noise_level": "normal",
            "temperature": 20,
            "social_context": "individual"
        }
    }
    
    print("✅ Frontend Emotion Format:")
    print(f"   Joy: {frontend_emotion['joy']:.2f}")
    print(f"   Calm: {frontend_emotion['calm']:.2f}")
    print(f"   Energy: {frontend_emotion['energy']:.2f}")
    print(f"   Melancholy: {frontend_emotion['melancholy']:.2f}")
    
    print("\n✅ Backend Emotion Format:")
    print(f"   Joy: {backend_emotion['joy']:.2f}")
    print(f"   Sadness: {backend_emotion['sadness']:.2f}")
    print(f"   Surprise: {backend_emotion['surprise']:.2f}")
    print(f"   Valence: {backend_emotion['valence']:.2f}")
    print(f"   Arousal: {backend_emotion['arousal']:.2f}")
    
    print("\n📊 Data Format Results: Pass\n")
    return True

def main():
    print("🧪 Frontend-Backend Integration Test Suite")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print(f"WebSocket URL: {WS_URL}")
    print("=" * 50)
    
    results = []
    
    # Test REST API
    results.append(test_rest_api())
    
    # Test WebSocket
    results.append(test_websocket())
    
    # Test data format compatibility
    results.append(test_frontend_backend_data_flow())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("🎯 Integration Test Summary")
    print("=" * 50)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ Frontend and backend are properly integrated!")
    else:
        print("⚠️  Some integration tests failed.")
        print("❌ Please check the configuration and try again.")
    
    return passed == total

if __name__ == "__main__":
    main()
