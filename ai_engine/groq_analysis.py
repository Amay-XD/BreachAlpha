"""
Groq AI Analysis Module.
Provides AI-powered analysis of breach-to-market correlation.
"""

import os
import logging
from typing import Dict, Any

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

client = None
if GROQ_AVAILABLE:
    try:
        api_key = os.getenv('GROQ_API_KEY')
        if api_key:
            client = Groq(api_key=api_key)
    except Exception as e:
        logger.warning(f'Groq client initialization failed: {e}')

def analyze_breach_impact(correlation_result: Dict[str, Any]) -> str:
    """
    Use Groq AI to analyze breach-to-market correlation.
    
    Args:
        correlation_result: Dict with correlation metrics
    
    Returns:
        AI-generated analysis text
    """
    if not client or not GROQ_AVAILABLE:
        logger.warning('Groq client not available, using fallback analysis')
        return _fallback_breach_analysis(correlation_result)
    
    try:
        company = correlation_result['company']
        ticker = correlation_result['ticker']
        breach_date = correlation_result['breach_date']
        breach_type = correlation_result['breach_type']
        records = correlation_result['records_affected']
        sector = correlation_result['sector']
        severity = correlation_result['severity']
        company_change = correlation_result['company_pct_change']
        market_change = correlation_result['market_pct_change']
        relative_impact = correlation_result['relative_impact']
        recovery_days = correlation_result['recovery_days']
        recovery_text = correlation_result['recovery_text']
        
        prompt = f"""
Analyze the correlation between a data breach and stock market performance. 
Provide a neutral, factual analysis that describes what the data shows WITHOUT claiming causation.

Breach Details:
- Company: {company} ({ticker})
- Breach Date: {breach_date}
- Breach Type: {breach_type}
- Records Affected: {records}
- Sector: {sector}
- Severity: {severity}

Market Analysis (60-day window around breach):
- Company Stock Change: {company_change}%
- S&P 500 Change: {market_change}%
- Relative Impact: {relative_impact}% (company performance vs market)
- Recovery: {recovery_text}

Your task: Write a 2-3 sentence analysis that:
1. Describes what the correlation shows (or doesn't show)
2. Mentions the relative impact metric
3. Notes recovery trajectory
4. IMPORTANT: Use language like "appears correlated" or "shows correlation" - NOT "caused" or "due to"
5. End with a disclaimer about correlation vs causation

Analysis:
"""
        
        message = client.messages.create(
            model='llama-3.3-70b-versatile',
            max_tokens=300,
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        
        analysis = message.content[0].text if message.content else _fallback_breach_analysis(correlation_result)
        return analysis.strip()
    
    except Exception as e:
        logger.error(f'Groq analysis failed: {e}')
        return _fallback_breach_analysis(correlation_result)

def analyze_no_breach(query: str) -> str:
    """
    Provide analysis when breach is not found in dataset.
    
    Args:
        query: User's search query
    
    Returns:
        Analysis text
    """
    if not client or not GROQ_AVAILABLE:
        return _fallback_no_breach(query)
    
    try:
        prompt = f"""
The user searched for "{query}" in a database of major data breaches (2010-2024).
No matching breach was found.

Provide a helpful 1-2 sentence response that:
1. Confirms no major breach was found for this query
2. Suggests it might be a private company, minor breach, or incorrect spelling
3. Invites them to search for other companies

Response:
"""
        
        message = client.messages.create(
            model='llama-3.3-70b-versatile',
            max_tokens=150,
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        
        return message.content[0].text if message.content else _fallback_no_breach(query)
    
    except Exception as e:
        logger.error(f'Groq no_breach analysis failed: {e}')
        return _fallback_no_breach(query)

def _fallback_breach_analysis(correlation_result: Dict[str, Any]) -> str:
    """
    Fallback analysis when Groq is unavailable.
    """
    company = correlation_result['company']
    relative = correlation_result['relative_impact']
    recovery = correlation_result['recovery_text']
    severity = correlation_result['severity']
    
    if abs(relative) < 2:
        correlation_desc = 'minimal correlation'
    elif abs(relative) < 5:
        correlation_desc = 'moderate correlation'
    elif abs(relative) < 10:
        correlation_desc = 'strong correlation'
    else:
        correlation_desc = 'very strong correlation'
    
    analysis = (
        f"{company}'s stock appears to show {correlation_desc} with the {severity.lower()} severity breach disclosure. "
        f"The stock declined {abs(relative):.1f}% more than the broader market during the 60-day analysis window. "
        f"{recovery}. Note: Market correlation does not imply causation; multiple factors influence stock price movements."
    )
    
    return analysis

def _fallback_no_breach(query: str) -> str:
    """
    Fallback response when breach is not found.
    """
    return (
        f'No major breach found for "{query}" in our database covering 2010-2024. '
        f'This could mean the company is private, the breach was below our reporting threshold, '
        f'or there may be a spelling difference. Try searching by ticker symbol or alternative company name.'
    )
