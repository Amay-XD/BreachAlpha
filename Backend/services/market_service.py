"""
Market Service.
Analyzes financial and market impact of breaches.
"""

import logging
import os
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
    
    def analyze_breach_with_ai(self, query: str) -> Optional[Dict[str, Any]]:
        """
        CORE BreachAlpha FEATURE: Analyze breach-to-market correlation with AI
        
        Steps:
        1. Find breach by company name or ticker
        2. Fetch company stock data (30 days pre/post breach)
        3. Fetch S&P 500 data (same period)
        4. Calculate relative underperformance
        5. Calculate recovery time
        6. Call Groq AI for analysis
        
        Args:
            query: Company name or ticker symbol
        
        Returns:
            Dict with correlation data and AI analysis, or None if breach not found
        """
        try:
            # Step 1: Find breach by company name or ticker
            breach = self.breach_service.get_breach_by_company(query)
            if not breach:
                breach = self.breach_service.get_breach_by_ticker(query)
            
            if not breach:
                logger.info(f'Breach not found for query: {query}')
                return None
            
            # Step 2: Extract breach info
            company_name = breach.get('company')
            ticker = breach.get('ticker')
            breach_date_str = breach.get('breach_date')
            
            if not ticker or ticker == 'null' or ticker is None:
                logger.warning(f'No valid ticker for {company_name}')
                return None
            
            # Parse ticker (handle "NYSE:XXX" format)
            ticker_symbol = ticker.split(':')[1] if ':' in ticker else ticker
            
            # Step 3: Parse breach date
            try:
                breach_date = datetime.fromisoformat(breach_date_str).date()
            except (ValueError, TypeError):
                logger.error(f'Invalid breach date: {breach_date_str}')
                return None
            
            # Step 4: Fetch company stock data
            start_date = breach_date - timedelta(days=30)
            end_date = breach_date + timedelta(days=30)
            
            try:
                company_stock = yf.Ticker(ticker_symbol)
                company_hist = company_stock.history(start=start_date, end=end_date)
                
                if company_hist.empty or len(company_hist) < 2:
                    logger.warning(f'Insufficient data for {ticker_symbol}')
                    return None
            
            except Exception as e:
                logger.error(f'Error fetching company stock data for {ticker_symbol}: {e}')
                return None
            
            # Step 5: Fetch S&P 500 data
            try:
                sp500 = yf.Ticker('^GSPC')
                sp500_hist = sp500.history(start=start_date, end=end_date)
                
                if sp500_hist.empty or len(sp500_hist) < 2:
                    logger.warning('Insufficient S&P 500 data')
                    return None
            
            except Exception as e:
                logger.error(f'Error fetching S&P 500 data: {e}')
                return None
            
            # Step 6: Calculate company % change
            company_first_price = company_hist['Close'].iloc[0]
            company_last_price = company_hist['Close'].iloc[-1]
            company_change = ((company_last_price - company_first_price) / company_first_price) * 100
            
            # Step 7: Calculate S&P 500 % change
            sp500_first_price = sp500_hist['Close'].iloc[0]
            sp500_last_price = sp500_hist['Close'].iloc[-1]
            sp500_change = ((sp500_last_price - sp500_first_price) / sp500_first_price) * 100
            
            # Step 8: Calculate RELATIVE IMPACT (core metric)
            relative_impact = company_change - sp500_change
            
            # Step 9: Calculate RECOVERY TIME
            recovery_days = None
            recovery_text = 'Did not recover to pre-breach price within 30 days'
            
            # Find breach date in the data
            breach_date_prices = company_hist[company_hist.index.date == breach_date]
            if not breach_date_prices.empty:
                breach_price = breach_date_prices['Close'].iloc[0]
                
                # Look for recovery after breach date
                post_breach_data = company_hist[company_hist.index.date >= breach_date]
                for idx, (date, row) in enumerate(post_breach_data.iterrows()):
                    if row['Close'] >= breach_price:
                        recovery_days = idx
                        recovery_text = f'Recovered to pre-breach price in {recovery_days} trading days'
                        break
            
            # Step 10: Build correlation result dict
            correlation_result = {
                'company': company_name,
                'ticker': ticker,
                'breach_date': breach_date_str,
                'breach_type': breach.get('type'),
                'records_affected': breach.get('records_affected'),
                'sector': breach.get('sector'),
                'attack_vector': breach.get('attack_vector'),
                'severity': breach.get('severity'),
                'company_pct_change': round(company_change, 2),
                'market_pct_change': round(sp500_change, 2),
                'relative_impact': round(relative_impact, 2),
                'recovery_days': recovery_days,
                'recovery_text': recovery_text,
                'analysis_period': f'{start_date} to {end_date}'
            }
            
            # Step 11-12: Import and call Groq
            try:
                from ai_engine.groq_analysis import analyze_breach_impact
                analysis_text = analyze_breach_impact(correlation_result)
            except ImportError:
                logger.warning('Groq analysis module not available')
                analysis_text = self._fallback_analysis(correlation_result)
            except Exception as e:
                logger.error(f'Groq analysis failed: {e}')
                analysis_text = f'AI analysis unavailable: {str(e)}'
            
            # Step 13: Return complete result
            return {
                'found': True,
                'result': correlation_result,
                'analysis': analysis_text
            }
        
        except Exception as e:
            logger.error(f'Unexpected error in analyze_breach_with_ai: {e}')
            return None
    
    def _fallback_analysis(self, correlation_result: Dict[str, Any]) -> str:
        """
        Fallback analysis when Groq is unavailable.
        
        Args:
            correlation_result: Dict with correlation metrics
        
        Returns:
            Analysis text
        """
        company = correlation_result['company']
        relative = correlation_result['relative_impact']
        recovery = correlation_result['recovery_text']
        severity = correlation_result['severity']
        
        if abs(relative) < 2:
            correlation = "minimal correlation"
        elif abs(relative) < 5:
            correlation = "moderate correlation"
        elif abs(relative) < 10:
            correlation = "strong correlation"
        else:
            correlation = "very strong correlation"
        
        analysis = (
            f"{company}'s stock appears to show {correlation} with the {severity.lower()} severity "
            f"breach disclosure. The stock declined {abs(relative):.1f}% more than the broader market during "
            f"the 60-day analysis window. {recovery}. "
            f"Note: Market correlation does not imply causation; multiple factors influence stock price movements."
        )
        
        return analysis
    
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
        cost_per_record = 150  # Conservative estimate
        breach_remediation_cost = records * cost_per_record
        
        incident_response = {'Critical': 5_000_000, 'High': 2_000_000, 'Medium': 500_000}.get(severity, 1_000_000)
        
        regulatory_multiplier = {'Financial Services': 0.04, 'Healthcare & Pharma': 0.03, 'Technology & Software': 0.02}.get(sector, 0.015)
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
        breaches_with_tickers = [b for b in self.breach_service.breaches if b.get('ticker')]
        
        return {
            'breaches_with_market_data': len(breaches_with_tickers),
            'total_breaches': len(self.breach_service.breaches),
            'note': 'Detailed correlation analysis requires extended historical data'
        }
