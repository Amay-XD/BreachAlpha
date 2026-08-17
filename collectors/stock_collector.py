"""
Stock Data Collector Module
Fetches stock price data using yfinance library with retry logic.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import time

import yfinance as yf

logger = logging.getLogger(__name__)

def get_price_window(ticker: str, center_date_str: str, days: int = 30, retries: int = 3):
    """
    Fetch stock price data for a date window around a center date.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'EFX', '^GSPC')
        center_date_str: Center date as string (YYYY-MM-DD)
        days: Days before and after center date (default: 30)
        retries: Number of retry attempts (default: 3)
    
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
        
        logger.info(f"📊 Fetching {ticker} from {start.date()} to {end.date()}")
        
        # Retry logic with exponential backoff
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
                    logger.warning(f"⚠️ No data returned for {ticker} (attempt {attempt + 1}/{retries})")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.info(f"⏳ Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Failed to fetch {ticker} after {retries} attempts")
                        return pd.DataFrame()
                
                # Validate data has required columns
                required_cols = ['Close']
                if not all(col in data.columns for col in required_cols):
                    logger.warning(f"⚠️ Missing required columns in {ticker} data")
                    return pd.DataFrame()
                
                logger.info(f"✅ Successfully fetched {len(data)} trading days for {ticker}")
                return data
            
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1}/{retries} failed for {ticker}: {str(e)[:100]}")
                if attempt < retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Error fetching {ticker} after {retries} attempts: {e}")
                    return pd.DataFrame()
        
        return pd.DataFrame()
    
    except ValueError as e:
        logger.error(f"❌ Invalid date format for {ticker}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching {ticker}: {e}")
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
