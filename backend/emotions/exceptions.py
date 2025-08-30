from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Custom exception handler for API errors"""
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error
        logger.error(f"API Error: {exc} - Context: {context}")
        
        # Customize error response format
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Specific error messages for common cases
        if response.status_code == 400:
            custom_response_data['message'] = 'Invalid data provided'
        elif response.status_code == 404:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == 500:
            custom_response_data['message'] = 'Internal server error'
        
        response.data = custom_response_data
    
    return response

class APIResponseMixin:
    """Mixin for standardized API responses"""
    
    @staticmethod
    def success_response(data, message="Success", status_code=200):
        """Standard success response format"""
        return Response({
            'success': True,
            'message': message,
            'data': data,
            'status_code': status_code
        }, status=status_code)
    
    @staticmethod
    def error_response(message, details=None, status_code=400):
        """Standard error response format"""
        response_data = {
            'success': False,
            'error': True,
            'message': message,
            'status_code': status_code
        }
        
        if details:
            response_data['details'] = details
        
        return Response(response_data, status=status_code)
