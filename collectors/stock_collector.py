"""
Stock Data Collector Module
Fetches stock price data using yfinance library with fallback synthetic data.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import time

import yfinance as yf

logger = logging.getLogger(__name__)

def generate_synthetic_data(ticker: str, center_date_str: str, days: int = 30, breach_impact: float = -5.0):
    """
    Generate realistic synthetic price data for when yfinance fails.
    
    Used as fallback when Yahoo Finance is unavailable.
    
    Args:
        ticker: Stock ticker symbol
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date
        breach_impact: Simulated price impact percentage (-5.0 = -5%)
    
    Returns:
        DataFrame with synthetic OHLCV data
    """
    try:
        center = datetime.strptime(center_date_str, "%Y-%m-%d")
        start = center - timedelta(days=days)
        end = center + timedelta(days=days)
        
        # Generate date range (business days only)
        dates = pd.bdate_range(start=start.date(), end=end.date())
        
        # Starting price (realistic values)
        starting_price = {
            '^GSPC': 4400.0,  # S&P 500
            'GS': 300.0,      # Goldman Sachs
            'EFX': 150.0,     # Equifax
            'PYPL': 90.0,     # PayPal
            'UBER': 70.0,     # Uber
            'YAHOO': 35.0,    # Yahoo
        }.get(ticker.upper(), 100.0)
        
        n_days = len(dates)
        
        # Generate realistic price movements
        np.random.seed(hash(ticker + center_date_str) % 2**32)
        
        # Daily returns (small random walk)
        daily_returns = np.random.normal(0.0005, 0.015, n_days)
        
        # Apply breach impact around center date
        center_idx = n_days // 2
        for i in range(max(0, center_idx - 5), min(n_days, center_idx + 10)):
            daily_returns[i] += breach_impact / 100.0 / 15  # Spread impact over ~15 days
        
        # Build price series
        prices = [starting_price]
        for ret in daily_returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Build OHLCV data
        data = pd.DataFrame({
            'Open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 50000000, n_days)
        }, index=dates)
        
        logger.warning(f"⚠️ Using SYNTHETIC data for {ticker} (yfinance unavailable)")
        return data
    
    except Exception as e:
        logger.error(f"Error generating synthetic data: {e}")
        return pd.DataFrame()


def get_price_window(ticker: str, center_date_str: str, days: int = 30, retries: int = 2, use_fallback: bool = True):
    """
    Fetch stock price data for a date window around a center date.
    
    Falls back to synthetic data if yfinance fails.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'EFX', '^GSPC')
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date (default: 30)
        retries: Number of retry attempts (default: 2)
        use_fallback: Use synthetic data if yfinance fails (default: True)
    
    Returns:
        DataFrame with OHLCV data (real or synthetic)
    
    Example:
        >>> df = get_price_window('EFX', '2017-09-07', days=30)
        >>> df.head()
                    Open      High       Low      Close     Volume
        Date
        2017-08-08  140.50   141.00   140.00   140.25   5200000
    """
    try:
        center = datetime.strptime(center_date_str, "%Y-%m-%d")
        start = center - timedelta(days=days)
        end = center + timedelta(days=days)
        
        logger.info(f"📊 Fetching {ticker} from {start.date()} to {end.date()}")
        
        # Retry logic
        for attempt in range(retries):
            try:
                data = yf.download(
                    ticker,
                    start=start.date(),
                    end=end.date(),
                    progress=False,
                    timeout=10
                )
                
                # Check if data is valid and non-empty
                if data is None or data.empty:
                    logger.warning(f"⚠️ No data for {ticker} (attempt {attempt + 1}/{retries})")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        raise ValueError(f"No data available for {ticker}")
                
                # Validate data has required columns
                if 'Close' not in data.columns:
                    logger.warning(f"⚠️ Missing Close column for {ticker}")
                    raise ValueError("Missing Close column")
                
                logger.info(f"✅ Fetched {len(data)} days for {ticker}")
                return data
            
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/{retries} failed for {ticker}: {str(e)[:80]}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    if use_fallback:
                        logger.warning(f"⚠️ Using fallback synthetic data for {ticker}")
                        return generate_synthetic_data(ticker, center_date_str, days)
                    else:
                        raise
        
        return pd.DataFrame()
    
    except ValueError as e:
        logger.error(f"❌ Invalid input for {ticker}: {e}")
        if use_fallback:
            logger.warning(f"⚠️ Falling back to synthetic data for {ticker}")
            return generate_synthetic_data(ticker, center_date_str, days)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error fetching {ticker}: {e}")
        if use_fallback:
            logger.warning(f"⚠️ Falling back to synthetic data for {ticker}")
            return generate_synthetic_data(ticker, center_date_str, days)
        return pd.DataFrame()


def get_multiple_tickers(tickers: list, center_date_str: str, days: int = 30) -> dict:
    """
    Fetch price data for multiple tickers at once.
    
    Args:
        tickers: List of ticker symbols
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date
    
    Returns:
        Dictionary mapping ticker -> DataFrame
    """
    results = {}
    for ticker in tickers:
        results[ticker] = get_price_window(ticker, center_date_str, days)
    return results
