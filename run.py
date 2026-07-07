#!/usr/bin/env python3
"""
Entry point for BreachAlpha Flask application.

Usage:
    python run.py                    # Development mode
    FLASK_ENV=production python run.py  # Production mode
    gunicorn -w 4 -b 0.0.0.0:5000 run:app  # Production with gunicorn
"""

import os
from Backend.app import create_app

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
