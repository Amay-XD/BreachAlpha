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

@market_bp.route('/analyze', methods=['POST'])
@handle_errors
def analyze_breach_market_correlation():
    """
    CORE BreachAlpha Feature: Analyze breach-to-market correlation
    
    Takes company name or ticker, returns:
    - Stock price change (30 days pre/post breach)
    - S&P 500 change (same period)
    - Relative underperformance (excess loss vs market)
    - Recovery time to pre-breach price
    - AI-generated neutral analysis with "appears correlated" framing
    
    JSON Body:
        {
            "query": "EFX" or "Equifax"
        }
    
    Returns:
        {
            "found": true,
            "result": {metrics},
            "analysis": "AI analysis text"
        }
    OR
        {
            "found": false,
            "analysis": "Fallback response for unknown ticker"
        }
    """
    body = request.get_json(silent=True) or {}
    query = (body.get('query') or '').strip()
    
    if not query:
        return jsonify({'error': 'Missing "query" field'}), 400
    
    if len(query) > 50:
        return jsonify({'error': 'Query too long'}), 400
    
    # Call the core service method
    result = service.analyze_breach_with_ai(query)
    
    if result is None:
        # Breach not found in dataset - try fallback analysis
        try:
            from ai_engine.groq_analysis import analyze_no_breach
            fallback_analysis = analyze_no_breach(query)
        except (ImportError, Exception) as e:
            fallback_analysis = f'No major breach found for "{query}" in our dataset. Please check the company name or ticker symbol.'
        
        return jsonify({
            'found': False,
            'query': query,
            'analysis': fallback_analysis
        }), 200
    
    # Success - return complete correlation analysis
    return jsonify(result), 200
