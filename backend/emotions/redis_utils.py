import redis
import json
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis management utilities for Mood Mirror"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        try:
            self.redis_client.ping()
            return True
        except redis.ConnectionError:
            logger.warning("Redis connection failed")
            return False
    
    def cache_emotion_reading(self, session_id: str, reading_data: Dict, ttl: int = 3600) -> bool:
        """Cache emotion reading data"""
        try:
            cache_key = f"emotion_reading:{session_id}:latest"
            cache.set(cache_key, reading_data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to cache emotion reading: {e}")
            return False
    
    def get_cached_emotion_reading(self, session_id: str) -> Optional[Dict]:
        """Get cached emotion reading"""
        try:
            cache_key = f"emotion_reading:{session_id}:latest"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get cached emotion reading: {e}")
            return None
    
    def cache_session_analytics(self, session_id: str, analytics_data: Dict, ttl: int = 1800) -> bool:
        """Cache session analytics data"""
        try:
            cache_key = f"session_analytics:{session_id}"
            cache.set(cache_key, analytics_data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to cache session analytics: {e}")
            return False
    
    def get_cached_session_analytics(self, session_id: str) -> Optional[Dict]:
        """Get cached session analytics"""
        try:
            cache_key = f"session_analytics:{session_id}"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get cached session analytics: {e}")
            return None
    
    def cache_collective_emotions(self, data: Dict, ttl: int = 300) -> bool:
        """Cache collective emotion data"""
        try:
            cache_key = "collective_emotions:current"
            cache.set(cache_key, data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to cache collective emotions: {e}")
            return False
    
    def get_cached_collective_emotions(self) -> Optional[Dict]:
        """Get cached collective emotions"""
        try:
            cache_key = "collective_emotions:current"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get cached collective emotions: {e}")
            return None
    
    def cache_system_health(self, health_data: Dict, ttl: int = 60) -> bool:
        """Cache system health data"""
        try:
            cache_key = "system_health:current"
            cache.set(cache_key, health_data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to cache system health: {e}")
            return False
    
    def get_cached_system_health(self) -> Optional[Dict]:
        """Get cached system health"""
        try:
            cache_key = "system_health:current"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get cached system health: {e}")
            return None
    
    def track_active_session(self, session_id: str, user_id: Optional[int] = None, ttl: int = 1800) -> bool:
        """Track active session in Redis"""
        try:
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'last_activity': timezone.now().isoformat(),
                'is_active': True
            }
            
            # Store in Redis set for quick lookups
            self.redis_client.setex(f"active_session:{session_id}", ttl, json.dumps(session_data))
            self.redis_client.sadd("active_sessions", session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to track active session: {e}")
            return False
    
    def remove_active_session(self, session_id: str) -> bool:
        """Remove session from active tracking"""
        try:
            self.redis_client.delete(f"active_session:{session_id}")
            self.redis_client.srem("active_sessions", session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to remove active session: {e}")
            return False
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        try:
            return list(self.redis_client.smembers("active_sessions"))
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        try:
            return self.redis_client.scard("active_sessions")
        except Exception as e:
            logger.error(f"Failed to get active session count: {e}")
            return 0
    
    def cache_emotion_trends(self, hours: int, trends_data: Dict, ttl: int = 600) -> bool:
        """Cache emotion trends data"""
        try:
            cache_key = f"emotion_trends:{hours}h"
            cache.set(cache_key, trends_data, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to cache emotion trends: {e}")
            return False
    
    def get_cached_emotion_trends(self, hours: int) -> Optional[Dict]:
        """Get cached emotion trends"""
        try:
            cache_key = f"emotion_trends:{hours}h"
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get cached emotion trends: {e}")
            return None
    
    def publish_emotion_update(self, session_id: str, emotion_data: Dict) -> bool:
        """Publish emotion update to Redis pub/sub"""
        try:
            channel = f"emotion_updates:{session_id}"
            message = json.dumps({
                'type': 'emotion_update',
                'session_id': session_id,
                'data': emotion_data,
                'timestamp': timezone.now().isoformat()
            })
            self.redis_client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Failed to publish emotion update: {e}")
            return False
    
    def publish_collective_update(self, collective_data: Dict) -> bool:
        """Publish collective emotion update"""
        try:
            channel = "collective_emotion_updates"
            message = json.dumps({
                'type': 'collective_update',
                'data': collective_data,
                'timestamp': timezone.now().isoformat()
            })
            self.redis_client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Failed to publish collective update: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from Redis"""
        try:
            active_sessions = self.get_active_sessions()
            cleaned_count = 0
            
            for session_id in active_sessions:
                session_key = f"active_session:{session_id}"
                if not self.redis_client.exists(session_key):
                    self.redis_client.srem("active_sessions", session_id)
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    def get_redis_stats(self) -> Dict:
        """Get Redis statistics"""
        try:
            info = self.redis_client.info()
            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'active_sessions_count': self.get_active_session_count()
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {'error': str(e)}

# Global Redis manager instance
redis_manager = RedisManager()
