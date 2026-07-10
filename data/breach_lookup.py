"""
Breach Lookup Module
Loads and searches the breach dataset.
"""

import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def load_breaches(filepath: str) -> List[Dict]:
    """
    Load all breaches from JSON file.
    
    Args:
        filepath: Path to breaches.json
    
    Returns:
        List of breach dictionaries
    
    Example:
        >>> breaches = load_breaches('data/breaches.json')
        >>> print(len(breaches))
        150
    """
    try:
        if not os.path.exists(filepath):
            logger.error(f"Breaches file not found: {filepath}")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            breaches = json.load(f)
        
        logger.info(f"✅ Loaded {len(breaches)} breaches from {filepath}")
        return breaches
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in breaches.json: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading breaches: {e}")
        return []

def find_breach(query: str, breaches: List[Dict]) -> Optional[Dict]:
    """
    Find a breach by company name or ticker symbol.
    
    Search is case-insensitive and supports partial company name matches.
    
    Args:
        query: Company name or ticker (e.g., 'Equifax', 'EFX')
        breaches: List of breach dictionaries
    
    Returns:
        Breach dictionary if found, None otherwise
    
    Example:
        >>> breach = find_breach('EFX', breaches)
        >>> print(breach['company'])
        Equifax
        
        >>> breach = find_breach('equifax', breaches)
        >>> print(breach['company'])
        Equifax
    """
    if not query or not breaches:
        return None
    
    query_lower = query.strip().lower()
    
    for breach in breaches:
        # Exact ticker match (case-insensitive)
        ticker = breach.get("ticker", "").lower()
        if ticker and query_lower == ticker:
            logger.info(f"✅ Found breach by ticker: {query}")
            return breach
        
        # Partial company name match (case-insensitive)
        company = breach.get("company", "").lower()
        if query_lower in company:
            logger.info(f"✅ Found breach by company: {query}")
            return breach
    
    logger.info(f"❌ Breach not found for query: {query}")
    return None

def search_breaches(keyword: str, breaches: List[Dict]) -> List[Dict]:
    """
    Search for multiple breaches matching a keyword.
    
    Searches company name, type, and sector.
    
    Args:
        keyword: Search term
        breaches: List of breach dictionaries
    
    Returns:
        List of matching breach dictionaries
    
    Example:
        >>> results = search_breaches('ransomware', breaches)
        >>> print(len(results))
        5
    """
    if not keyword or not breaches:
        return []
    
    keyword_lower = keyword.lower()
    results = []
    
    for breach in breaches:
        company = breach.get("company", "").lower()
        breach_type = breach.get("type", "").lower()
        sector = breach.get("sector", "").lower()
        attack_vector = breach.get("attack_vector", "").lower()
        
        if (keyword_lower in company or
            keyword_lower in breach_type or
            keyword_lower in sector or
            keyword_lower in attack_vector):
            results.append(breach)
    
    logger.info(f"Found {len(results)} breaches matching '{keyword}'")
    return results

def get_breaches_by_sector(sector: str, breaches: List[Dict]) -> List[Dict]:
    """
    Get all breaches in a specific sector.
    
    Args:
        sector: Industry sector (e.g., 'Financial Services', 'Technology')
        breaches: List of breach dictionaries
    
    Returns:
        List of breaches in that sector
    """
    if not sector or not breaches:
        return []
    
    sector_lower = sector.lower()
    results = [
        b for b in breaches
        if b.get("sector", "").lower() == sector_lower
    ]
    
    logger.info(f"Found {len(results)} breaches in {sector}")
    return results

def get_breaches_by_severity(severity: str, breaches: List[Dict]) -> List[Dict]:
    """
    Get all breaches with a specific severity level.
    
    Args:
        severity: Severity level ('Critical', 'High', 'Medium')
        breaches: List of breach dictionaries
    
    Returns:
        List of breaches with that severity
    """
    if not severity or not breaches:
        return []
    
    severity_lower = severity.lower()
    results = [
        b for b in breaches
        if b.get("severity", "").lower() == severity_lower
    ]
    
    logger.info(f"Found {len(results)} {severity} breaches")
    return results
