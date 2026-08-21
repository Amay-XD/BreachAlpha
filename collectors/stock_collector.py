"""
Stock Data Collector Module
Fetches REAL stock price data using Alpha Vantage API (primary)
Falls back to synthetic data ONLY if Alpha Vantage fails.

NO yfinance - clean and simple!
"""

import logging
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_price_alpha_vantage(ticker: str, center_date_str: str, days: int = 30):
    """
    Fetch REAL stock data from Alpha Vantage API.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'EFX', 'GSPC')
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date
    
    Returns:
        DataFrame with real OHLCV data or None if failed
    """
    if not ALPHA_VANTAGE_API_KEY:
        logger.error("❌ ALPHA_VANTAGE_API_KEY not set in .env file!")
        return None
    
    try:
        center = datetime.strptime(center_date_str, "%Y-%m-%d")
        start = center - timedelta(days=days)
        end = center + timedelta(days=days)
        
        logger.info(f"📊 Fetching REAL data from Alpha Vantage: {ticker}")
        
        # Alpha Vantage API call
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'apikey': ALPHA_VANTAGE_API_KEY,
            'outputsize': 'compact'  # Free tier only gets last 100 days 🥀 
        }
        
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        # Check for errors
        if 'Error Message' in data:
            logger.error(f"❌ Alpha Vantage error: {data['Error Message']}")
            return None
        
        if 'Note' in data:
            logger.warning(f"⚠️ Alpha Vantage rate limit reached (5 calls/min)")
            return None
        
        if 'Time Series (Daily)' not in data:
            logger.warning(f"⚠️ No time series data for {ticker}")
            return None
        
        # Parse the data
        time_series = data['Time Series (Daily)']
        dates = []
        closes = []
        opens = []
        highs = []
        lows = []
        volumes = []
        
        for date_str in sorted(time_series.keys()):
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Only include dates in our window
            if date_obj < start or date_obj > end:
                continue
            
            day_data = time_series[date_str]
            dates.append(date_obj)
            opens.append(float(day_data.get('1. open', 0)))
            highs.append(float(day_data.get('2. high', 0)))
            lows.append(float(day_data.get('3. low', 0)))
            closes.append(float(day_data.get('4. close', 0)))
            volumes.append(int(day_data.get('5. volume', 0)))
        
        if not dates:
            logger.warning(f"⚠️ No data in date range for {ticker}")
            return None
        
        # Build DataFrame
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes
        }, index=pd.DatetimeIndex(dates, name='Date'))
        
        logger.info(f"✅ Got {len(df)} REAL trading days for {ticker} from Alpha Vantage")
        return df
    
    except requests.exceptions.Timeout:
        logger.warning(f"⚠️ Alpha Vantage timeout for {ticker}")
        return None
    except Exception as e:
        logger.error(f"❌ Alpha Vantage error: {e}")
        return None


def generate_synthetic_data(ticker: str, center_date_str: str, days: int = 30, breach_impact: float = -5.0):
    """
    Generate realistic synthetic price data (FALLBACK ONLY).
    
    Used ONLY when Alpha Vantage fails.
    """
    try:
        center = datetime.strptime(center_date_str, "%Y-%m-%d")
        start = center - timedelta(days=days)
        end = center + timedelta(days=days)
        
        dates = pd.bdate_range(start=start.date(), end=end.date())
        
        starting_price = {
            'GSPC': 4400.0,
            'GS': 300.0,
            'EFX': 150.0,
            'PYPL': 90.0,
            'UBER': 70.0,
        }.get(ticker.upper(), 100.0)
        
        n_days = len(dates)
        np.random.seed(hash(ticker + center_date_str) % 2**32)
        
        daily_returns = np.random.normal(0.0005, 0.015, n_days)
        
        center_idx = n_days // 2
        for i in range(max(0, center_idx - 5), min(n_days, center_idx + 10)):
            daily_returns[i] += breach_impact / 100.0 / 15
        
        prices = [starting_price]
        for ret in daily_returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 50000000, n_days)
        }, index=dates)
        
        logger.warning(f"⚠️ Using SYNTHETIC fallback for {ticker} (Alpha Vantage unavailable)")
        return data
    
    except Exception as e:
        logger.error(f"❌ Synthetic data failed: {e}")
        return pd.DataFrame()


def get_price_window(ticker: str, center_date_str: str, days: int = 30):
    """
    Fetch stock price data with fallback:
    1. Try Alpha Vantage (REAL data) ✅
    2. Use synthetic data (FALLBACK) ⚠️
    
    Args:
        ticker: Stock ticker symbol (e.g., 'EFX', 'GSPC')
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date
    
    Returns:
        DataFrame with OHLCV data (real or synthetic)
    """
    # Normalize ticker (handle GSPC or ^GSPC)
    ticker_normalized = ticker.replace('^', '')
    
    # Try Alpha Vantage (REAL DATA)
    logger.info(f"🔵 Attempting Alpha Vantage for {ticker}")
    df = get_price_alpha_vantage(ticker_normalized, center_date_str, days)
    
    if df is not None and not df.empty:
        return df
    
    # Fallback to synthetic
    logger.warning(f"🔴 Falling back to synthetic data for {ticker}")
    return generate_synthetic_data(ticker, center_date_str, days)


def get_multiple_tickers(tickers: list, center_date_str: str, days: int = 30) -> dict:
    """Fetch price data for multiple tickers."""
    results = {}
    for ticker in tickers:
        results[ticker] = get_price_window(ticker, center_date_str, days)
    return results
