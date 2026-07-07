"""
Market Impact API endpoints.
Analyzes financial and market impact of breaches.
"""

from flask import Blueprint, request, jsonify
from Backend.services.market_service import MarketService
from Backend.utils.decorators import handle_errors

market_bp = Blueprint('market', __name__)
service = MarketService()

@market_bp.route('/impact/<company_name>', methods=['GET'])
@handle_errors
def get_market_impact(company_name):
    """
    Get market impact analysis for a company's breach.
    
    Args:
        company_name: Company name
    
    Returns:
        JSON with stock price, market cap changes, etc.
    """
    impact = service.calculate_market_impact(company_name)
    
    if not impact:
        return jsonify({'error': 'Data not available', 'company': company_name}), 404
    
    return jsonify(impact), 200

@market_bp.route('/recovery/<company_name>', methods=['GET'])
@handle_errors
def get_recovery_analysis(company_name):
    """
    Analyze breach recovery timeline and metrics.
    
    Args:
        company_name: Company name
    
    Returns:
        JSON with recovery timeline and milestones
    """
    recovery = service.analyze_recovery(company_name)
    
    if not recovery:
        return jsonify({'error': 'Data not available', 'company': company_name}), 404
    
    return jsonify(recovery), 200

@market_bp.route('/financial-impact/<company_name>', methods=['GET'])
@handle_errors
def get_financial_impact(company_name):
    """
    Calculate estimated financial impact of breach.
    
    Args:
        company_name: Company name
    
    Returns:
        JSON with financial impact estimates (fines, losses, etc.)
    """
    impact = service.calculate_financial_impact(company_name)
    
    if not impact:
        return jsonify({'error': 'Data not available', 'company': company_name}), 404
    
    return jsonify(impact), 200

@market_bp.route('/sector-impact', methods=['GET'])
@handle_errors
def get_sector_market_impact():
    """
    Get aggregate market impact by sector.
    
    Returns:
        JSON with sector-level impact metrics
    """
    sector_impact = service.get_sector_impact()
    
    return jsonify(sector_impact), 200

@market_bp.route('/correlation', methods=['GET'])
@handle_errors
def get_breach_market_correlation():
    """
    Analyze correlation between breach disclosure and stock price.
    
    Returns:
        JSON with correlation analysis
    """
    correlation = service.analyze_correlation()
    
    return jsonify(correlation), 200
