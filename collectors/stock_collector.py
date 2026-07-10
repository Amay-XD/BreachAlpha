"""
Stock Data Collector Module
Fetches stock price data using yfinance library.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)

def get_price_window(ticker: str, center_date_str: str, days: int = 30):
    """
    Fetch stock price data for a date window around a center date.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'EFX', '^GSPC')
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date (default: 30)
    
    Returns:
        DataFrame with OHLCV data or empty DataFrame on error
    
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
        
        logger.info(f"Fetching {ticker} from {start.date()} to {end.date()}")
        
        # Download data from Yahoo Finance
        data = yf.download(
            ticker,
            start=start.date(),
            end=end.date(),
            progress=False
        )
        
        if data.empty:
            logger.warning(f"No data found for {ticker}")
            return data
        
        logger.info(f"✅ Fetched {len(data)} trading days for {ticker}")
        return data
    
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return yf.download('', start='2000-01-01', end='2000-01-02')  # Return empty DataFrame
