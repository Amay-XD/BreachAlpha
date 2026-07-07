#!/usr/bin/env python3
"""
Ticker verification helper for BreachAlpha breaches.json.
Provides methods to verify company tickers and research alternatives.

Usage:
    python3 scripts/verify_tickers.py --company "Target"
    python3 scripts/verify_tickers.py --batch data/companies_to_verify.csv
"""

import json
import sys
import csv
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import urllib.parse

class TickerVerifier:
    """Helper for researching and verifying company tickers."""
    
    # Manual mappings for reference (build as you research)
    KNOWN_TICKERS = {
        "Target": "NYSE:TGT",
        "Equifax": "NYSE:EFX",
        "Home Depot": "NYSE:HD",
        "Marriott International": "NASDAQ:MAR",
        "Yahoo": "NASDAQ:YAHOOA (delisted 2016, acquired by Verizon)",
        "JPMorgan Chase": "NYSE:JPM",
        "Bank of America": "NYSE:BAC",
        "Citigroup": "NYSE:C",
        "Wells Fargo": "NYSE:WFC",
        "Facebook": "NASDAQ:META",
        "Amazon": "NASDAQ:AMZN",
        "Apple": "NASDAQ:AAPL",
        "Microsoft": "NASDAQ:MSFT",
        "Google": "NASDAQ:GOOGL",
        "Twitter": "NYSE:TWTR (delisted 2023, privatized by Elon Musk)",
        "Zoom": "NASDAQ:ZM",
        "Uber": "NYSE:UBER",
        "Airbnb": "NASDAQ:ABNB",
        "PayPal": "NASDAQ:PYPL",
        "Square": "NYSE:SQ",
        "Stripe": "Private",
        "Shopify": "NYSE:SHOP",
        "Slack": "NYSE:WORK (rebranded to Salesforce)",
        "Twilio": "NYSE:TWLO",
        "Okta": "NASDAQ:OKTA",
        "CrowdStrike": "NASDAQ:CRWD",
        "Palo Alto Networks": "NASDAQ:PANW",
        "Fortinet": "NASDAQ:FTNT",
        "IBM": "NYSE:IBM",
        "Intel": "NASDAQ:INTC",
        "Cisco": "NASDAQ:CSCO",
        "Dell": "NYSE:DELL",
        "HP": "NYSE:HPE",
        "Canon": "NYSE:CAJ",
        "Xerox": "NYSE:XRX",
        "3M": "NYSE:MMM",
        "Johnson & Johnson": "NYSE:JNJ",
        "Pfizer": "NYSE:PFE",
        "Merck": "NYSE:MRK",
        "AbbVie": "NYSE:ABBV",
        "Bristol-Myers Squibb": "NYSE:BMY",
        "UnitedHealth": "NYSE:UNH",
        "CVS Health": "NYSE:CVS",
        "Walgreens": "NASDAQ:WBA",
        "Anthem": "NYSE:ANTM",
        "United Airlines": "NASDAQ:UAL",
        "American Airlines": "NASDAQ:AAL",
        "Delta Air Lines": "NYSE:DAL",
        "Southwest Airlines": "NYSE:LUV",
        "Marriott": "NASDAQ:MAR",
        "Hilton": "NYSE:HLT",
        "Wyndham": "NYSE:WH",
        "Booking.com": "NASDAQ:BKNG",
        "Expedia": "NASDAQ:EXPE",
        "TripAdvisor": "NASDAQ:TRIP",
        "Uber Eats": "Part of Uber (NYSE:UBER)",
        "DoorDash": "NYSE:DASH",
        "Lyft": "NASDAQ:LYFT",
        "Tesla": "NASDAQ:TSLA",
        "GM": "NYSE:GM",
        "Ford": "NYSE:F",
        "Toyota": "NYSE:TM",
        "Honda": "NYSE:HMC",
        "BMW": "OTC (German company, not US listed)",
        "Volkswagen": "OTC (German company, not US listed)",
        "Nissan": "OTC (Japanese company, not US listed)",
        "Walmart": "NYSE:WMT",
        "Costco": "NASDAQ:COST",
        "Best Buy": "NYSE:BBY",
        "Gap": "NYSE:GPS",
        "H&M": "OTC (Swedish company, not US listed)",
        "Nike": "NYSE:NKE",
        "Adidas": "OTC (German company, not US listed)",
        "Starbucks": "NASDAQ:SBUX",
        "McDonald's": "NYSE:MCD",
        "Coca-Cola": "NYSE:KO",
        "PepsiCo": "NASDAQ:PEP",
        "Netflix": "NASDAQ:NFLX",
        "Disney": "NYSE:DIS",
        "Warner Bros": "NASDAQ:WBD",
        "Paramount": "NASDAQ:PARA",
        "Comcast": "NASDAQ:CMCSA",
        "Charter Communications": "NASDAQ:CHTR",
        "AT&T": "NYSE:T",
        "Verizon": "NYSE:VZ",
        "Sprint": "Delisted (merged with T-Mobile in 2020)",
        "T-Mobile": "NASDAQ:TMUS",
        "Dish Network": "NASDAQ:DISH",
        "Sinclair Broadcast": "NASDAQ:SBGI",
        "Meta": "NASDAQ:META",
        "Alphabet": "NASDAQ:GOOGL",
        "Baidu": "NASDAQ:BIDU",
        "Alibaba": "NYSE:BABA",
        "Tencent": "OTC (Chinese company, not US listed)",
        "ByteDance": "Private",
        "Duolingo": "NASDAQ:DUOL",
    }
    
    def __init__(self):
        """Initialize verifier."""
        self.research_notes = {}
    
    @staticmethod
    def _yahoo_finance_url(company: str) -> str:
        """Generate Yahoo Finance search URL."""
        encoded = urllib.parse.quote(company)
        return f"https://finance.yahoo.com/quote/{encoded}"
    
    @staticmethod
    def _sec_edgar_url(company: str) -> str:
        """Generate SEC EDGAR search URL."""
        encoded = urllib.parse.quote(company)
        return f"https://www.sec.gov/cgi-bin/browse-edgar?company={encoded}"
    
    def lookup_ticker(self, company: str) -> Dict[str, str]:
        """Look up ticker and provide verification resources."""
        
        result = {
            "company": company,
            "ticker": None,
            "source": None,
            "status": "unknown",
            "verification_urls": {},
            "notes": ""
        }
        
        # Check known tickers
        if company in self.KNOWN_TICKERS:
            result["ticker"] = self.KNOWN_TICKERS[company]
            result["source"] = "known_mapping"
            result["verification_urls"] = {
                "yahoo_finance": self._yahoo_finance_url(company),
                "sec_edgar": self._sec_edgar_url(company)
            }
            
            # Parse status
            if "delisted" in result["ticker"].lower():
                result["status"] = "delisted"
            elif "private" in result["ticker"].lower():
                result["status"] = "private"
            elif "merged" in result["ticker"].lower():
                result["status"] = "merged"
            elif "(" in result["ticker"]:
                result["status"] = "acquired"
            else:
                result["status"] = "active"
            
            return result
        
        # Return URLs for manual research
        result["ticker"] = "TBD - Manual research required"
        result["source"] = "requires_research"
        result["status"] = "unknown"
        result["verification_urls"] = {
            "yahoo_finance": self._yahoo_finance_url(company),
            "sec_edgar": self._sec_edgar_url(company),
            "wikipedia_search": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(company)}"
        }
        result["notes"] = (
            f"Ticker not in known mappings. Use provided URLs to research. "
            f"Check if company is: (1) US-traded on NYSE/NASDAQ, "
            f"(2) Subsidiary of public parent, (3) Private/delisted/international"
        )
        
        return result
    
    def batch_lookup(self, companies: List[str]) -> List[Dict[str, str]]:
        """Look up multiple companies."""
        return [self.lookup_ticker(company) for company in companies]
    
    def generate_research_template(self, company: str) -> Dict[str, str]:
        """Generate a research template for a company."""
        lookup = self.lookup_ticker(company)
        
        return {
            "company": company,
            "ticker": lookup["ticker"],
            "status": lookup["status"],
            "source_1": "",
            "source_1_url": "",
            "source_2": "",
            "source_2_url": "",
            "verification_urls": json.dumps(lookup["verification_urls"], indent=2),
            "notes": lookup["notes"],
            "research_notes": "YOUR NOTES HERE - What did you find?"
        }
    
    @staticmethod
    def print_lookup(lookup: Dict[str, str], verbose: bool = True) -> None:
        """Print formatted lookup result."""
        print(f"\n{'='*60}")
        print(f"Company: {lookup['company']}")
        print(f"Ticker: {lookup['ticker']}")
        print(f"Status: {lookup['status']}")
        
        if verbose and lookup.get("verification_urls"):
            print(f"\nVerification Resources:")
            for url_type, url in lookup["verification_urls"].items():
                print(f"  • {url_type}: {url}")
        
        if lookup.get("notes"):
            print(f"\nNotes: {lookup['notes']}")
        print(f"{'='*60}\n")
    
    @staticmethod
    def print_batch(lookups: List[Dict[str, str]]) -> None:
        """Print formatted batch results."""
        print(f"\n{'='*80}")
        print(f"{'Company':<30} {'Ticker':<25} {'Status':<15}")
        print(f"{'='*80}")
        
        for lookup in lookups:
            ticker = lookup["ticker"][:24] if lookup["ticker"] else "N/A"
            print(f"{lookup['company']:<30} {ticker:<25} {lookup['status']:<15}")
        
        print(f"{'='*80}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify and research company tickers for BreachAlpha dataset"
    )
    parser.add_argument(
        "--company",
        type=str,
        help="Look up a single company ticker"
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="Look up multiple companies from CSV file (one company per line)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verification URLs and detailed info"
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Generate research template (use with --company)"
    )
    
    args = parser.parse_args()
    verifier = TickerVerifier()
    
    if args.company:
        if args.template:
            template = verifier.generate_research_template(args.company)
            print("\nResearch Template:")
            print(json.dumps(template, indent=2))
        else:
            lookup = verifier.lookup_ticker(args.company)
            verifier.print_lookup(lookup, verbose=args.verbose)
    
    elif args.batch:
        try:
            with open(args.batch, 'r') as f:
                companies = [line.strip() for line in f if line.strip()]
            
            lookups = verifier.batch_lookup(companies)
            verifier.print_batch(lookups)
            
            # Save results
            output_file = args.batch.replace('.txt', '_results.json')
            with open(output_file, 'w') as f:
                json.dump(lookups, f, indent=2)
            print(f"Results saved to: {output_file}")
        
        except FileNotFoundError:
            print(f"Error: File not found: {args.batch}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
