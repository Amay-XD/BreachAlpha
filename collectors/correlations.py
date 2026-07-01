def pct_change(df):
    if df is None or hasattr(df, "get") and isinstance(df, dict):
        return None  # error dict from stock_collector
    if df.empty or len(df) < 2:
        return None
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    return round(((end_price - start_price) / start_price) * 100, 2)

def relative_impact(company_change, market_change):
    if company_change is None or market_change is None:
        return None
    return round(company_change - market_change, 2)

def recovery_days(df, pre_breach_price):
    if df is None or df.empty:
        return None
    for i, price in enumerate(df["Close"]):
        if price >= pre_breach_price:
            return i
    return None

def recovery_text(days):
    if days is None:
        return "Did not recover to pre-breach price within 30 days"
    return f"Recovered in {days} trading days"

def build_correlation_result(breach, company_df, market_df):
    company_change = pct_change(company_df)
    market_change = pct_change(market_df)
    rel_impact = relative_impact(company_change, market_change)

    pre_breach_price = None
    if company_df is not None and not company_df.empty:
        pre_breach_price = company_df["Close"].iloc[0]

    days = recovery_days(company_df, pre_breach_price) if pre_breach_price else None

    return {
        "company": breach["company"],
        "ticker": breach["ticker"],
        "breach_date": breach["breach_date"],
        "breach_type": breach["type"],
        "company_pct_change": company_change,
        "market_pct_change": market_change,
        "relative_impact": rel_impact,
        "recovery": recovery_text(days)
    }
