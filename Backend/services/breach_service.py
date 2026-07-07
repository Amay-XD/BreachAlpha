"""
Breach Service.
Handles breach data operations and queries.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from Backend.config import Config

logger = logging.getLogger(__name__)

class BreachService:
    """
    Service for managing breach data.
    Loads from JSON and provides query/analysis methods.
    """
    
    def __init__(self):
        self.breaches_path = Config.BREACHES_JSON_PATH
        self.breaches = self._load_breaches()
    
    def _load_breaches(self) -> List[Dict[str, Any]]:
        """
        Load breaches from JSON file.
        
        Returns:
            List of breach dictionaries
        """
        try:
            with open(self.breaches_path, 'r') as f:
                data = json.load(f)
            
            # Handle both array and object with 'breaches' key
            if isinstance(data, dict) and 'breaches' in data:
                return data['breaches']
            elif isinstance(data, list):
                return data
            else:
                logger.warning('Unexpected JSON structure')
                return []
        
        except FileNotFoundError:
            logger.error(f'Breaches file not found: {self.breaches_path}')
            return []
        except json.JSONDecodeError as e:
            logger.error(f'JSON decode error: {e}')
            return []
    
    def get_all_breaches(self, sector: Optional[str] = None, 
                        severity: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        search: Optional[str] = None,
                        page: int = 1,
                        per_page: int = 50) -> Dict[str, Any]:
        """
        Get all breaches with filtering and pagination.
        
        Args:
            sector: Filter by sector
            severity: Filter by severity
            start_date: Filter from date (YYYY-MM-DD)
            end_date: Filter to date (YYYY-MM-DD)
            search: Search term
            page: Page number
            per_page: Items per page
        
        Returns:
            Dict with breaches list and pagination metadata
        """
        filtered = self.breaches.copy()
        
        # Apply filters
        if sector:
            filtered = [b for b in filtered if b.get('sector', '').lower() == sector.lower()]
        
        if severity:
            filtered = [b for b in filtered if b.get('severity', '').lower() == severity.lower()]
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date).date()
                filtered = [b for b in filtered if datetime.fromisoformat(b.get('breach_date', '9999-01-01')).date() >= start]
            except ValueError:
                logger.warning(f'Invalid start_date format: {start_date}')
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date).date()
                filtered = [b for b in filtered if datetime.fromisoformat(b.get('breach_date', '0000-01-01')).date() <= end]
            except ValueError:
                logger.warning(f'Invalid end_date format: {end_date}')
        
        if search:
            search_lower = search.lower()
            filtered = [b for b in filtered if 
                       search_lower in b.get('company', '').lower() or
                       search_lower in b.get('summary', '').lower()]
        
        # Pagination
        total = len(filtered)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = filtered[start_idx:end_idx]
        
        return {
            'breaches': paginated,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'filters': {
                'sector': sector,
                'severity': severity,
                'start_date': start_date,
                'end_date': end_date,
                'search': search
            }
        }
    
    def get_breach_by_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get breach by company name.
        
        Args:
            company_name: Company name
        
        Returns:
            Breach dict or None
        """
        for breach in self.breaches:
            if breach.get('company', '').lower() == company_name.lower():
                return breach
        return None
    
    def get_breach_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get breach by company ticker.
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Breach dict or None
        """
        for breach in self.breaches:
            breach_ticker = breach.get('ticker', '').upper()
            if breach_ticker == ticker.upper() or breach_ticker.endswith(ticker.upper()):
                return breach
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics about breaches.
        
        Returns:
            Dict with statistics
        """
        sectors = {}
        severities = {'Critical': 0, 'High': 0, 'Medium': 0}
        types = {}
        years = {}
        total_records = 0
        
        for breach in self.breaches:
            # Sector counts
            sector = breach.get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + 1
            
            # Severity counts
            severity = breach.get('severity', 'Unknown')
            if severity in severities:
                severities[severity] += 1
            
            # Type counts
            breach_type = breach.get('type', 'Unknown')
            types[breach_type] = types.get(breach_type, 0) + 1
            
            # Year counts
            try:
                year = datetime.fromisoformat(breach.get('breach_date', '0000-01-01')).year
                years[year] = years.get(year, 0) + 1
            except ValueError:
                pass
            
            # Parse records affected
            records_str = breach.get('records_affected', 'Unknown')
            if records_str != 'Unknown':
                try:
                    if 'M' in records_str:
                        total_records += int(records_str.replace('M', '')) * 1_000_000
                    elif 'K' in records_str:
                        total_records += int(records_str.replace('K', '')) * 1_000
                except ValueError:
                    pass
        
        return {
            'total_breaches': len(self.breaches),
            'total_records_affected': total_records,
            'sectors': sectors,
            'severities': severities,
            'types': types,
            'by_year': dict(sorted(years.items()))
        }
    
    def create_breach(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new breach record.
        
        Args:
            data: Breach data
        
        Returns:
            Created breach dict
        """
        self.breaches.append(data)
        self._save_breaches()
        return data
    
    def update_breach(self, company_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a breach record.
        
        Args:
            company_name: Company name
            data: Updated data
        
        Returns:
            Updated breach dict or None
        """
        for breach in self.breaches:
            if breach.get('company', '').lower() == company_name.lower():
                breach.update(data)
                self._save_breaches()
                return breach
        return None
    
    def delete_breach(self, company_name: str) -> bool:
        """
        Delete a breach record.
        
        Args:
            company_name: Company name
        
        Returns:
            True if deleted, False if not found
        """
        initial_count = len(self.breaches)
        self.breaches = [b for b in self.breaches if b.get('company', '').lower() != company_name.lower()]
        
        if len(self.breaches) < initial_count:
            self._save_breaches()
            return True
        return False
    
    def _save_breaches(self):
        """
        Save breaches to JSON file.
        """
        try:
            with open(self.breaches_path, 'w') as f:
                json.dump(self.breaches, f, indent=2)
            logger.info('Breaches saved successfully')
        except IOError as e:
            logger.error(f'Error saving breaches: {e}')
