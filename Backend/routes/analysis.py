"""
Analysis API endpoints.
Provides breach pattern analysis and insights.
"""

from flask import Blueprint, request, jsonify
from Backend.services.analysis_service import AnalysisService
from Backend.utils.decorators import handle_errors

analysis_bp = Blueprint('analysis', __name__)
service = AnalysisService()

@analysis_bp.route('/patterns', methods=['GET'])
@handle_errors
def get_breach_patterns():
    """
    Analyze breach patterns and trends.
    
    Query Parameters:
        - year: Filter by year
        - sector: Filter by sector
    
    Returns:
        JSON with pattern analysis
    """
    year = request.args.get('year', type=int)
    sector = request.args.get('sector', type=str)
    
    patterns = service.analyze_patterns(year=year, sector=sector)
    
    return jsonify(patterns), 200

@analysis_bp.route('/attack-vectors', methods=['GET'])
@handle_errors
def get_attack_vector_analysis():
    """
    Analyze most common attack vectors.
    
    Returns:
        JSON with attack vector statistics
    """
    analysis = service.analyze_attack_vectors()
    
    return jsonify(analysis), 200

@analysis_bp.route('/sector-risk', methods=['GET'])
@handle_errors
def get_sector_risk_assessment():
    """
    Calculate risk scores by sector.
    
    Returns:
        JSON with sector risk rankings
    """
    risk_assessment = service.calculate_sector_risk()
    
    return jsonify(risk_assessment), 200

@analysis_bp.route('/timeline', methods=['GET'])
@handle_errors
def get_breach_timeline():
    """
    Get timeline of breaches over time.
    
    Query Parameters:
        - granularity: 'year', 'quarter', 'month' (default: 'year')
    
    Returns:
        JSON with timeline data
    """
    granularity = request.args.get('granularity', 'year', type=str)
    
    timeline = service.get_timeline(granularity)
    
    return jsonify(timeline), 200

@analysis_bp.route('/severity-distribution', methods=['GET'])
@handle_errors
def get_severity_distribution():
    """
    Get distribution of breach severity levels.
    
    Returns:
        JSON with severity distribution
    """
    distribution = service.get_severity_distribution()
    
    return jsonify(distribution), 200
