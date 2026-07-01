import json
import os

BREACHES_PATH = os.path.join(os.path.dirname(__file__), "breaches.json")

def load_breaches():
    with open(BREACHES_PATH) as f:
        return json.load(f)

def find_breach(query: str):
    query = query.strip().lower()
    if not query:
        return None
    for b in load_breaches():
        ticker = b["ticker"]
        ticker_match = ticker and query == ticker.lower()
        company_match = query in b["company"].lower()
        if ticker_match or company_match:
            return b
    return None

def list_breaches():
    breaches = load_breaches()
    return [
        {
            "company": b["company"],
            "ticker": b["ticker"],
            "sector": b["sector"],
            "severity": b["severity"],
            "records_affected": b["records_affected"]
        }
        for b in breaches
    ]
