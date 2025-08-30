from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import EmotionReading, EnvironmentResponse, EmotionSession, CollectiveEmotion
from .serializers import (
    EmotionReadingSerializer, EnvironmentResponseSerializer,
    EmotionSessionSerializer, CollectiveEmotionSerializer,
    EmotionReadingDetailSerializer, SessionSummarySerializer
)
from .utils import calculate_environment_response, get_session_analytics
from .analytics import EmotionAnalytics, PerformanceMetrics
from .exceptions import APIResponseMixin
from .redis_utils import redis_manager
import logging

logger = logging.getLogger(__name__)

class EmotionReadingViewSet(viewsets.ModelViewSet, APIResponseMixin):
    queryset = EmotionReading.objects.all()
    serializer_class = EmotionReadingSerializer
    
    def perform_create(self, serializer):
        try:
            emotion_reading = serializer.save()
            
            # Create environment response
            emotion_data = {
                'joy': emotion_reading.joy,
                'calm': emotion_reading.calm,
                'energy': emotion_reading.energy,
                'melancholy': emotion_reading.melancholy
            }
            
            env_response = calculate_environment_response(emotion_data)
            EnvironmentResponse.objects.create(
                emotion_reading=emotion_reading,
                **env_response
            )
            
            # Update session averages
            session, created = EmotionSession.objects.get_or_create(
                session_id=emotion_reading.session_id,
                defaults={'is_active': True}
            )
            session.update_averages()
            
            logger.info(f"Created emotion reading for session {emotion_reading.session_id}")
            
        except Exception as e:
            logger.error(f"Error creating emotion reading: {e}")
            raise
    
    def create(self, request, *args, **kwargs):
        """Override create to return custom response format"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created reading with environment response
        reading = serializer.instance
        detailed_serializer = EmotionReadingDetailSerializer(reading)
        
        return self.success_response(
            detailed_serializer.data,
            "Emotion reading created successfully",
            status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def by_session(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return self.error_response('session_id parameter is required')
        
        readings = self.queryset.filter(session_id=session_id).order_by('-timestamp')
        serializer = EmotionReadingDetailSerializer(readings, many=True)
        
        return self.success_response(
            serializer.data,
            f"Retrieved {readings.count()} readings for session {session_id}"
        )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent readings from the last hour"""
        hours = int(request.query_params.get('hours', 1))
        cutoff = timezone.now() - timedelta(hours=hours)
        readings = self.queryset.filter(timestamp__gte=cutoff).order_by('-timestamp')
        
        serializer = self.get_serializer(readings, many=True)
        return self.success_response(
            serializer.data,
            f"Retrieved {readings.count()} readings from last {hours} hour(s)"
        )
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get emotion trends analysis with caching"""
        hours = int(request.query_params.get('hours', 24))
        
        # Try to get from cache first
        cached_trends = redis_manager.get_cached_emotion_trends(hours)
        if cached_trends:
            return self.success_response(cached_trends, "Emotion trends retrieved from cache")
        
        # Calculate fresh data
        trends_data = EmotionAnalytics.get_emotion_trends(hours)
        
        if 'error' in trends_data:
            return self.error_response(trends_data['error'])
        
        # Cache the results
        redis_manager.cache_emotion_trends(hours, trends_data)
        
        return self.success_response(trends_data, "Emotion trends retrieved successfully")
    
    @action(detail=False, methods=['get'])
    def distribution(self, request):
        """Get emotion distribution statistics"""
        distribution_data = EmotionAnalytics.get_emotion_distribution()
        
        if 'error' in distribution_data:
            return self.error_response(distribution_data['error'])
        
        return self.success_response(distribution_data, "Emotion distribution retrieved successfully")

class EmotionSessionViewSet(viewsets.ModelViewSet, APIResponseMixin):
    queryset = EmotionSession.objects.all()
    serializer_class = EmotionSessionSerializer
    lookup_field = 'session_id'
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, session_id=None):
        """Get detailed analytics for a session with caching"""
        # Try to get from cache first
        cached_analytics = redis_manager.get_cached_session_analytics(session_id)
        if cached_analytics:
            return self.success_response(cached_analytics, "Session analytics retrieved from cache")
        
        # Calculate fresh data
        analytics_data = get_session_analytics(session_id)
        
        if 'error' in analytics_data:
            return self.error_response(analytics_data['error'], status_code=404)
        
        # Cache the results
        redis_manager.cache_session_analytics(session_id, analytics_data)
        
        return self.success_response(analytics_data, "Session analytics retrieved successfully")
    
    @action(detail=True, methods=['get'])
    def insights(self, request, session_id=None):
        """Get advanced insights for a session"""
        insights_data = EmotionAnalytics.get_session_insights(session_id)
        
        if 'error' in insights_data:
            return self.error_response(insights_data['error'], status_code=404)
        
        return self.success_response(insights_data, "Session insights retrieved successfully")
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, session_id=None):
        """Mark a session as inactive"""
        try:
            session = self.get_object()
            session.is_active = False
            session.save()
            
            logger.info(f"Session {session_id} ended")
            return self.success_response(
                {'session_id': session_id, 'is_active': False},
                "Session ended successfully"
            )
        except EmotionSession.DoesNotExist:
            return self.error_response('Session not found', status_code=404)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active sessions"""
        cutoff = timezone.now() - timedelta(minutes=30)
        active_sessions = self.queryset.filter(
            is_active=True,
            last_activity__gte=cutoff
        ).order_by('-last_activity')
        
        serializer = self.get_serializer(active_sessions, many=True)
        return self.success_response(
            serializer.data,
            f"Retrieved {active_sessions.count()} active sessions"
        )

class CollectiveEmotionViewSet(viewsets.ReadOnlyModelViewSet, APIResponseMixin):
    queryset = CollectiveEmotion.objects.all()
    serializer_class = CollectiveEmotionSerializer
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current collective emotion state with caching"""
        # Try to get from cache first
        cached_collective = redis_manager.get_cached_collective_emotions()
        if cached_collective:
            return self.success_response(cached_collective, "Current collective emotion state retrieved from cache")
        
        try:
            # Create/update current collective emotion
            collective = CollectiveEmotion()
            collective.calculate_collective_emotions()
            
            serializer = self.get_serializer(collective)
            collective_data = serializer.data
            
            # Cache the results
            redis_manager.cache_collective_emotions(collective_data)
            
            return self.success_response(
                collective_data,
                "Current collective emotion state retrieved"
            )
        except Exception as e:
            logger.error(f"Error calculating collective emotions: {e}")
            return self.error_response("Error calculating collective emotions")
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get collective emotion history"""
        hours = int(request.query_params.get('hours', 24))
        cutoff = timezone.now() - timedelta(hours=hours)
        
        history = self.queryset.filter(timestamp__gte=cutoff).order_by('timestamp')
        serializer = self.get_serializer(history, many=True)
        
        return self.success_response(
            serializer.data,
            f"Retrieved collective emotion history for last {hours} hours"
        )
    
    @action(detail=False, methods=['get'])
    def insights(self, request):
        """Get collective emotion insights"""
        hours = int(request.query_params.get('hours', 24))
        insights_data = EmotionAnalytics.get_collective_insights(hours)
        
        if 'error' in insights_data:
            return self.error_response(insights_data['error'])
        
        return self.success_response(insights_data, "Collective insights retrieved successfully")

class EnvironmentResponseViewSet(viewsets.ReadOnlyModelViewSet, APIResponseMixin):
    queryset = EnvironmentResponse.objects.all()
    serializer_class = EnvironmentResponseSerializer
    
    @action(detail=False, methods=['get'])
    def for_session(self, request):
        """Get environment responses for a session"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return self.error_response('session_id parameter is required')
        
        responses = self.queryset.filter(
            emotion_reading__session_id=session_id
        ).order_by('-created_at')
        
        serializer = self.get_serializer(responses, many=True)
        return self.success_response(
            serializer.data,
            f"Retrieved {responses.count()} environment responses for session {session_id}"
        )
    
    @action(detail=False, methods=['get'])
    def latest_for_session(self, request):
        """Get latest environment response for a session"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return self.error_response('session_id parameter is required')
        
        try:
            latest_response = self.queryset.filter(
                emotion_reading__session_id=session_id
            ).latest('created_at')
            
            serializer = self.get_serializer(latest_response)
            return self.success_response(
                serializer.data,
                "Latest environment response retrieved"
            )
        except EnvironmentResponse.DoesNotExist:
            return self.error_response('No environment responses found for this session', status_code=404)

# System health and metrics endpoint
class SystemViewSet(viewsets.ViewSet, APIResponseMixin):
    """System monitoring and health endpoints"""
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Get system health metrics with caching"""
        # Try to get from cache first
        cached_health = redis_manager.get_cached_system_health()
        if cached_health:
            return self.success_response(cached_health, "System health retrieved from cache")
        
        try:
            health_data = PerformanceMetrics.get_system_health()
            
            # Add Redis statistics
            if redis_manager.is_redis_available():
                health_data['redis'] = redis_manager.get_redis_stats()
            else:
                health_data['redis'] = {'status': 'unavailable', 'using_fallback': True}
            
            # Cache the results
            redis_manager.cache_system_health(health_data)
            
            return self.success_response(health_data, "System health retrieved successfully")
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return self.error_response("Error retrieving system health")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get comprehensive system statistics"""
        try:
            # Combine various analytics
            health = PerformanceMetrics.get_system_health()
            distribution = EmotionAnalytics.get_emotion_distribution()
            trends = EmotionAnalytics.get_emotion_trends(24)
            
            stats_data = {
                'system_health': health,
                'emotion_distribution': distribution,
                'recent_trends': trends,
                'timestamp': timezone.now().isoformat()
            }
            
            return self.success_response(stats_data, "System statistics retrieved successfully")
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return self.error_response("Error retrieving system statistics")
