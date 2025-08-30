from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class EmotionReading(models.Model):
    """Store individual emotion readings from users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Core emotions (0.0 to 1.0)
    joy = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0
    )
    calm = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0
    )
    energy = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0
    )
    melancholy = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.0
    )
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Analysis fields
    dominant_emotion = models.CharField(max_length=20, blank=True)
    emotion_intensity = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_id', '-timestamp']),
            models.Index(fields=['dominant_emotion']),
            models.Index(fields=['-timestamp']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate dominant emotion and intensity
        emotions = {
            'joy': self.joy,
            'calm': self.calm,
            'energy': self.energy,
            'melancholy': self.melancholy
        }
        
        self.dominant_emotion = max(emotions.keys(), key=emotions.get)
        self.emotion_intensity = max(emotions.values())
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.session_id} - {self.dominant_emotion} ({self.timestamp})"

class EnvironmentResponse(models.Model):
    """Store calculated environmental responses"""
    emotion_reading = models.OneToOneField(
        EmotionReading, 
        on_delete=models.CASCADE,
        related_name='environment_response'
    )
    
    # Visual responses
    lighting_color = models.CharField(max_length=7, default='#FFFFFF')  # Hex color
    lighting_intensity = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.5
    )
    background_color = models.CharField(max_length=7, default='#2C3E50')
    
    # Audio responses
    audio_tone = models.CharField(max_length=50, default='ambient')
    audio_frequency = models.FloatField(default=440.0)
    audio_volume = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.1
    )
    
    # Pattern responses
    visual_pattern = models.CharField(max_length=50, default='gentle_ripples')
    particle_count = models.IntegerField(default=1000)
    animation_speed = models.FloatField(default=1.0)
    
    # Smart home simulation
    temperature = models.FloatField(default=22.0)  # Celsius
    humidity = models.FloatField(default=50.0)     # Percentage
    air_quality = models.CharField(max_length=20, default='good')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Environment for {self.emotion_reading.dominant_emotion}"

class EmotionSession(models.Model):
    """Track emotion sessions and their metadata"""
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Session metadata
    start_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Session stats
    total_readings = models.IntegerField(default=0)
    average_joy = models.FloatField(default=0.0)
    average_calm = models.FloatField(default=0.0)
    average_energy = models.FloatField(default=0.0)
    average_melancholy = models.FloatField(default=0.0)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    location_country = models.CharField(max_length=2, blank=True)  # ISO country code
    
    class Meta:
        ordering = ['-last_activity']
    
    def update_averages(self):
        """Recalculate average emotions for this session"""
        readings = EmotionReading.objects.filter(session_id=self.session_id)
        count = readings.count()
        
        if count > 0:
            self.total_readings = count
            self.average_joy = sum(r.joy for r in readings) / count
            self.average_calm = sum(r.calm for r in readings) / count
            self.average_energy = sum(r.energy for r in readings) / count
            self.average_melancholy = sum(r.melancholy for r in readings) / count
            self.save()
    
    def __str__(self):
        return f"Session {self.session_id} ({self.total_readings} readings)"

class CollectiveEmotion(models.Model):
    """Aggregate emotion data for collective experiences"""
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Collective emotions (averaged from all active sessions)
    collective_joy = models.FloatField(default=0.0)
    collective_calm = models.FloatField(default=0.0)
    collective_energy = models.FloatField(default=0.0)
    collective_melancholy = models.FloatField(default=0.0)
    
    # Metadata
    active_sessions = models.IntegerField(default=0)
    total_readings_processed = models.IntegerField(default=0)
    dominant_collective_emotion = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def calculate_collective_emotions(self):
        """Calculate collective emotions from recent active sessions"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Get sessions active in the last 10 minutes
        cutoff_time = timezone.now() - timedelta(minutes=10)
        active_sessions = EmotionSession.objects.filter(
            last_activity__gte=cutoff_time,
            is_active=True
        )
        
        if not active_sessions.exists():
            return
        
        count = active_sessions.count()
        self.active_sessions = count
        
        # Calculate averages
        self.collective_joy = sum(s.average_joy for s in active_sessions) / count
        self.collective_calm = sum(s.average_calm for s in active_sessions) / count
        self.collective_energy = sum(s.average_energy for s in active_sessions) / count
        self.collective_melancholy = sum(s.average_melancholy for s in active_sessions) / count
        
        # Find dominant emotion
        emotions = {
            'joy': self.collective_joy,
            'calm': self.collective_calm,
            'energy': self.collective_energy,
            'melancholy': self.collective_melancholy
        }
        self.dominant_collective_emotion = max(emotions.keys(), key=emotions.get)
        
        # Count total readings
        self.total_readings_processed = sum(s.total_readings for s in active_sessions)
        
        self.save()
    
    def __str__(self):
        return f"Collective {self.dominant_collective_emotion} ({self.active_sessions} sessions)"
