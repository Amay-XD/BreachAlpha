#!/usr/bin/env python3
"""
Validation script for BreachAlpha breaches.json dataset.
Checks data quality, completeness, and consistency.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

class BreachValidator:
    """Validates breach data against quality standards."""
    
    # Valid enums
    VALID_TYPES = {
        "Data Exfiltration", "Ransomware", "Supply Chain Attack",
        "Zero-Day Exploit", "Insider Threat", "Social Engineering",
        "Cloud Misconfiguration", "POS Malware", "API Abuse",
        "State-Sponsored", "Brute Force / Weak Credentials",
        "Vulnerability Exploitation", "Unpatched Vulnerability Exploitation",
        "Malware", "Physical Theft", "Credential Stuffing"
    }
    
    VALID_SECTORS = {
        "Finance & Banking", "Healthcare & Pharma", "Retail & E-commerce",
        "Technology & Software", "Government & Defense", "Energy & Utilities",
        "Telecommunications", "Manufacturing & Industrial", "Hospitality & Travel",
        "Media & Entertainment", "Education", "Insurance", "Transportation",
        "Real Estate", "Agriculture", "Non-Profit", "Logistics"
    }
    
    VALID_SEVERITIES = {"Critical", "High", "Medium"}
    
    def __init__(self, filepath: str):
        """Initialize validator with filepath."""
        self.filepath = Path(filepath)
        self.data = None
        self.errors = []
        self.warnings = []
        
    def load_data(self) -> bool:
        """Load and parse JSON file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except FileNotFoundError:
            self.errors.append(f"File not found: {self.filepath}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON parsing error: {e}")
            return False
    
    def validate_structure(self) -> bool:
        """Validate top-level structure."""
        valid = True
        
        if not isinstance(self.data, dict):
            self.errors.append("Root must be a dictionary")
            return False
        
        if "metadata" not in self.data:
            self.errors.append("Missing 'metadata' key")
            valid = False
        
        if "breaches" not in self.data:
            self.errors.append("Missing 'breaches' key")
            return False
        
        if not isinstance(self.data["breaches"], list):
            self.errors.append("'breaches' must be a list")
            return False
        
        return valid
    
    def validate_metadata(self) -> bool:
        """Validate metadata section."""
        if "metadata" not in self.data:
            return True
        
        meta = self.data["metadata"]
        valid = True
        
        required_meta = ["total_breaches", "date_generated", "coverage_period"]
        for key in required_meta:
            if key not in meta:
                self.warnings.append(f"Missing metadata key: {key}")
        
        # Validate date format
        if "date_generated" in meta:
            try:
                datetime.fromisoformat(meta["date_generated"])
            except ValueError:
                self.errors.append(
                    f"Invalid date format in metadata: {meta['date_generated']} "
                    "(expected YYYY-MM-DD)"
                )
                valid = False
        
        return valid
    
    def validate_breach(self, breach: Dict[str, Any], index: int) -> Tuple[bool, List[str]]:
        """Validate individual breach record."""
        errors = []
        valid = True
        
        # Required fields
        required = ["company", "ticker", "breach_date", "type", "records_affected",
                   "sector", "attack_vector", "severity", "summary", "sources"]
        
        for field in required:
            if field not in breach:
                errors.append(f"Breach {index}: Missing required field '{field}'")
                valid = False
        
        if not valid:
            return False, errors
        
        # Validate company name
        if not isinstance(breach["company"], str) or len(breach["company"]) == 0:
            errors.append(f"Breach {index}: 'company' must be non-empty string")
            valid = False
        
        # Validate ticker format
        ticker = breach.get("ticker")
        if ticker is not None:
            if isinstance(ticker, str):
                if len(ticker) == 0:
                    errors.append(f"Breach {index}: 'ticker' cannot be empty string (use null)")
                    valid = False
                elif not (":" in ticker or ticker == "null"):
                    if not ticker.isupper() and ticker != "null":
                        self.warnings.append(
                            f"Breach {index}: Ticker format unusual: {ticker} "
                            "(expected NYSE:XXX or NASDAQ:YYY or null)"
                        )
            else:
                errors.append(f"Breach {index}: 'ticker' must be string or null")
                valid = False
        
        # Validate date format
        breach_date = breach.get("breach_date")
        if breach_date:
            try:
                date_obj = datetime.fromisoformat(breach_date)
                # Check if date is in valid range
                if date_obj.year < 2010 or date_obj.year > 2024:
                    errors.append(
                        f"Breach {index}: Date {breach_date} outside coverage period (2010-2024)"
                    )
                    valid = False
            except ValueError:
                errors.append(
                    f"Breach {index}: Invalid date format: {breach_date} "
                    "(expected YYYY-MM-DD)"
                )
                valid = False
        
        # Validate type
        breach_type = breach.get("type")
        if breach_type not in self.VALID_TYPES:
            self.warnings.append(
                f"Breach {index}: Type '{breach_type}' not in approved list. "
                f"Approved: {', '.join(sorted(self.VALID_TYPES))}"
            )
        
        # Validate sector
        sector = breach.get("sector")
        if sector not in self.VALID_SECTORS:
            self.warnings.append(
                f"Breach {index}: Sector '{sector}' not in approved list. "
                f"Approved: {', '.join(sorted(self.VALID_SECTORS))}"
            )
        
        # Validate severity
        severity = breach.get("severity")
        if severity not in self.VALID_SEVERITIES:
            errors.append(
                f"Breach {index}: Invalid severity '{severity}'. "
                f"Must be one of: {', '.join(self.VALID_SEVERITIES)}"
            )
            valid = False
        
        # Validate records affected (should contain number or "Unknown")
        records = breach.get("records_affected")
        if records and records != "Unknown":
            if not any(unit in records for unit in ["M", "K", "B", "million", "thousand"]):
                self.warnings.append(
                    f"Breach {index}: records_affected format unclear: {records} "
                    "(expected format: '147M', '500K', etc.)"
                )
        
        # Validate summary length
        summary = breach.get("summary", "")
        if len(summary) < 50:
            self.warnings.append(
                f"Breach {index}: Summary may be too short ({len(summary)} chars): {summary[:50]}..."
            )
        elif len(summary) > 500:
            self.warnings.append(
                f"Breach {index}: Summary may be too long ({len(summary)} chars)"
            )
        
        # Validate summary doesn't contain speculation
        speculation_words = ["allegedly", "possibly", "might", "could", "perhaps", "rumor"]
        if any(word in summary.lower() for word in speculation_words):
            errors.append(
                f"Breach {index}: Summary contains speculative language. "
                "Only use confirmed facts from sources."
            )
            valid = False
        
        # Validate sources
        sources = breach.get("sources", [])
        if not isinstance(sources, list):
            errors.append(f"Breach {index}: 'sources' must be a list")
            valid = False
        elif len(sources) < 2:
            self.warnings.append(
                f"Breach {index}: Only {len(sources)} source(s) cited. "
                "Recommend 2+ sources for verification."
            )
        
        return valid, errors
    
    def validate_all(self) -> bool:
        """Run all validations."""
        if not self.load_data():
            return False
        
        if not self.validate_structure():
            return False
        
        if not self.validate_metadata():
            pass  # Continue even if metadata has issues
        
        # Validate each breach
        breaches = self.data.get("breaches", [])
        for idx, breach in enumerate(breaches):
            valid, errors = self.validate_breach(breach, idx)
            self.errors.extend(errors)
        
        # Check for duplicates
        companies = [b.get("company") for b in breaches]
        duplicates = [c for c in companies if companies.count(c) > 1]
        if duplicates:
            for dup in set(duplicates):
                self.warnings.append(f"Duplicate company found: {dup}")
        
        return len(self.errors) == 0
    
    def report(self, verbose: bool = True) -> None:
        """Print validation report."""
        print("\n" + "="*70)
        print("BREACHEALPHA VALIDATION REPORT")
        print("="*70 + "\n")
        
        if self.data:
            breaches_count = len(self.data.get("breaches", []))
            print(f"✓ File loaded successfully")
            print(f"✓ Total breaches: {breaches_count}\n")
        
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
            print()
        else:
            print("✓ No critical errors found\n")
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        else:
            print("✓ No warnings\n")
        
        if not self.errors:
            print("✅ VALIDATION PASSED - Data quality check complete")
        else:
            print("❌ VALIDATION FAILED - Please fix errors above")
        
        print("="*70 + "\n")
    
    def get_stats(self) -> Dict[str, Any]:
        """Return validation statistics."""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "passed": len(self.errors) == 0,
            "breaches_count": len(self.data.get("breaches", [])) if self.data else 0
        }


def main():
    """Main entry point."""
    filepath = "data/breaches.json"
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    validator = BreachValidator(filepath)
    passed = validator.validate_all()
    validator.report(verbose=True)
    
    stats = validator.get_stats()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
