"""
Data validators.
"""

from typing import Dict, Any, List
from datetime import datetime

REQUIRED_BREACH_FIELDS = ['company', 'ticker', 'breach_date', 'type', 'records_affected', 'sector', 'attack_vector', 'severity', 'summary']

VALID_SEVERITIES = ['Critical', 'High', 'Medium']

VALID_SECTORS = [
    'Finance & Banking', 'Healthcare & Pharma', 'Retail & E-commerce',
    'Technology & Software', 'Government & Defense', 'Energy & Utilities',
    'Telecommunications', 'Manufacturing & Industrial', 'Hospitality & Travel',
    'Media & Entertainment', 'Education', 'Insurance', 'Transportation'
]

def validate_breach_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate breach data.
    
    Args:
        data: Breach data dict
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    for field in REQUIRED_BREACH_FIELDS:
        if field not in data or not data[field]:
            errors.append(f'Missing required field: {field}')
    
    # Validate severity
    if 'severity' in data and data['severity'] not in VALID_SEVERITIES:
        errors.append(f'Invalid severity: {data["severity"]}')
    
    # Validate sector
    if 'sector' in data and data['sector'] not in VALID_SECTORS:
        errors.append(f'Invalid sector: {data["sector"]}')
    
    # Validate date format
    if 'breach_date' in data:
        try:
            datetime.fromisoformat(data['breach_date'])
        except ValueError:
            errors.append('Invalid breach_date format (expected YYYY-MM-DD)')
    
    return errors

def validate_query_params(args) -> Dict[str, Any]:
    """
    Validate and extract query parameters.
    
    Args:
        args: Flask request.args
    
    Returns:
        Dict with validated parameters
    """
    return {
        'sector': args.get('sector'),
        'severity': args.get('severity'),
        'start_date': args.get('start_date'),
        'end_date': args.get('end_date'),
        'search': args.get('search'),
        'page': int(args.get('page', 1)),
        'per_page': min(int(args.get('per_page', 50)), 100)
    }
