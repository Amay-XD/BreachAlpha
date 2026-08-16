#!/usr/bin/env python3
"""
Entry point for BreachAlpha Flask application.

Architecture:
  - backend/app.py creates ONE authoritative Flask app instance at module load
  - Routes are registered to this instance via @app.route(...) decorators
  - This script imports that existing instance and serves it
  - NO duplicate app creation

Usage:
    python run.py                       # Development mode
    FLASK_ENV=production python run.py  # Production mode
    gunicorn -w 4 -b 0.0.0.0:5000 run:app  # Production with gunicorn
"""
import os
from backend.app import app

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
