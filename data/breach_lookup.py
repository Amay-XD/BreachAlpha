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
        if query == b["ticker"].lower() or query in b["company"].lower():
            return b
    return None
