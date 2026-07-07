"""
Custom Flask decorators.
"""

import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

def handle_errors(f):
    """
    Decorator to catch and handle errors in route handlers.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f'Error in {f.__name__}: {str(e)}')
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
    return decorated_function

def require_auth(f):
    """
    Decorator to require authentication (API key).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        
        # TODO: Validate API key against database
        # For now, accept any non-empty key
        if not api_key or len(api_key) < 10:
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
