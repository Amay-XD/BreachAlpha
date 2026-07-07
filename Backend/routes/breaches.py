"""
Breaches API endpoints.
Manages CRUD operations and querying of breach data.
"""

from flask import Blueprint, request, jsonify
from Backend.services.breach_service import BreachService
from Backend.utils.validators import validate_query_params, validate_breach_data
from Backend.utils.decorators import handle_errors, require_auth

breaches_bp = Blueprint('breaches', __name__)
service = BreachService()

@breaches_bp.route('/', methods=['GET'])
@handle_errors
def get_breaches():
    """
    Get all breaches with filtering and pagination.
    
    Query Parameters:
        - sector: Filter by sector
        - severity: Filter by severity (Critical, High, Medium)
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        - page: Page number (default 1)
        - per_page: Items per page (default 50, max 100)
        - search: Search in company name or summary
    
    Returns:
        JSON with paginated breach list and metadata
    """
    # Validate and extract params
    params = validate_query_params(request.args)
    
    # Fetch breaches
    result = service.get_all_breaches(**params)
    
    return jsonify(result), 200

@breaches_bp.route('/<company_name>', methods=['GET'])
@handle_errors
def get_breach_by_company(company_name):
    """
    Get breach details by company name.
    
    Args:
        company_name: Company name (URL parameter)
    
    Returns:
        JSON with breach details
    """
    breach = service.get_breach_by_company(company_name)
    
    if not breach:
        return jsonify({'error': 'Breach not found', 'company': company_name}), 404
    
    return jsonify(breach), 200

@breaches_bp.route('/ticker/<ticker>', methods=['GET'])
@handle_errors
def get_breach_by_ticker(ticker):
    """
    Get breach details by company ticker.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        JSON with breach details
    """
    breach = service.get_breach_by_ticker(ticker)
    
    if not breach:
        return jsonify({'error': 'Breach not found', 'ticker': ticker}), 404
    
    return jsonify(breach), 200

@breaches_bp.route('/sector/<sector>', methods=['GET'])
@handle_errors
def get_breaches_by_sector(sector):
    """
    Get all breaches in a specific sector.
    
    Args:
        sector: Industry sector
    
    Returns:
        JSON with breach list filtered by sector
    """
    params = validate_query_params(request.args)
    params['sector'] = sector
    
    result = service.get_all_breaches(**params)
    
    return jsonify(result), 200

@breaches_bp.route('/stats', methods=['GET'])
@handle_errors
def get_breach_statistics():
    """
    Get aggregated statistics about breaches.
    
    Returns:
        JSON with statistics (counts by sector, severity, etc.)
    """
    stats = service.get_statistics()
    
    return jsonify(stats), 200

@breaches_bp.route('/', methods=['POST'])
@require_auth
@handle_errors
def create_breach():
    """
    Add a new breach to the database.
    Requires authentication.
    
    JSON Body:
        breach object with all required fields
    
    Returns:
        JSON with created breach and 201 status
    """
    data = request.get_json()
    
    # Validate data
    errors = validate_breach_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Create breach
    breach = service.create_breach(data)
    
    return jsonify(breach), 201

@breaches_bp.route('/<company_name>', methods=['PUT'])
@require_auth
@handle_errors
def update_breach(company_name):
    """
    Update an existing breach.
    Requires authentication.
    
    Args:
        company_name: Company name (URL parameter)
    
    JSON Body:
        Fields to update
    
    Returns:
        JSON with updated breach
    """
    data = request.get_json()
    
    breach = service.update_breach(company_name, data)
    
    if not breach:
        return jsonify({'error': 'Breach not found', 'company': company_name}), 404
    
    return jsonify(breach), 200

@breaches_bp.route('/<company_name>', methods=['DELETE'])
@require_auth
@handle_errors
def delete_breach(company_name):
    """
    Delete a breach record.
    Requires authentication.
    
    Args:
        company_name: Company name (URL parameter)
    
    Returns:
        JSON confirmation or 404
    """
    success = service.delete_breach(company_name)
    
    if not success:
        return jsonify({'error': 'Breach not found', 'company': company_name}), 404
    
    return jsonify({'message': 'Breach deleted successfully', 'company': company_name}), 200
