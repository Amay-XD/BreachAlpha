"""
API Routes Blueprint.
Aggregates all route blueprints.
"""

from flask import Blueprint
from Backend.routes.breaches import breaches_bp
from Backend.routes.analysis import analysis_bp
from Backend.routes.market import market_bp

api_bp = Blueprint('api', __name__)

# Register sub-blueprints
api_bp.register_blueprint(breaches_bp, url_prefix='/breaches')
api_bp.register_blueprint(analysis_bp, url_prefix='/analysis')
api_bp.register_blueprint(market_bp, url_prefix='/market')

__all__ = ['api_bp']
