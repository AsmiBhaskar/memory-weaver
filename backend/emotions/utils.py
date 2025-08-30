# emotions/utils.py
import colorsys
import math
from typing import Dict, List, Tuple
from django.utils import timezone
from datetime import timedelta
from .models import EmotionReading, EmotionSession, CollectiveEmotion

def calculate_environment_response(emotion_data: Dict[str, float]) -> Dict:
    """
    Calculate comprehensive environmental responses based on emotion data
    
    Args:
        emotion_data: Dictionary with keys 'joy', 'calm', 'energy', 'melancholy'
        
    Returns:
        Dictionary with environmental response parameters
    """
    joy = emotion_data.get('joy', 0.0)
    calm = emotion_data.get('calm', 0.0)
    energy = emotion_data.get('energy', 0.0)
    melancholy = emotion_data.get('melancholy', 0.0)
    
    # Lighting calculations
    lighting_color = calculate_lighting_color(joy, calm, energy, melancholy)
    lighting_intensity = calculate_lighting_intensity(joy, calm, energy, melancholy)
    background_color = calculate_background_color(joy, calm, energy, melancholy)
    
    # Audio calculations
    audio_tone = determine_audio_tone(joy, calm, energy, melancholy)
    audio_frequency = calculate_audio_frequency(joy, calm, energy, melancholy)
    audio_volume = calculate_audio_volume(joy, calm, energy, melancholy)
    
    # Visual pattern calculations
    visual_pattern = determine_visual_pattern(joy, calm, energy, melancholy)
    particle_count = calculate_particle_count(joy, calm, energy, melancholy)
    animation_speed = calculate_animation_speed(joy, calm, energy, melancholy)
    
    # Smart home simulation
    temperature = calculate_temperature(joy, calm, energy, melancholy)
    humidity = calculate_humidity(joy, calm, energy, melancholy)
    air_quality = determine_air_quality(joy, calm, energy, melancholy)
    
    return {
        'lighting_color': lighting_color,
        'lighting_intensity': lighting_intensity,
        'background_color': background_color,
        'audio_tone': audio_tone,
        'audio_frequency': audio_frequency,
        'audio_volume': audio_volume,
        'visual_pattern': visual_pattern,
        'particle_count': particle_count,
        'animation_speed': animation_speed,
        'temperature': temperature,
        'humidity': humidity,
        'air_quality': air_quality,
    }

def calculate_lighting_color(joy: float, calm: float, energy: float, melancholy: float) -> str:
    """Calculate lighting color based on emotions"""
    # Define base colors for each emotion
    emotion_colors = {
        'joy': (60, 100, 100),      # Bright yellow (HSV)
        'calm': (200, 70, 90),      # Soft blue
        'energy': (15, 100, 100),   # Bright orange
        'melancholy': (280, 80, 70) # Purple
    }
    
    emotions = {'joy': joy, 'calm': calm, 'energy': energy, 'melancholy': melancholy}
    
    # Find dominant emotion
    dominant = max(emotions.keys(), key=emotions.get)
    dominant_value = emotions[dominant]
    
    if dominant_value > 0.7:
        # Strong single emotion
        h, s, v = emotion_colors[dominant]
    else:
        # Blend colors based on emotion mix
        total_weight = sum(emotions.values())
        if total_weight == 0:
            return '#FFFFFF'
        
        weighted_h = sum(emotions[emotion] * emotion_colors[emotion][0] for emotion in emotions) / total_weight
        weighted_s = sum(emotions[emotion] * emotion_colors[emotion][1] for emotion in emotions) / total_weight
        weighted_v = sum(emotions[emotion] * emotion_colors[emotion][2] for emotion in emotions) / total_weight
        
        h, s, v = weighted_h, weighted_s, weighted_v
    
    # Convert HSV to RGB to HEX
    r, g, b = colorsys.hsv_to_rgb(h/360, s/100, v/100)
    hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
    
    return hex_color

def calculate_lighting_intensity(joy: float, calm: float, energy: float, melancholy: float) -> float:
    """Calculate lighting intensity (0.0 to 1.0)"""
    # Joy and energy increase brightness, melancholy decreases it
    base_intensity = 0.4
    joy_boost = joy * 0.4
    energy_boost = energy * 0.3
    calm_boost = calm * 0.2
    melancholy_reduction = melancholy * 0.3
    
    intensity = base_intensity + joy_boost + energy_boost + calm_boost - melancholy_reduction
    return max(0.1, min(1.0, intensity))

def calculate_background_color(joy: float, calm: float, energy: float, melancholy: float) -> str:
    """Calculate background color"""
    if joy > 0.6:
        return '#4A90E2'  # Bright blue
    elif calm > 0.6:
        return '#2E8B57'  # Sea green
    elif energy > 0.6:
        return '#B22222'  # Fire brick
    elif melancholy > 0.6:
        return '#483D8B'  # Dark slate blue
    else:
        return '#2C3E50'  # Default dark blue

def determine_audio_tone(joy: float, calm: float, energy: float, melancholy: float) -> str:
    """Determine audio tone category"""
    emotions = {'joy': joy, 'calm': calm, 'energy': energy, 'melancholy': melancholy}
    dominant = max(emotions.keys(), key=emotions.get)
    
    tone_mapping = {
        'joy': 'uplifting',
        'calm': 'peaceful',
        'energy': 'energetic',
        'melancholy': 'melancholic'
    }
    
    return tone_mapping.get(dominant, 'ambient')

def calculate_audio_frequency(joy: float, calm: float, energy: float, melancholy: float) -> float:
    """Calculate base audio frequency"""
    # Base frequency around middle C
    base_freq = 261.63
    
    # Joy and energy raise pitch, melancholy lowers it
    frequency_modifier = (joy * 1.5 + energy * 1.2 - melancholy * 0.8)
    final_freq = base_freq * (1 + frequency_modifier)
    
    return max(100.0, min(1000.0, final_freq))

def calculate_audio_volume(joy: float, calm: float, energy: float, melancholy: float) -> float:
    """Calculate audio volume (0.0 to 1.0)"""
    # Energy and joy increase volume
    base_volume = 0.05
    volume_boost = energy * 0.15 + joy * 0.1
    final_volume = base_volume + volume_boost
    
    return max(0.01, min(0.3, final_volume))  # Keep it subtle

def determine_visual_pattern(joy: float, calm: float, energy: float, melancholy: float) -> str:
    """Determine visual pattern type"""
    if energy > 0.6:
        return 'dynamic_particles'
    elif joy > 0.6:
        return 'flowing_waves'
    elif calm > 0.6:
        return 'gentle_ripples'
    elif melancholy > 0.6:
        return 'slow_drift'
    else:
        return 'ambient_float'

def calculate_particle_count(joy: float, calm: float, energy: float, melancholy: float) -> int:
    """Calculate number of particles for visualization"""
    base_count = 500
    
    # Energy and joy increase particles
    multiplier = 1 + (energy * 1.5) + (joy * 1.2) - (melancholy * 0.5)
    particle_count = int(base_count * multiplier)
    
    return max(100, min(2000, particle_count))

def calculate_animation_speed(joy: float, calm: float, energy: float, melancholy: float) -> float:
    """Calculate animation speed multiplier"""
    base_speed = 1.0
    
    # Energy increases speed, calm and melancholy decrease it
    speed_modifier = (energy * 2.0) + (joy * 1.5) - (calm * 0.3) - (melancholy * 0.7)
    final_speed = base_speed + speed_modifier
    
    return max(0.1, min(3.0, final_speed))

def calculate_temperature(joy: float, calm: float, energy: float, melancholy: float) -> float:
    """Calculate ideal temperature in Celsius"""
    base_temp = 22.0  # Comfortable room temperature
    
    # Energy increases temperature, calm decreases slightly
    temp_modifier = (energy * 3.0) + (joy * 1.5) - (calm * 1.0) - (melancholy * 0.5)
    final_temp = base_temp + temp_modifier
    
    return max(18.0, min(28.0, final_temp))

def calculate_humidity(joy: float, calm: float, energy: float, melancholy: float) -> float:
    """Calculate ideal humidity percentage"""
    base_humidity = 45.0
    
    # Calm increases humidity (like being near water), energy decreases
    humidity_modifier = (calm * 15.0) + (melancholy * 5.0) - (energy * 10.0)
    final_humidity = base_humidity + humidity_modifier
    
    return max(30.0, min(70.0, final_humidity))

def determine_air_quality(joy: float, calm: float, energy: float, melancholy: float) -> str:
    """Determine air quality description"""
    overall_positive = joy + calm + energy - melancholy
    
    if overall_positive > 1.5:
        return 'excellent'
    elif overall_positive > 1.0:
        return 'good'
    elif overall_positive > 0.5:
        return 'moderate'
    else:
        return 'needs_improvement'

def get_session_analytics(session_id: str) -> Dict:
    """Get comprehensive analytics for a session"""
    try:
        session = EmotionSession.objects.get(session_id=session_id)
        readings = EmotionReading.objects.filter(session_id=session_id).order_by('timestamp')
        
        if not readings.exists():
            return {'error': 'No readings found for this session'}
        
        # Calculate emotion journey (simplified time series)
        emotion_journey = []
        for reading in readings[::max(1, len(readings)//20)]:  # Sample up to 20 points
            emotion_journey.append({
                'timestamp': reading.timestamp.isoformat(),
                'joy': reading.joy,
                'calm': reading.calm,
                'energy': reading.energy,
                'melancholy': reading.melancholy,
                'dominant': reading.dominant_emotion
            })
        
        # Calculate peak emotions
        peak_emotions = {
            'joy': max(r.joy for r in readings),
            'calm': max(r.calm for r in readings),
            'energy': max(r.energy for r in readings),
            'melancholy': max(r.melancholy for r in readings)
        }
        
        # Get recent readings (last 10)
        recent_readings = readings[:10]
        
        return {
            'session_id': session_id,
            'total_readings': session.total_readings,
            'session_duration_minutes': (session.last_activity - session.start_time).total_seconds() / 60,
            'dominant_emotion': max(['joy', 'calm', 'energy', 'melancholy'], 
                                  key=lambda x: getattr(session, f'average_{x}')),
            'emotion_journey': emotion_journey,
            'peak_emotions': peak_emotions,
            'recent_readings': [
                {
                    'timestamp': r.timestamp.isoformat(),
                    'joy': r.joy,
                    'calm': r.calm,
                    'energy': r.energy,
                    'melancholy': r.melancholy,
                    'dominant': r.dominant_emotion
                } for r in recent_readings
            ],
            'averages': {
                'joy': session.average_joy,
                'calm': session.average_calm,
                'energy': session.average_energy,
                'melancholy': session.average_melancholy
            }
        }
    except EmotionSession.DoesNotExist:
        return {'error': 'Session not found'}
    except Exception as e:
        return {'error': str(e)}