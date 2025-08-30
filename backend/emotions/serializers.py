# emotions/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import EmotionReading, EnvironmentResponse, EmotionSession, CollectiveEmotion

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class EmotionReadingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    emotion_intensity = serializers.ReadOnlyField()
    dominant_emotion = serializers.ReadOnlyField()
    
    class Meta:
        model = EmotionReading
        fields = [
            'id', 'session_id', 'user', 'joy', 'calm', 'energy', 'melancholy',
            'timestamp', 'dominant_emotion', 'emotion_intensity'
        ]
        read_only_fields = ['id', 'timestamp', 'dominant_emotion', 'emotion_intensity']
    
    def validate(self, data):
        """Validate emotion values are within range"""
        emotions = ['joy', 'calm', 'energy', 'melancholy']
        for emotion in emotions:
            value = data.get(emotion, 0)
            if not 0 <= value <= 1:
                raise serializers.ValidationError(
                    f"{emotion} must be between 0 and 1"
                )
        return data

class EnvironmentResponseSerializer(serializers.ModelSerializer):
    emotion_reading_id = serializers.UUIDField(source='emotion_reading.id', read_only=True)
    dominant_emotion = serializers.CharField(source='emotion_reading.dominant_emotion', read_only=True)
    
    class Meta:
        model = EnvironmentResponse
        fields = [
            'emotion_reading_id', 'dominant_emotion', 'lighting_color', 
            'lighting_intensity', 'background_color', 'audio_tone', 
            'audio_frequency', 'audio_volume', 'visual_pattern', 
            'particle_count', 'animation_speed', 'temperature', 
            'humidity', 'air_quality', 'created_at'
        ]

class EmotionSessionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    readings_count = serializers.SerializerMethodField()
    session_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = EmotionSession
        fields = [
            'session_id', 'user', 'start_time', 'last_activity', 'is_active',
            'total_readings', 'average_joy', 'average_calm', 'average_energy',
            'average_melancholy', 'device_type', 'browser', 'location_country',
            'readings_count', 'session_duration'
        ]
    
    def get_readings_count(self, obj):
        return obj.total_readings
    
    def get_session_duration(self, obj):
        """Return session duration in minutes"""
        duration = obj.last_activity - obj.start_time
        return duration.total_seconds() / 60

class CollectiveEmotionSerializer(serializers.ModelSerializer):
    emotion_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = CollectiveEmotion
        fields = [
            'timestamp', 'collective_joy', 'collective_calm', 'collective_energy',
            'collective_melancholy', 'active_sessions', 'total_readings_processed',
            'dominant_collective_emotion', 'emotion_breakdown'
        ]
    
    def get_emotion_breakdown(self, obj):
        """Return emotion values as percentages"""
        return {
            'joy': round(obj.collective_joy * 100, 1),
            'calm': round(obj.collective_calm * 100, 1),
            'energy': round(obj.collective_energy * 100, 1),
            'melancholy': round(obj.collective_melancholy * 100, 1),
        }

# Combined serializers for detailed responses
class EmotionReadingDetailSerializer(EmotionReadingSerializer):
    environment_response = EnvironmentResponseSerializer(read_only=True)
    
    class Meta(EmotionReadingSerializer.Meta):
        fields = EmotionReadingSerializer.Meta.fields + ['environment_response']

class SessionSummarySerializer(serializers.Serializer):
    """Serializer for session summary statistics"""
    session_id = serializers.CharField()
    total_readings = serializers.IntegerField()
    session_duration_minutes = serializers.FloatField()
    dominant_emotion = serializers.CharField()
    emotion_journey = serializers.ListField()
    peak_emotions = serializers.DictField()
    recent_readings = EmotionReadingSerializer(many=True)