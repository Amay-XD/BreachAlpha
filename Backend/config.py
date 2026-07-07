"""
Configuration management for BreachAlpha Backend.
Handles environment-based settings and validation.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # API
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
    
    # Data
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    BREACHES_JSON_PATH = os.path.join(DATA_DIR, 'breaches.json')
    
    # AI/LLM
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = 'mixtral-8x7b-32768'
    
    # Market Data
    CACHE_EXPIRY = timedelta(hours=24)
    MARKET_DATA_TIMEOUT = 30
    
    # Pagination
    ITEMS_PER_PAGE = 50
    MAX_ITEMS_PER_PAGE = 100

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Ensure critical env vars are set
    if not os.getenv('SECRET_KEY'):
        raise ValueError('SECRET_KEY environment variable not set')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATELIMIT_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
