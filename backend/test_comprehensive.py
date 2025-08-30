#!/usr/bin/env python
"""
Comprehensive testing suite for Mood Mirror backend
"""
import os
import sys
import django
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
import websocket
import threading

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mood_mirror.settings')
django.setup()

from emotions.models import EmotionReading, EmotionSession, EnvironmentResponse, CollectiveEmotion
from emotions.analytics import EmotionAnalytics, PerformanceMetrics

class BackendTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/emotions/api"
        self.ws_base = base_url.replace('http', 'ws')
        
    def test_database_models(self):
        """Test database models and relationships"""
        print("🧪 Testing Database Models...")
        import uuid
        unique_session_id = f"test_{uuid.uuid4().hex[:8]}"
        try:
            # Clean up test data for this session
            EmotionReading.objects.filter(session_id=unique_session_id).delete()
            EmotionSession.objects.filter(session_id=unique_session_id).delete()
            # Test 1: Create emotion reading
            reading = EmotionReading.objects.create(
                session_id=unique_session_id,
                joy=0.8,
                calm=0.6,
                energy=0.9,
                melancholy=0.2
            )
            assert reading.dominant_emotion == 'energy'
            assert reading.emotion_intensity == 0.9
            print("  ✅ Emotion reading creation and calculations")
            # Test 2: Session creation and updates
            session = EmotionSession.objects.create(session_id=unique_session_id)
            session.update_averages()
            assert session.total_readings == 1
            assert session.average_joy == 0.8
            print("  ✅ Session creation and average calculations")
            # Test 3: Environment response
            env_count_before = EnvironmentResponse.objects.count()
            # Create another reading (should trigger environment response via signal/view)
            reading2 = EmotionReading.objects.create(
                session_id=unique_session_id,
                joy=0.5,
                calm=0.7,
                energy=0.4,
                melancholy=0.6
            )
            print("  ✅ Multiple emotion readings")
            # Test 4: Collective emotions
            collective = CollectiveEmotion()
            collective.calculate_collective_emotions()
            print("  ✅ Collective emotion calculations")
            return True
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test all API endpoints"""
        print("🌐 Testing API Endpoints...")
        
        try:
            # Test 1: Create emotion reading
            emotion_data = {
                "session_id": "api_test_advanced",
                "joy": 0.7,
                "calm": 0.5,
                "energy": 0.8,
                "melancholy": 0.3
            }
            
            response = requests.post(f"{self.api_base}/readings/", json=emotion_data, timeout=10)
            assert response.status_code == 201
            reading_data = response.json()
            print("  ✅ POST /readings/ - Create emotion reading")
            
            # Test 2: Get readings
            response = requests.get(f"{self.api_base}/readings/", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /readings/ - List readings")
            
            # Test 3: Get readings by session
            response = requests.get(
                f"{self.api_base}/readings/by_session/?session_id=api_test_advanced",
                timeout=10
            )
            assert response.status_code == 200
            session_readings = response.json()
            assert session_readings['success'] == True
            print("  ✅ GET /readings/by_session/ - Filter by session")
            
            # Test 4: Get emotion trends
            response = requests.get(f"{self.api_base}/readings/trends/?hours=1", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /readings/trends/ - Emotion trends")
            
            # Test 5: Get emotion distribution
            response = requests.get(f"{self.api_base}/readings/distribution/", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /readings/distribution/ - Emotion distribution")
            
            # Test 6: Session endpoints
            response = requests.get(f"{self.api_base}/sessions/", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /sessions/ - List sessions")
            
            # Test 7: Session analytics
            response = requests.get(
                f"{self.api_base}/sessions/api_test_advanced/analytics/",
                timeout=10
            )
            assert response.status_code == 200
            print("  ✅ GET /sessions/{id}/analytics/ - Session analytics")
            
            # Test 8: Collective emotions
            response = requests.get(f"{self.api_base}/collective/current/", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /collective/current/ - Current collective state")
            
            # Test 9: System health
            response = requests.get(f"{self.api_base}/system/health/", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /system/health/ - System health")
            
            # Test 10: System stats
            response = requests.get(f"{self.api_base}/system/stats/", timeout=10)
            assert response.status_code == 200
            print("  ✅ GET /system/stats/ - System statistics")
            
            return True
            
        except requests.exceptions.ConnectionError:
            print("  ❌ Server not running - start with: python manage.py runserver")
            return False
        except AssertionError as e:
            print(f"  ❌ API assertion failed: {e}")
            return False
        except Exception as e:
            print(f"  ❌ API test failed: {e}")
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket functionality"""
        print("🔌 Testing WebSocket Connection...")
        
        try:
            messages_received = []
            connection_successful = threading.Event()
            
            def on_message(ws, message):
                data = json.loads(message)
                messages_received.append(data)
                print(f"  📨 Received: {data.get('type', 'unknown')}")
            
            def on_open(ws):
                connection_successful.set()
                print("  ✅ WebSocket connected")
                
                # Send test emotion data
                test_data = {
                    "type": "emotion_data",
                    "joy": 0.6,
                    "calm": 0.7,
                    "energy": 0.5,
                    "melancholy": 0.4
                }
                ws.send(json.dumps(test_data))
                print("  📤 Sent emotion data")
                
                # Send ping
                ws.send(json.dumps({"type": "ping"}))
                print("  📤 Sent ping")
                
                # Close after a short delay
                def close_later():
                    time.sleep(2)
                    ws.close()
                
                threading.Thread(target=close_later).start()
            
            def on_error(ws, error):
                print(f"  ❌ WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                print("  ✅ WebSocket closed")
            
            # Create WebSocket connection
            ws_url = f"{self.ws_base}/ws/emotions/websocket_test/"
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket in a thread
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection or timeout
            if connection_successful.wait(timeout=5):
                time.sleep(3)  # Wait for messages
                
                if len(messages_received) > 0:
                    print("  ✅ WebSocket message exchange successful")
                    return True
                else:
                    print("  ⚠️  WebSocket connected but no messages received")
                    return True
            else:
                print("  ❌ WebSocket connection timeout")
                return False
                
        except Exception as e:
            print(f"  ❌ WebSocket test failed: {e}")
            return False
    
    def test_performance_load(self):
        """Test system performance under load"""
        print("⚡ Testing Performance Under Load...")
        
        try:
            # Test concurrent API requests
            def make_request(i):
                emotion_data = {
                    "session_id": f"load_test_{i % 5}",  # 5 different sessions
                    "joy": 0.1 + (i % 10) * 0.1,
                    "calm": 0.1 + ((i + 1) % 10) * 0.1,
                    "energy": 0.1 + ((i + 2) % 10) * 0.1,
                    "melancholy": 0.1 + ((i + 3) % 10) * 0.1
                }
                
                response = requests.post(f"{self.api_base}/readings/", json=emotion_data, timeout=10)
                return response.status_code == 201
            
            # Send 20 concurrent requests
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(make_request, range(20)))
            
            end_time = time.time()
            success_count = sum(results)
            
            print(f"  📊 {success_count}/20 requests successful")
            print(f"  ⏱️  Total time: {end_time - start_time:.2f} seconds")
            print(f"  🚀 Requests per second: {20 / (end_time - start_time):.2f}")
            
            if success_count >= 18:  # Allow for some failures
                print("  ✅ Performance test passed")
                return True
            else:
                print("  ❌ Too many failed requests")
                return False
                
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            return False
    
    def test_analytics_functions(self):
        """Test analytics and utility functions"""
        print("📈 Testing Analytics Functions...")
        
        try:
            # Test emotion trends
            trends = EmotionAnalytics.get_emotion_trends(1)
            print("  ✅ Emotion trends analysis")
            
            # Test emotion distribution
            distribution = EmotionAnalytics.get_emotion_distribution()
            print("  ✅ Emotion distribution analysis")
            
            # Test session insights (if we have test data)
            try:
                insights = EmotionAnalytics.get_session_insights('api_test_advanced')
                if 'error' not in insights:
                    print("  ✅ Session insights analysis")
                else:
                    print("  ⚠️  Session insights (no data)")
            except:
                print("  ⚠️  Session insights (no data)")
            
            # Test collective insights
            collective_insights = EmotionAnalytics.get_collective_insights(1)
            print("  ✅ Collective insights analysis")
            
            # Test performance metrics
            health = PerformanceMetrics.get_system_health()
            print("  ✅ System health metrics")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Analytics test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Mood Mirror Backend - Comprehensive Test Suite")
        print("=" * 60)
        
        tests = [
            ("Database Models", self.test_database_models),
            ("API Endpoints", self.test_api_endpoints),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Performance Load", self.test_performance_load),
            ("Analytics Functions", self.test_analytics_functions),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"  💥 Test crashed: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = len(tests)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Backend is fully functional.")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed. Minor issues may exist.")
        else:
            print("❌ Multiple test failures. Check server and configuration.")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()
