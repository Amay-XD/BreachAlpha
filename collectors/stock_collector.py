import yfinance as yf
from datetime import datetime, timedelta

def get_price_window(ticker, center_date_str, days=30):
    try:
        center = datetime.strptime(center_date_str, "%Y-%m-%d")
        start = center - timedelta(days=days)
        end = center + timedelta(days=days)

        data = yf.download(ticker, start=start, end=end, progress=False)

        if data.empty:
            return {"error": f"No data found for ticker: {ticker}"}

        return data

    except Exception as e:
        return {"error": str(e)}
      
