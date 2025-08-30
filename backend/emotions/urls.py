from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, auth_views

router = DefaultRouter()
router.register(r'readings', views.EmotionReadingViewSet)
router.register(r'sessions', views.EmotionSessionViewSet)
router.register(r'collective', views.CollectiveEmotionViewSet)
router.register(r'environment', views.EnvironmentResponseViewSet)
router.register(r'system', views.SystemViewSet, basename='system')

urlpatterns = [
    path('api/', include(router.urls)),
    # Authentication endpoints
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login_user, name='login'),
    path('auth/logout/', auth_views.logout_user, name='logout'),
    path('auth/profile/', auth_views.profile, name='profile'),
    path('auth/profile/update/', auth_views.update_profile, name='update_profile'),
]
