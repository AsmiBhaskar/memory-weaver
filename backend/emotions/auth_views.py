from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from .auth_serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer
from .exceptions import APIResponseMixin

class AuthMixin(APIResponseMixin):
    pass

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return AuthMixin.success_response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Registration successful'
        }, "User registered successfully", status.HTTP_201_CREATED)
    
    return AuthMixin.error_response(
        "Registration failed", 
        serializer.errors, 
        status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login user and return token"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return AuthMixin.success_response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        }, "Login successful")
    
    return AuthMixin.error_response(
        "Login failed", 
        serializer.errors, 
        status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Logout user and delete token"""
    try:
        request.user.auth_token.delete()
        return AuthMixin.success_response(
            {'message': 'Logout successful'}, 
            "Logout successful"
        )
    except:
        return AuthMixin.error_response("Logout failed")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get user profile"""
    serializer = UserProfileSerializer(request.user)
    return AuthMixin.success_response(
        serializer.data, 
        "Profile retrieved successfully"
    )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return AuthMixin.success_response(
            serializer.data, 
            "Profile updated successfully"
        )
    
    return AuthMixin.error_response(
        "Profile update failed", 
        serializer.errors, 
        status.HTTP_400_BAD_REQUEST
    )
