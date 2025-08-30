from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Any
from .models import EmotionReading, EmotionSession, CollectiveEmotion

class EmotionAnalytics:
    """Advanced analytics for emotion data"""
    
    @staticmethod
    def get_emotion_trends(hours: int = 24) -> Dict[str, Any]:
        """Get emotion trends over time"""
        cutoff = timezone.now() - timedelta(hours=hours)
        
        readings = EmotionReading.objects.filter(
            timestamp__gte=cutoff
        ).order_by('timestamp')
        
        if not readings.exists():
            return {'error': 'No data available for the specified period'}
        
        # Calculate hourly averages
        hourly_trends = []
        current_time = cutoff
        
        while current_time < timezone.now():
            hour_end = current_time + timedelta(hours=1)
            hour_readings = readings.filter(
                timestamp__gte=current_time,
                timestamp__lt=hour_end
            )
            
            if hour_readings.exists():
                avg_emotions = hour_readings.aggregate(
                    avg_joy=Avg('joy'),
                    avg_calm=Avg('calm'),
                    avg_energy=Avg('energy'),
                    avg_melancholy=Avg('melancholy')
                )
                
                hourly_trends.append({
                    'hour': current_time.isoformat(),
                    'readings_count': hour_readings.count(),
                    **avg_emotions
                })
            
            current_time = hour_end
        
        return {
            'period_hours': hours,
            'total_readings': readings.count(),
            'hourly_trends': hourly_trends,
            'overall_averages': readings.aggregate(
                avg_joy=Avg('joy'),
                avg_calm=Avg('calm'),
                avg_energy=Avg('energy'),
                avg_melancholy=Avg('melancholy')
            )
        }
    
    @staticmethod
    def get_emotion_distribution() -> Dict[str, Any]:
        """Get distribution of dominant emotions"""
        total_readings = EmotionReading.objects.count()
        
        if total_readings == 0:
            return {'error': 'No emotion readings available'}
        
        distribution = EmotionReading.objects.values('dominant_emotion').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Calculate percentages
        for item in distribution:
            item['percentage'] = round((item['count'] / total_readings) * 100, 2)
        
        return {
            'total_readings': total_readings,
            'distribution': list(distribution)
        }
    
    @staticmethod
    def get_session_insights(session_id: str) -> Dict[str, Any]:
        """Get detailed insights for a specific session"""
        try:
            session = EmotionSession.objects.get(session_id=session_id)
            readings = EmotionReading.objects.filter(
                session_id=session_id
            ).order_by('timestamp')
            
            if not readings.exists():
                return {'error': 'No readings found for this session'}
            
            # Calculate emotion volatility (standard deviation)
            emotions = ['joy', 'calm', 'energy', 'melancholy']
            volatility = {}
            
            for emotion in emotions:
                values = [getattr(r, emotion) for r in readings]
                avg = sum(values) / len(values)
                variance = sum((x - avg) ** 2 for x in values) / len(values)
                volatility[f'{emotion}_volatility'] = variance ** 0.5
            
            # Emotion progression analysis
            first_reading = readings.first()
            last_reading = readings.last()
            
            progression = {}
            for emotion in emotions:
                start_val = getattr(first_reading, emotion)
                end_val = getattr(last_reading, emotion)
                progression[f'{emotion}_change'] = end_val - start_val
            
            # Peak and low moments
            peaks = {}
            lows = {}
            for emotion in emotions:
                max_reading = readings.order_by(f'-{emotion}').first()
                min_reading = readings.order_by(emotion).first()
                
                peaks[f'{emotion}_peak'] = {
                    'value': getattr(max_reading, emotion),
                    'timestamp': max_reading.timestamp.isoformat()
                }
                lows[f'{emotion}_low'] = {
                    'value': getattr(min_reading, emotion),
                    'timestamp': min_reading.timestamp.isoformat()
                }
            
            return {
                'session_id': session_id,
                'duration_minutes': (session.last_activity - session.start_time).total_seconds() / 60,
                'total_readings': readings.count(),
                'volatility': volatility,
                'progression': progression,
                'peaks': peaks,
                'lows': lows,
                'dominant_emotion_overall': session.dominant_emotion if hasattr(session, 'dominant_emotion') else 'unknown'
            }
            
        except EmotionSession.DoesNotExist:
            return {'error': 'Session not found'}
    
    @staticmethod
    def get_collective_insights(hours: int = 24) -> Dict[str, Any]:
        """Get insights about collective emotions"""
        cutoff = timezone.now() - timedelta(hours=hours)
        
        collective_data = CollectiveEmotion.objects.filter(
            timestamp__gte=cutoff
        ).order_by('timestamp')
        
        if not collective_data.exists():
            return {'error': 'No collective data available'}
        
        # Peak collective moments
        peak_joy = collective_data.order_by('-collective_joy').first()
        peak_energy = collective_data.order_by('-collective_energy').first()
        peak_calm = collective_data.order_by('-collective_calm').first()
        peak_melancholy = collective_data.order_by('-collective_melancholy').first()
        
        # Active sessions trends
        session_stats = collective_data.aggregate(
            max_sessions=Max('active_sessions'),
            min_sessions=Min('active_sessions'),
            avg_sessions=Avg('active_sessions')
        )
        
        return {
            'period_hours': hours,
            'data_points': collective_data.count(),
            'peak_moments': {
                'highest_joy': {
                    'value': peak_joy.collective_joy,
                    'timestamp': peak_joy.timestamp.isoformat(),
                    'active_sessions': peak_joy.active_sessions
                },
                'highest_energy': {
                    'value': peak_energy.collective_energy,
                    'timestamp': peak_energy.timestamp.isoformat(),
                    'active_sessions': peak_energy.active_sessions
                },
                'highest_calm': {
                    'value': peak_calm.collective_calm,
                    'timestamp': peak_calm.timestamp.isoformat(),
                    'active_sessions': peak_calm.active_sessions
                },
                'highest_melancholy': {
                    'value': peak_melancholy.collective_melancholy,
                    'timestamp': peak_melancholy.timestamp.isoformat(),
                    'active_sessions': peak_melancholy.active_sessions
                }
            },
            'session_statistics': session_stats,
            'current_state': collective_data.last()
        }

class PerformanceMetrics:
    """Performance monitoring for the system"""
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get overall system health metrics"""
        now = timezone.now()
        
        # Recent activity (last hour)
        recent_readings = EmotionReading.objects.filter(
            timestamp__gte=now - timedelta(hours=1)
        ).count()
        
        # Active sessions
        active_sessions = EmotionSession.objects.filter(
            is_active=True,
            last_activity__gte=now - timedelta(minutes=30)
        ).count()
        
        # Database size estimates
        total_readings = EmotionReading.objects.count()
        total_sessions = EmotionSession.objects.count()
        
        # Response time estimates (simplified)
        avg_environment_responses = EmotionReading.objects.filter(
            environment_response__isnull=False
        ).count()
        
        response_rate = (avg_environment_responses / total_readings * 100) if total_readings > 0 else 0
        
        return {
            'timestamp': now.isoformat(),
            'activity': {
                'recent_readings_1h': recent_readings,
                'active_sessions': active_sessions,
                'readings_per_minute_1h': recent_readings / 60 if recent_readings > 0 else 0
            },
            'database': {
                'total_emotion_readings': total_readings,
                'total_sessions': total_sessions,
                'environment_response_rate': round(response_rate, 2)
            },
            'status': 'healthy' if recent_readings > 0 or active_sessions > 0 else 'idle'
        }
