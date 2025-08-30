from django.urls import re_path
from emotions import consumers

websocket_urlpatterns = [
    re_path(r'ws/emotions/$', consumers.EmotionConsumer.as_asgi()),
]
