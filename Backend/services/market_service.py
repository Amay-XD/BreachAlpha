"""
Market Service.
Analyzes financial and market impact of breaches.
"""

import logging
from typing import Dict, Any, Optional
import yfinance as yf
from datetime import datetime, timedelta
from Backend.services.breach_service import BreachService

logger = logging.getLogger(__name__)

class MarketService:
    """
    Service for analyzing market impact of breaches.
    Integrates with yfinance for stock data.
    """
    
    def __init__(self):
        self.breach_service = BreachService()
    
    def calculate_market_impact(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Calculate market impact of a breach.
        
        Args:
            company_name: Company name
        
        Returns:
            Dict with market impact metrics or None
        """
        breach = self.breach_service.get_breach_by_company(company_name)
        
        if not breach or not breach.get('ticker'):
            return None
        
        ticker = breach.get('ticker')
        breach_date_str = breach.get('breach_date')
        
        try:
            breach_date = datetime.fromisoformat(breach_date_str).date()
        except ValueError:
            return None
        
        # Fetch stock data
        try:
            stock = yf.Ticker(ticker.split(':')[1] if ':' in ticker else ticker)
            
            # Get data for 30 days before and after breach
            start_date = breach_date - timedelta(days=30)
            end_date = breach_date + timedelta(days=30)
            
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            # Calculate impact
            price_before = hist['Close'].iloc[0] if len(hist) > 0 else None
            price_after = hist['Close'].iloc[-1] if len(hist) > 0 else None
            
            if price_before and price_after:
                price_change = ((price_after - price_before) / price_before) * 100
            else:
                price_change = 0
            
            return {
                'company': company_name,
                'ticker': ticker,
                'breach_date': breach_date_str,
                'price_before_breach': round(price_before, 2) if price_before else None,
                'price_after_breach': round(price_after, 2) if price_after else None,
                'price_change_percent': round(price_change, 2),
                'analysis_period': f'{start_date} to {end_date}',
                'note': 'Impact calculated from 30 days before to 30 days after breach disclosure'
            }
        
        except Exception as e:
            logger.error(f'Error fetching stock data for {ticker}: {e}')
            return None
    
    def analyze_recovery(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Analyze breach recovery timeline.
        
        Args:
            company_name: Company name
        
        Returns:
            Dict with recovery metrics or None
        """
        breach = self.breach_service.get_breach_by_company(company_name)
        
        if not breach:
            return None
        
        # Calculate estimated recovery based on historical data
        severity = breach.get('severity', 'High')
        records_affected = breach.get('records_affected', 'Unknown')
        
        # Rough estimates based on historical patterns
        recovery_estimates = {
            'Critical': {'months': 12, 'stock_recovery_percent': -15},
            'High': {'months': 6, 'stock_recovery_percent': -8},
            'Medium': {'months': 3, 'stock_recovery_percent': -3}
        }
        
        estimate = recovery_estimates.get(severity, recovery_estimates['High'])
        
        return {
            'company': company_name,
            'breach_date': breach.get('breach_date'),
            'severity': severity,
            'records_affected': records_affected,
            'estimated_recovery_months': estimate['months'],
            'estimated_stock_impact_percent': estimate['stock_recovery_percent'],
            'note': 'Estimates based on historical breach recovery patterns'
        }
    
    def calculate_financial_impact(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Calculate estimated financial impact.
        
        Args:
            company_name: Company name
        
        Returns:
            Dict with financial impact or None
        """
        breach = self.breach_service.get_breach_by_company(company_name)
        
        if not breach:
            return None
        
        records_str = breach.get('records_affected', 'Unknown')
        severity = breach.get('severity', 'High')
        sector = breach.get('sector', 'Unknown')
        
        # Parse records
        try:
            if 'M' in records_str:
                records = int(records_str.replace('M', '')) * 1_000_000
            elif 'K' in records_str:
                records = int(records_str.replace('K', '')) * 1_000
            else:
                records = 0
        except ValueError:
            records = 0
        
        # Estimate costs
        # Average cost per compromised record: $150-$200
        # Regulatory fines: 2-4% of revenue (variable)
        # Incident response: $1M-$10M depending on severity
        
        cost_per_record = 150  # Conservative estimate
        breach_remediation_cost = records * cost_per_record
        
        incident_response = {'Critical': 5_000_000, 'High': 2_000_000, 'Medium': 500_000}.get(severity, 1_000_000)
        
        # Regulatory fines (variable by sector and jurisdiction)
        regulatory_multiplier = {'Financial Services': 0.04, 'Healthcare': 0.03, 'Technology': 0.02}.get(sector, 0.015)
        estimated_regulatory = records * cost_per_record * regulatory_multiplier
        
        total_estimated = breach_remediation_cost + incident_response + estimated_regulatory
        
        return {
            'company': company_name,
            'breach_date': breach.get('breach_date'),
            'records_affected': records_str,
            'sector': sector,
            'severity': severity,
            'cost_breakdown': {
                'breach_remediation_cost': round(breach_remediation_cost, 2),
                'incident_response_cost': incident_response,
                'estimated_regulatory_fines': round(estimated_regulatory, 2)
            },
            'total_estimated_impact': round(total_estimated, 2),
            'currency': 'USD',
            'note': 'Estimates based on historical averages and industry benchmarks'
        }
    
    def get_sector_impact(self) -> Dict[str, Any]:
        """
        Get aggregate market impact by sector.
        
        Returns:
            Dict with sector-level impact metrics
        """
        breaches = self.breach_service.breaches
        sectors = {}
        
        for breach in breaches:
            sector = breach.get('sector', 'Unknown')
            
            if sector not in sectors:
                sectors[sector] = {
                    'breaches': 0,
                    'critical': 0,
                    'total_records': 0,
                    'total_estimated_impact': 0
                }
            
            sectors[sector]['breaches'] += 1
            
            if breach.get('severity') == 'Critical':
                sectors[sector]['critical'] += 1
            
            # Parse records
            records_str = breach.get('records_affected', '0')
            try:
                if 'M' in records_str:
                    records = int(records_str.replace('M', '')) * 1_000_000
                elif 'K' in records_str:
                    records = int(records_str.replace('K', '')) * 1_000
                else:
                    records = 0
                sectors[sector]['total_records'] += records
            except ValueError:
                pass
        
        return {
            'sector_impact_summary': sectors,
            'note': 'Aggregate metrics by sector'
        }
    
    def analyze_correlation(self) -> Dict[str, Any]:
        """
        Analyze correlation between breach disclosure and stock price.
        
        Returns:
            Dict with correlation analysis
        """
        # This would require more detailed historical data
        # For now, return summary of available data
        
        breaches_with_tickers = [b for b in self.breach_service.breaches if b.get('ticker')]
        
        return {
            'breaches_with_market_data': len(breaches_with_tickers),
            'total_breaches': len(self.breach_service.breaches),
            'note': 'Detailed correlation analysis requires extended historical data'
        }
