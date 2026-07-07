"""
BreachAlpha Flask Application Factory.
Initializes and configures the Flask app with all extensions.
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from Backend.config import config
from Backend.utils.logger import setup_logger
from Backend.routes import api_bp

def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: 'development', 'production', 'testing'
    
    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logger(app)
    logger = logging.getLogger(__name__)
    logger.info(f'Creating BreachAlpha app with config: {config_name}')
    
    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=['200 per day', '50 per hour'],
        storage_uri=app.config['RATELIMIT_STORAGE_URL']
    )
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Error handlers
    register_error_handlers(app)
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'BreachAlpha'}, 200
    
    logger.info('BreachAlpha app initialized successfully')
    return app

def register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found', 'status': 404}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f'Internal server error: {error}')
        return {'error': 'Internal server error', 'status': 500}, 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {'error': 'Rate limit exceeded', 'status': 429}, 429

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
