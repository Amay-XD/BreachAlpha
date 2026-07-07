"""
Analysis Service.
Provides breach pattern analysis and insights.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
from Backend.services.breach_service import BreachService

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Service for analyzing breach data and patterns.
    """
    
    def __init__(self):
        self.breach_service = BreachService()
    
    def analyze_patterns(self, year: Optional[int] = None, sector: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze breach patterns.
        
        Args:
            year: Filter by year
            sector: Filter by sector
        
        Returns:
            Dict with pattern analysis
        """
        breaches = self.breach_service.breaches
        
        # Filter by year
        if year:
            breaches = [b for b in breaches if datetime.fromisoformat(b.get('breach_date', '0000-01-01')).year == year]
        
        # Filter by sector
        if sector:
            breaches = [b for b in breaches if b.get('sector', '').lower() == sector.lower()]
        
        # Analyze
        attack_vectors = Counter([b.get('attack_vector', 'Unknown') for b in breaches])
        types = Counter([b.get('type', 'Unknown') for b in breaches])
        
        return {
            'total_breaches_in_period': len(breaches),
            'most_common_attack_vectors': dict(attack_vectors.most_common(5)),
            'breach_types': dict(types),
            'filters': {'year': year, 'sector': sector}
        }
    
    def analyze_attack_vectors(self) -> Dict[str, Any]:
        """
        Analyze most common attack vectors.
        
        Returns:
            Dict with attack vector statistics
        """
        breaches = self.breach_service.breaches
        vectors = Counter([b.get('attack_vector', 'Unknown') for b in breaches])
        
        return {
            'total_unique_vectors': len(vectors),
            'attack_vectors': dict(vectors.most_common(10)),
            'total_incidents': len(breaches)
        }
    
    def calculate_sector_risk(self) -> Dict[str, Any]:
        """
        Calculate risk scores by sector.
        
        Returns:
            Dict with sector risk rankings
        """
        breaches = self.breach_service.breaches
        sectors = {}
        
        for breach in breaches:
            sector = breach.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = {'count': 0, 'critical': 0, 'high': 0, 'medium': 0}
            
            sectors[sector]['count'] += 1
            severity = breach.get('severity', 'Unknown')
            if severity == 'Critical':
                sectors[sector]['critical'] += 1
            elif severity == 'High':
                sectors[sector]['high'] += 1
            elif severity == 'Medium':
                sectors[sector]['medium'] += 1
        
        # Calculate risk scores (weighted)
        risk_scores = {}
        for sector, data in sectors.items():
            risk_score = (data['critical'] * 10) + (data['high'] * 5) + (data['medium'] * 2)
            risk_scores[sector] = {
                'risk_score': risk_score,
                'total_breaches': data['count'],
                'critical': data['critical'],
                'high': data['high'],
                'medium': data['medium']
            }
        
        # Sort by risk score
        sorted_sectors = dict(sorted(risk_scores.items(), key=lambda x: x[1]['risk_score'], reverse=True))
        
        return {'sector_risk_rankings': sorted_sectors}
    
    def get_timeline(self, granularity: str = 'year') -> Dict[str, Any]:
        """
        Get timeline of breaches.
        
        Args:
            granularity: 'year', 'quarter', 'month'
        
        Returns:
            Dict with timeline data
        """
        breaches = self.breach_service.breaches
        timeline = {}
        
        for breach in breaches:
            try:
                date = datetime.fromisoformat(breach.get('breach_date', '0000-01-01'))
                
                if granularity == 'year':
                    key = str(date.year)
                elif granularity == 'quarter':
                    quarter = (date.month - 1) // 3 + 1
                    key = f'{date.year}-Q{quarter}'
                elif granularity == 'month':
                    key = date.strftime('%Y-%m')
                else:
                    key = str(date.year)
                
                timeline[key] = timeline.get(key, 0) + 1
            
            except ValueError:
                pass
        
        return {'timeline': dict(sorted(timeline.items())), 'granularity': granularity}
    
    def get_severity_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of severity levels.
        
        Returns:
            Dict with severity distribution
        """
        breaches = self.breach_service.breaches
        distribution = Counter([b.get('severity', 'Unknown') for b in breaches])
        
        return {'severity_distribution': dict(distribution)}
