from django.core.management.base import BaseCommand
from emotions.redis_utils import redis_manager
import time

class Command(BaseCommand):
    help = 'Check Redis connection and perform basic operations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-operations',
            action='store_true',
            help='Run test operations on Redis'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 Redis Health Check")
        self.stdout.write("=" * 40)
        
        # Check Redis availability
        if redis_manager.is_redis_available():
            self.stdout.write(
                self.style.SUCCESS("✅ Redis connection: AVAILABLE")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ Redis connection: UNAVAILABLE")
            )
            self.stdout.write(
                "Note: System will use in-memory fallback for WebSockets"
            )
            return
        
        # Get Redis stats
        stats = redis_manager.get_redis_stats()
        if 'error' not in stats:
            self.stdout.write("\n📊 Redis Statistics:")
            for key, value in stats.items():
                self.stdout.write(f"  {key}: {value}")
        
        # Test operations if requested
        if options['test_operations']:
            self.stdout.write("\n🧪 Testing Redis Operations...")
            self._test_redis_operations()
    
    def _test_redis_operations(self):
        """Test various Redis operations"""
        test_session_id = f"health_check_{int(time.time())}"
        
        try:
            # Test caching
            test_data = {'test': 'data', 'timestamp': time.time()}
            
            # Test emotion reading cache
            success = redis_manager.cache_emotion_reading(test_session_id, test_data, 60)
            if success:
                cached_data = redis_manager.get_cached_emotion_reading(test_session_id)
                if cached_data == test_data:
                    self.stdout.write("  ✅ Emotion reading cache: WORKING")
                else:
                    self.stdout.write("  ❌ Emotion reading cache: DATA MISMATCH")
            else:
                self.stdout.write("  ❌ Emotion reading cache: FAILED")
            
            # Test session tracking
            success = redis_manager.track_active_session(test_session_id, 1, 60)
            if success:
                active_sessions = redis_manager.get_active_sessions()
                if test_session_id in active_sessions:
                    self.stdout.write("  ✅ Session tracking: WORKING")
                    # Clean up
                    redis_manager.remove_active_session(test_session_id)
                else:
                    self.stdout.write("  ❌ Session tracking: NOT FOUND")
            else:
                self.stdout.write("  ❌ Session tracking: FAILED")
            
            # Test collective emotions cache
            collective_data = {'collective_joy': 0.5, 'active_sessions': 1}
            success = redis_manager.cache_collective_emotions(collective_data, 60)
            if success:
                cached_collective = redis_manager.get_cached_collective_emotions()
                if cached_collective == collective_data:
                    self.stdout.write("  ✅ Collective emotions cache: WORKING")
                else:
                    self.stdout.write("  ❌ Collective emotions cache: DATA MISMATCH")
            else:
                self.stdout.write("  ❌ Collective emotions cache: FAILED")
            
            # Test system health cache
            health_data = {'status': 'healthy', 'timestamp': time.time()}
            success = redis_manager.cache_system_health(health_data, 60)
            if success:
                cached_health = redis_manager.get_cached_system_health()
                if cached_health == health_data:
                    self.stdout.write("  ✅ System health cache: WORKING")
                else:
                    self.stdout.write("  ❌ System health cache: DATA MISMATCH")
            else:
                self.stdout.write("  ❌ System health cache: FAILED")
            
            self.stdout.write(
                self.style.SUCCESS("\n🎉 Redis health check completed!")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Redis test operations failed: {e}")
            )
