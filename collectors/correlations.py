"""
Correlations Module
Calculates financial metrics and correlation analysis.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def calculate_pct_change(df) -> Optional[float]:
    """
    Calculate percentage price change from first to last trading day.
    
    Args:
        df: DataFrame with 'Close' column (from yfinance)
    
    Returns:
        Float percentage change, rounded to 2 decimals, or None if insufficient data
    
    Example:
        >>> df = yf.download('EFX', start='2017-08-08', end='2017-10-07')
        >>> pct = calculate_pct_change(df)
        >>> print(pct)
        -10.71
    """
    try:
        if df.empty or len(df) < 2:
            logger.warning("Insufficient data for percentage change calculation")
            return None
        
        first_close = df["Close"].iloc[0]
        last_close = df["Close"].iloc[-1]
        
        pct_change = ((last_close - first_close) / first_close) * 100
        
        logger.info(f"Price change: {pct_change:.2f}% (${first_close:.2f} → ${last_close:.2f})")
        
        return round(pct_change, 2)
    
    except Exception as e:
        logger.error(f"Error calculating percentage change: {e}")
        return None

def calculate_relative_impact(company_change: float, market_change: float) -> float:
    """
    Calculate relative underperformance vs S&P 500.
    
    This is the KEY METRIC: How much worse did the stock perform compared to
    the overall market during the same time period?
    
    Args:
        company_change: Company stock % change
        market_change: S&P 500 % change
    
    Returns:
        Percentage points of underperformance (negative = outperformance)
    
    Example:
        >>> company_change = -10.7
        >>> market_change = -0.5
        >>> impact = calculate_relative_impact(company_change, market_change)
        >>> print(impact)
        -10.2  # Stock underperformed by 10.2 percentage points
    
    Interpretation:
        -10.2 pp = stock fell 10.2% more than the market
        +5.0 pp = stock rose 5.0% more than the market
    """
    try:
        if company_change is None or market_change is None:
            logger.warning("Cannot calculate relative impact with None values")
            return 0.0
        
        relative = company_change - market_change
        logger.info(f"Relative impact: {relative:.2f}pp ({company_change:.2f}% - {market_change:.2f}%)")
        
        return round(relative, 2)
    
    except Exception as e:
        logger.error(f"Error calculating relative impact: {e}")
        return 0.0

def calculate_recovery_days(df, pre_breach_price: float) -> Optional[int]:
    """
    Calculate how many trading days until stock recovered to pre-breach price.
    
    Args:
        df: DataFrame with 'Close' column (post-breach data)
        pre_breach_price: Stock price before the breach
    
    Returns:
        Number of trading days to recovery, or None if not recovered in window
    
    Example:
        >>> # Stock was $140 before breach
        >>> # We check if it recovered to $140+ in the 30 days after
        >>> recovery = calculate_recovery_days(post_breach_df, 140.0)
        >>> print(recovery)
        45  # Took 45 trading days to recover
    """
    try:
        if df.empty:
            logger.warning("Cannot calculate recovery with empty data")
            return None
        
        # Skip the first day (breach date itself)
        prices = df["Close"].iloc[1:]
        
        for i, price in enumerate(prices):
            if price >= pre_breach_price:
                logger.info(f"Recovery achieved after {i+1} trading days")
                return i + 1  # +1 because we skipped first day
        
        logger.info(f"No recovery to ${pre_breach_price:.2f} within analysis window")
        return None
    
    except Exception as e:
        logger.error(f"Error calculating recovery days: {e}")
        return None

def interpret_correlation_strength(relative_impact: float) -> str:
    """
    Interpret the strength of correlation between breach and stock performance.
    
    Args:
        relative_impact: Percentage points of underperformance
    
    Returns:
        Text description of correlation strength
    
    Example:
        >>> strength = interpret_correlation_strength(-10.2)
        >>> print(strength)
        "strong correlation"
    """
    abs_impact = abs(relative_impact)
    
    if abs_impact < 1:
        return "minimal correlation"
    elif abs_impact < 3:
        return "weak correlation"
    elif abs_impact < 5:
        return "moderate correlation"
    elif abs_impact < 10:
        return "strong correlation"
    else:
        return "very strong correlation"
