from django.core.management.base import BaseCommand
from emotions.models import EmotionReading, EmotionSession, EnvironmentResponse
import json
import csv
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Export emotion data to JSON or CSV format'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['json', 'csv'],
            default='json',
            help='Export format (json or csv)'
        )
        parser.add_argument(
            '--output',
            type=str,
            required=True,
            help='Output file path'
        )
        parser.add_argument(
            '--session-id',
            type=str,
            help='Export specific session only'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to export (default: 30)'
        )
        parser.add_argument(
            '--include-environment',
            action='store_true',
            help='Include environment response data'
        )
    
    def handle(self, *args, **options):
        format_type = options['format']
        output_file = options['output']
        session_id = options.get('session_id')
        days = options['days']
        include_env = options['include_environment']
        
        # Build query
        queryset = EmotionReading.objects.all()
        
        if session_id:
            queryset = queryset.filter(session_id=session_id)
            self.stdout.write(f'Filtering by session: {session_id}')
        
        if days > 0:
            cutoff = timezone.now() - timezone.timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=cutoff)
            self.stdout.write(f'Filtering last {days} days')
        
        queryset = queryset.order_by('timestamp')
        
        if include_env:
            queryset = queryset.select_related('environment_response')
        
        self.stdout.write(f'Found {queryset.count()} emotion readings')
        
        if format_type == 'json':
            self.export_json(queryset, output_file, include_env)
        else:
            self.export_csv(queryset, output_file, include_env)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported to {output_file}')
        )
    
    def export_json(self, queryset, output_file, include_env):
        """Export data to JSON format"""
        data = {
            'export_timestamp': timezone.now().isoformat(),
            'total_records': queryset.count(),
            'emotions': []
        }
        
        for reading in queryset:
            emotion_data = {
                'id': str(reading.id),
                'session_id': reading.session_id,
                'timestamp': reading.timestamp.isoformat(),
                'emotions': {
                    'joy': reading.joy,
                    'calm': reading.calm,
                    'energy': reading.energy,
                    'melancholy': reading.melancholy
                },
                'dominant_emotion': reading.dominant_emotion,
                'emotion_intensity': reading.emotion_intensity
            }
            
            if include_env and hasattr(reading, 'environment_response'):
                env = reading.environment_response
                emotion_data['environment_response'] = {
                    'lighting_color': env.lighting_color,
                    'lighting_intensity': env.lighting_intensity,
                    'background_color': env.background_color,
                    'audio_tone': env.audio_tone,
                    'audio_frequency': env.audio_frequency,
                    'audio_volume': env.audio_volume,
                    'visual_pattern': env.visual_pattern,
                    'particle_count': env.particle_count,
                    'animation_speed': env.animation_speed,
                    'temperature': env.temperature,
                    'humidity': env.humidity,
                    'air_quality': env.air_quality
                }
            
            data['emotions'].append(emotion_data)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_csv(self, queryset, output_file, include_env):
        """Export data to CSV format"""
        fieldnames = [
            'id', 'session_id', 'timestamp', 'joy', 'calm', 'energy', 
            'melancholy', 'dominant_emotion', 'emotion_intensity'
        ]
        
        if include_env:
            fieldnames.extend([
                'lighting_color', 'lighting_intensity', 'background_color',
                'audio_tone', 'audio_frequency', 'audio_volume',
                'visual_pattern', 'particle_count', 'animation_speed',
                'temperature', 'humidity', 'air_quality'
            ])
        
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for reading in queryset:
                row = {
                    'id': str(reading.id),
                    'session_id': reading.session_id,
                    'timestamp': reading.timestamp.isoformat(),
                    'joy': reading.joy,
                    'calm': reading.calm,
                    'energy': reading.energy,
                    'melancholy': reading.melancholy,
                    'dominant_emotion': reading.dominant_emotion,
                    'emotion_intensity': reading.emotion_intensity
                }
                
                if include_env and hasattr(reading, 'environment_response'):
                    env = reading.environment_response
                    row.update({
                        'lighting_color': env.lighting_color,
                        'lighting_intensity': env.lighting_intensity,
                        'background_color': env.background_color,
                        'audio_tone': env.audio_tone,
                        'audio_frequency': env.audio_frequency,
                        'audio_volume': env.audio_volume,
                        'visual_pattern': env.visual_pattern,
                        'particle_count': env.particle_count,
                        'animation_speed': env.animation_speed,
                        'temperature': env.temperature,
                        'humidity': env.humidity,
                        'air_quality': env.air_quality
                    })
                elif include_env:
                    # Fill with None if no environment response
                    for field in fieldnames[9:]:
                        row[field] = None
                
                writer.writerow(row)
