from django.contrib import admin
from .models import EmotionReading, EnvironmentResponse, EmotionSession, CollectiveEmotion

@admin.register(EmotionReading)
class EmotionReadingAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'dominant_emotion', 'emotion_intensity', 'timestamp']
    list_filter = ['dominant_emotion', 'timestamp']
    search_fields = ['session_id']
    readonly_fields = ['id', 'dominant_emotion', 'emotion_intensity', 'timestamp']

@admin.register(EnvironmentResponse)
class EnvironmentResponseAdmin(admin.ModelAdmin):
    list_display = ['emotion_reading', 'lighting_color', 'audio_tone', 'visual_pattern', 'created_at']
    list_filter = ['audio_tone', 'visual_pattern', 'created_at']
    readonly_fields = ['created_at']

@admin.register(EmotionSession)
class EmotionSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'total_readings', 'is_active', 'start_time', 'last_activity']
    list_filter = ['is_active', 'start_time']
    search_fields = ['session_id']
    readonly_fields = ['start_time', 'last_activity']

@admin.register(CollectiveEmotion)
class CollectiveEmotionAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'dominant_collective_emotion', 'active_sessions', 'total_readings_processed']
    list_filter = ['dominant_collective_emotion', 'timestamp']
    readonly_fields = ['timestamp']
