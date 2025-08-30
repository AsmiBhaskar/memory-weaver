import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import EmotionReading, CollectiveEmotion
from .serializers import EmotionReadingSerializer, CollectiveEmotionSerializer
from .redis_utils import redis_manager

class EmotionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Generate a session ID or get from query params
        self.session_id = self.scope.get('url_route', {}).get('kwargs', {}).get('session_id')
        if not self.session_id:
            # Try to get from query string
            query_string = self.scope.get('query_string', b'').decode()
            if 'session_id=' in query_string:
                self.session_id = query_string.split('session_id=')[1].split('&')[0]
            else:
                # Generate a unique session ID
                import uuid
                self.session_id = str(uuid.uuid4())
        
        self.group_name = f'emotions_{self.session_id}'
        
        # Join session group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Join collective group for global updates
        await self.channel_layer.group_add(
            'collective_emotions',
            self.channel_name
        )
        
        # Track session as active in Redis
        await self.track_session_active()
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Remove session from active tracking
        await self.remove_session_active()
        
        # Leave groups
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            'collective_emotions',
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'emotion_data':
                await self.handle_emotion_data(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def handle_emotion_data(self, data):
        """Handle incoming emotion data"""
        try:
            # Save emotion reading
            emotion_reading = await self.save_emotion_reading(data)
            
            # Broadcast to session group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'emotion_update',
                    'emotion_data': emotion_reading
                }
            )
            
            # Update collective emotions
            collective_data = await self.update_collective_emotions()
            
            # Broadcast collective update
            await self.channel_layer.group_send(
                'collective_emotions',
                {
                    'type': 'collective_update',
                    'collective_data': collective_data
                }
            )
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def emotion_update(self, event):
        """Send emotion update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'emotion_update',
            'data': event['emotion_data']
        }))
    
    async def collective_update(self, event):
        """Send collective emotion update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'collective_update',
            'data': event['collective_data']
        }))
    
    @database_sync_to_async
    def save_emotion_reading(self, data):
        """Save emotion reading to database"""
        from .utils import calculate_environment_response
        from .models import EnvironmentResponse, EmotionSession
        
        # Create emotion reading
        reading = EmotionReading.objects.create(
            session_id=self.session_id,
            joy=data.get('joy', 0.0),
            calm=data.get('calm', 0.0),
            energy=data.get('energy', 0.0),
            melancholy=data.get('melancholy', 0.0)
        )
        
        # Create environment response
        emotion_data = {
            'joy': reading.joy,
            'calm': reading.calm,
            'energy': reading.energy,
            'melancholy': reading.melancholy
        }
        
        env_response = calculate_environment_response(emotion_data)
        EnvironmentResponse.objects.create(
            emotion_reading=reading,
            **env_response
        )
        
        # Update session
        session, created = EmotionSession.objects.get_or_create(
            session_id=self.session_id,
            defaults={'is_active': True}
        )
        session.update_averages()
        
        # Serialize for response
        serializer = EmotionReadingSerializer(reading)
        return serializer.data
    
    @database_sync_to_async
    def update_collective_emotions(self):
        """Update and return collective emotions"""
        collective = CollectiveEmotion()
        collective.calculate_collective_emotions()
        
        serializer = CollectiveEmotionSerializer(collective)
        collective_data = serializer.data
        
        # Cache in Redis
        redis_manager.cache_collective_emotions(collective_data)
        
        return collective_data
    
    async def track_session_active(self):
        """Track session as active in Redis"""
        user_id = None
        if self.scope.get('user') and self.scope['user'].is_authenticated:
            user_id = self.scope['user'].id
        
        await database_sync_to_async(redis_manager.track_active_session)(
            self.session_id, user_id
        )
    
    async def remove_session_active(self):
        """Remove session from active tracking"""
        await database_sync_to_async(redis_manager.remove_active_session)(
            self.session_id
        )
