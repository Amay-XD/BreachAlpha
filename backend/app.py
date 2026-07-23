"""
BreachAlpha Backend - Production-Ready Flask Application
Breach-to-Market Impact Engine + Executive Cyber Risk Intelligence Engine

A comprehensive AI-powered tool that correlates historical data breaches
with stock market movements to analyze financial impact, and produces
an executive-facing Intelligence Score so the frontend needs almost no
client-side calculation.
"""

import os
import math
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Tuple, List

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import helper modules
from collectors.stock_collector import get_price_window
from collectors.correlations import (
    calculate_pct_change,
    calculate_relative_impact,
    calculate_recovery_days
)
from data.breach_lookup import find_breach, load_breaches
from ai_engine.mistral_analysis import analyze_breach_impact, analyze_no_breach
from output.pdf import generate_breach_report_pdf


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DECORATORS
# ============================================================================

def handle_errors(f):
    """Decorator to handle errors gracefully."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as ve:
            logger.warning(f"Validation error in {f.__name__}: {ve}")
            return jsonify({"error": str(ve)}), 400
        except FileNotFoundError as fe:
            logger.error(f"File not found in {f.__name__}: {fe}")
            return jsonify({"error": "Data file not found"}), 500
        except Exception as e:
            logger.error(f"Unhandled error in {f.__name__}: {e}", exc_info=True)
            return jsonify({"error": f"Server error: {str(e)}"}), 500
    return decorated

def validate_query(f):
    """Decorator to validate user input query."""
    @wraps(f)
    def decorated(*args, **kwargs):
        body = request.get_json(silent=True) or {}
        query = (body.get("query") or "").strip()

        if not query:
            return jsonify({"error": "Missing 'query' field"}), 400
        if len(query) > 50:
            return jsonify({"error": "Query too long (max 50 characters)"}), 400
        if not query.replace(" ", "").replace("-", "").isalnum():
            return jsonify({"error": "Invalid characters in query"}), 400

        return f(*args, **kwargs)
    return decorated

# ============================================================================
# INTELLIGENCE SCORE ENGINE
# ============================================================================
#
# Produces a single 0-100 "Executive Cyber Risk Intelligence Score" plus a
# full factor breakdown, so the frontend can render gauges/badges/tables
# without doing any math itself.
#
# Score is a weighted composite of five factors:
#   1. Severity (breach dataset label)              weight 25%
#   2. Market impact (relative underperformance)     weight 30%  (only if available)
#   3. Recovery speed (trading days to recover)       weight 20%  (only if available)
#   4. Records affected (scale of exposure)           weight 15%
#   5. Sector risk (baseline sector sensitivity)       weight 10%
#
# When market-derived factors (2 and 3) are unavailable (e.g. static
# breach-only scoring for the leaderboard), their weight is redistributed
# proportionally across the remaining factors so the score still spans 0-100.

SEVERITY_SCORE_MAP = {
    "critical": 100,
    "high": 80,
    "medium": 55,
    "moderate": 55,
    "low": 30,
    "unknown": 45,
}

SECTOR_RISK_MAP = {
    "financial services": 90,
    "finance": 90,
    "banking": 90,
    "healthcare": 85,
    "technology": 75,
    "retail": 65,
    "e-commerce": 65,
    "telecommunications": 70,
    "government": 88,
    "energy": 80,
    "hospitality": 60,
    "education": 55,
    "insurance": 82,
    "unknown": 50,
}

RISK_TIER_THRESHOLDS = [
    (85, "Severe", "#b91c1c"),
    (70, "High", "#ea580c"),
    (50, "Elevated", "#ca8a04"),
    (30, "Moderate", "#16a34a"),
    (0, "Low", "#0891b2"),
]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _severity_component(breach: Dict[str, Any]) -> float:
    severity = str(breach.get("severity", "unknown")).strip().lower()
    return SEVERITY_SCORE_MAP.get(severity, SEVERITY_SCORE_MAP["unknown"])


def _sector_component(breach: Dict[str, Any]) -> float:
    sector = str(breach.get("sector", "unknown")).strip().lower()
    return SECTOR_RISK_MAP.get(sector, SECTOR_RISK_MAP["unknown"])


def _records_component(breach: Dict[str, Any]) -> float:
    """Log-scaled score: 1K records ~ low, 1B+ records ~ maxed out."""
    records = breach.get("records_affected") or 0
    try:
        records = float(records)
    except (TypeError, ValueError):
        records = 0.0
    if records <= 0:
        return 20.0  # unknown scale, assume moderate-low baseline
    # log10(1,000) = 3 -> ~20 ; log10(1,000,000,000) = 9 -> ~100
    scaled = (math.log10(records) - 3) / (9 - 3) * 80 + 20
    return _clamp(scaled)


def _market_impact_component(relative_impact: Optional[float]) -> Optional[float]:
    """relative_impact is a percentage point figure, typically negative
    (underperformance vs market). More negative = worse = higher risk score."""
    if relative_impact is None:
        return None
    # -30pp or worse -> 100 ; 0pp or better -> 10
    scaled = _clamp((-relative_impact) / 30 * 90 + 10)
    return scaled


def _recovery_component(recovery_days: Optional[int]) -> Optional[float]:
    """No recovery within window (None) is treated as worst case (100).
    0 days -> low risk, 30+ days -> high risk."""
    if recovery_days is None:
        return 95.0
    scaled = _clamp((recovery_days / 30) * 90 + 10)
    return scaled


def _risk_tier(score: float) -> Tuple[str, str]:
    for threshold, label, color in RISK_TIER_THRESHOLDS:
        if score >= threshold:
            return label, color
    return "Low", "#0891b2"


def _letter_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def calculate_intelligence_score(
    breach: Dict[str, Any],
    relative_impact: Optional[float] = None,
    recovery_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute the Executive Cyber Risk Intelligence Score.

    Args:
        breach: breach record dict (must contain severity, sector, records_affected)
        relative_impact: optional market underperformance in percentage points
        recovery_days: optional trading days to recovery (None = did not recover)

    Returns:
        Structured dict with overall score, grade, tier, and factor breakdown.
        Designed to be dropped directly into a JSON API response.
    """
    severity_val = _severity_component(breach)
    sector_val = _sector_component(breach)
    records_val = _records_component(breach)
    market_val = _market_impact_component(relative_impact)
    recovery_val = _recovery_component(recovery_days) if market_val is not None else None

    # Base weights
    weights = {
        "severity": 0.25,
        "market_impact": 0.30,
        "recovery_speed": 0.20,
        "records_affected": 0.15,
        "sector_risk": 0.10,
    }

    components = {
        "severity": severity_val,
        "market_impact": market_val,
        "recovery_speed": recovery_val,
        "records_affected": records_val,
        "sector_risk": sector_val,
    }

    # Redistribute weight of any missing (None) components proportionally
    available = {k: v for k, v in components.items() if v is not None}
    missing_weight = sum(w for k, w in weights.items() if components[k] is None)
    if missing_weight > 0 and available:
        redistribute_ratio = missing_weight / sum(weights[k] for k in available)
        effective_weights = {
            k: weights[k] * (1 + redistribute_ratio) for k in available
        }
    else:
        effective_weights = {k: weights[k] for k in available}

    overall = sum(available[k] * effective_weights[k] for k in available)
    overall = round(_clamp(overall), 1)

    tier_label, tier_color = _risk_tier(overall)
    grade = _letter_grade(overall)

    factors = []
    factor_meta = {
        "severity": "Breach Severity",
        "market_impact": "Market Impact",
        "recovery_speed": "Recovery Speed",
        "records_affected": "Records Exposed",
        "sector_risk": "Sector Risk Baseline",
    }
    for key, label in factor_meta.items():
        value = components[key]
        factors.append({
            "key": key,
            "label": label,
            "score": round(value, 1) if value is not None else None,
            "weight_pct": round(effective_weights.get(key, weights[key]) * 100, 1),
            "available": value is not None
        })

    return {
        "overall_score": overall,
        "grade": grade,
        "risk_tier": tier_label,
        "risk_color": tier_color,
        "factors": factors,
        "summary": (
            f"{breach.get('company', 'This company')} scores {overall}/100 "
            f"({grade}) — classified as {tier_label} risk."
        ),
        "methodology_version": "1.0"
    }


def calculate_score_for_query(query: str, breach: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience wrapper: attempts a live market-based score, falling back
    to a static breach-metadata-only score if price data is unavailable.
    Used by the standalone intelligence endpoints.
    """
    relative_impact = None
    recovery_days = None
    market_data_used = False

    try:
        ticker = breach.get("ticker")
        breach_date_str = breach.get("breach_date")
        if ticker and breach_date_str:
            company_df = get_price_window(ticker, breach_date_str, days=30)
            sp500_df = get_price_window("^GSPC", breach_date_str, days=30)
            if not company_df.empty and not sp500_df.empty and len(company_df) >= 2 and len(sp500_df) >= 2:
                company_change = calculate_pct_change(company_df)
                market_change = calculate_pct_change(sp500_df)
                relative_impact = calculate_relative_impact(company_change, market_change)
                pre_breach_price = company_df["Close"].iloc[0]
                recovery_days = calculate_recovery_days(company_df, pre_breach_price)
                market_data_used = True
    except Exception as e:
        logger.warning(f"Live market scoring unavailable for {query}: {e}")

    score = calculate_intelligence_score(breach, relative_impact, recovery_days)
    score["market_data_used"] = market_data_used
    return score

# ============================================================================
# FLASK APPLICATION FACTORY
# ============================================================================

def create_app(config_name: str = 'development') -> Flask:
    """
    Create and configure Flask application.

    Args:
        config_name: 'development' or 'production'

    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__)

    # Configuration
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request

    # Load environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['FLASK_ENV'] = config_name

    # CORS Configuration
    cors_origins = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:8000,http://localhost:3000,http://localhost:8080'
    ).split(',')
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins, "allow_headers": ["Content-Type"]}},
        supports_credentials=True
    )

    # Load breach dataset
    try:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        breaches_path = os.path.join(data_dir, 'breaches.json')
        app.breaches = load_breaches(breaches_path)
        logger.info(f"✅ Loaded {len(app.breaches)} breaches from dataset")
    except Exception as e:
        logger.error(f"❌ Failed to load breaches: {e}")
        app.breaches = []

    return app

# Initialize app
app = create_app(os.getenv('FLASK_ENV', 'development'))

# ============================================================================
# API ROUTES - HEALTH & STATUS
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.

    Returns: JSON with service status and loaded data count
    """
    return jsonify({
        "status": "healthy",
        "service": "BreachAlpha",
        "version": "1.1.0",
        "breaches_loaded": len(app.breaches),
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1', methods=['GET'])
def api_info():
    """API information and available endpoints."""
    return jsonify({
        "service": "BreachAlpha - Breach-to-Market Impact & Intelligence Engine",
        "version": "1.1.0",
        "endpoints": {
            "health": "GET /health",
            "api_info": "GET /api/v1",
            "list_breaches": "GET /api/v1/breaches/",
            "get_breach": "GET /api/v1/breaches/<query>",
            "analyze_breach": "POST /api/v1/market/analyze",
            "breach_patterns": "GET /api/v1/analysis/patterns",
            "breach_sector": "GET /api/v1/analysis/sector/<sector>",
            "export_pdf": "GET /api/v1/export/pdf/<query>",
            "intelligence_score": "GET /api/v1/intelligence/score/<query>",
            "intelligence_leaderboard": "GET /api/v1/intelligence/leaderboard"
        }
    }), 200

# ============================================================================
# API ROUTES - BREACH DATA
# ============================================================================

@app.route('/api/v1/breaches/', methods=['GET'])
@handle_errors
def list_breaches():
    """
    List all breaches with pagination.

    Query params:
        page: Page number (default: 1)
        per_page: Items per page (default: 50, max: 100)

    Returns: Paginated list of breaches
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Validation
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50

    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    breaches_page = app.breaches[start:end]

    # Format response
    summary = [
        {
            "company": b.get("company"),
            "ticker": b.get("ticker"),
            "breach_date": b.get("breach_date"),
            "sector": b.get("sector"),
            "severity": b.get("severity"),
            "records_affected": b.get("records_affected")
        }
        for b in breaches_page
    ]

    return jsonify({
        "breaches": summary,
        "pagination": {
            "total": len(app.breaches),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(app.breaches) + per_page - 1) // per_page
        }
    }), 200

@app.route('/api/v1/breaches/<query>', methods=['GET'])
@handle_errors
def get_single_breach(query: str):
    """
    Get a single breach by company name or ticker.

    Args:
        query: Company name or ticker symbol

    Returns: Breach details or 404 if not found
    """
    breach = find_breach(query, app.breaches)

    if not breach:
        return jsonify({
            "error": "Breach not found",
            "query": query,
            "suggestion": "Try searching by ticker (e.g., 'EFX') or full company name"
        }), 404

    return jsonify({"breach": breach}), 200

# ============================================================================
# API ROUTES - CORE ANALYSIS ENGINE
# ============================================================================

@app.route('/api/v1/market/analyze', methods=['POST', 'OPTIONS'])
@validate_query
@handle_errors
def analyze_breach_market_correlation():
    """
    🔥 CORE FEATURE: Analyze breach-to-market correlation

    Performs comprehensive financial impact analysis:
    1. Fetches company stock price (30 days pre/post breach)
    2. Fetches S&P 500 benchmark for same period
    3. Calculates relative underperformance
    4. Determines recovery time
    5. Generates AI analysis (correlation-based, not causal)
    6. Computes the Executive Cyber Risk Intelligence Score

    Input JSON:
        {
            "query": "EFX" or "Equifax"
        }

    Output JSON:
        {
            "found": true,
            "result": {
                "company": "Equifax",
                "ticker": "EFX",
                "company_pct_change": -10.7,
                "market_pct_change": -0.5,
                "relative_impact": -10.2,
                "recovery_days": 45,
                ...
            },
            "analysis": "AI-generated text...",
            "intelligence": { "overall_score": 82.4, "grade": "A", ... },
            "pdf_report": "..."
        }

    Or if not found:
        {
            "found": false,
            "query": "UNKNOWN",
            "analysis": "No major breach found..."
        }
    """
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()

    # Find breach in dataset
    breach = find_breach(query, app.breaches)

    if not breach:
        logger.info(f"Breach not found for query: {query}")
        fallback_analysis = analyze_no_breach(query)
        return jsonify({
            "found": False,
            "query": query,
            "analysis": fallback_analysis
        }), 200

    try:
        logger.info(f"Analyzing breach: {breach.get('company')} ({breach.get('ticker')})")

        ticker = breach.get("ticker")
        breach_date_str = breach.get("breach_date")

        # Parse breach date
        breach_date = datetime.strptime(breach_date_str, "%Y-%m-%d")
        start_date = breach_date - timedelta(days=30)
        end_date = breach_date + timedelta(days=30)

        logger.info(f"Fetching stock data for {ticker} from {start_date.date()} to {end_date.date()}")

        # Fetch stock data using collector
        company_df = get_price_window(ticker, breach_date_str, days=30)
        sp500_df = get_price_window("^GSPC", breach_date_str, days=30)

        # Validate data
        if company_df.empty or sp500_df.empty:
            logger.warning(f"No price data for {ticker}")
            return jsonify({
                "error": f"No price data available for {ticker}",
                "found": False
            }), 502

        if len(company_df) < 2 or len(sp500_df) < 2:
            logger.warning(f"Insufficient data points for {ticker}")
            return jsonify({
                "error": "Insufficient price history",
                "found": False
            }), 502

        # Calculate metrics using correlations module
        company_change = calculate_pct_change(company_df)
        market_change = calculate_pct_change(sp500_df)
        relative_impact = calculate_relative_impact(company_change, market_change)

        # Calculate recovery time
        pre_breach_price = company_df["Close"].iloc[0]
        recovery_days = calculate_recovery_days(company_df, pre_breach_price)
        recovery_text = (
            f"Recovered in {recovery_days} trading days"
            if recovery_days is not None
            else "Did not recover to pre-breach price within 30 days"
        )

        logger.info(f"Metrics calculated: relative_impact={relative_impact}pp, recovery={recovery_days} days")

        # Build correlation result for AI analysis
        correlation_result = {
            "company": breach.get("company"),
            "ticker": ticker,
            "breach_date": breach_date_str,
            "breach_type": breach.get("type"),
            "records_affected": breach.get("records_affected"),
            "sector": breach.get("sector"),
            "severity": breach.get("severity"),
            "attack_vector": breach.get("attack_vector"),
            "company_pct_change": company_change,
            "market_pct_change": market_change,
            "relative_impact": relative_impact,
            "recovery_days": recovery_days,
            "recovery_text": recovery_text
        }

        # Get AI analysis from Mistral
        logger.info("Requesting AI analysis from Mistral...")
        analysis_text = analyze_breach_impact(correlation_result)

        logger.info(f"✅ Analysis complete for {breach.get('company')}")

        # Compute Executive Intelligence Score
        intelligence = calculate_intelligence_score(
            breach, relative_impact=relative_impact, recovery_days=recovery_days
        )
        intelligence["market_data_used"] = True

        # Generate PDF
        pdf_report = None
        try:
            if not company_df.empty and not sp500_df.empty and len(company_df) > 5:
                dates = [d.strftime('%Y-%m-%d') for d in company_df.index]
                company_prices = company_df['Close'].tolist()
                market_prices = sp500_df['Close'].tolist()

                volatility = []
                for i in range(1, len(company_df)):
                    daily_pct_change = ((company_df['Close'].iloc[i] - company_df['Close'].iloc[i-1]) / company_df['Close'].iloc[i-1]) * 100
                    volatility.append(daily_pct_change)

                price_series = {
                    'dates': dates,
                    'company_prices': company_prices,
                    'market_prices': market_prices,
                    'volatility': volatility
                }

                os.makedirs('output/reports', exist_ok=True)
                pdf_report = generate_breach_report_pdf(
                    correlation_result=correlation_result,
                    analysis_text=analysis_text,
                    price_series=price_series,
                    output_dir='output/reports'
                )

                if pdf_report:
                    logger.info(f"✅ PDF generated: {pdf_report}")

        except Exception as e:
            logger.warning(f"PDF generation skipped: {e}")
            pdf_report = None

        return jsonify({
            "found": True,
            "result": correlation_result,
            "analysis": analysis_text,
            "intelligence": intelligence,
            "pdf_report": pdf_report
        }), 200

    except Exception as e:
        logger.error(f"Market analysis failed: {e}", exc_info=True)
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "found": False
        }), 502

# ============================================================================
# API ROUTES - INTELLIGENCE SCORE
# ============================================================================

@app.route('/api/v1/intelligence/score/<query>', methods=['GET'])
@handle_errors
def get_intelligence_score(query: str):
    """
    Get the Executive Cyber Risk Intelligence Score for a single company,
    without running the full market-analysis pipeline.

    Attempts to enrich the score with live market data (relative impact,
    recovery days); falls back to a static breach-metadata-only score if
    price data isn't available. Response indicates which mode was used via
    "market_data_used".

    Args:
        query: Company name or ticker symbol

    Returns: Intelligence score breakdown, or 404 if breach not found
    """
    breach = find_breach(query, app.breaches)

    if not breach:
        return jsonify({
            "error": "Breach not found",
            "query": query,
            "suggestion": "Try searching by ticker (e.g., 'EFX') or full company name"
        }), 404

    score = calculate_score_for_query(query, breach)

    return jsonify({
        "found": True,
        "company": breach.get("company"),
        "ticker": breach.get("ticker"),
        "intelligence": score
    }), 200

@app.route('/api/v1/intelligence/leaderboard', methods=['GET'])
@handle_errors
def intelligence_leaderboard():
    """
    Rank all breaches in the dataset by Executive Cyber Risk Intelligence
    Score, using static breach metadata only (no live market calls, so
    this endpoint stays fast even with large datasets).

    Query params:
        limit: Max number of results to return (default: 25, max: 200)
        order: 'desc' (highest risk first, default) or 'asc'

    Returns: Ranked list of companies with scores/grades/tiers
    """
    limit = request.args.get('limit', 25, type=int)
    order = request.args.get('order', 'desc')

    if limit < 1 or limit > 200:
        limit = 25

    ranked = []
    for breach in app.breaches:
        score = calculate_intelligence_score(breach)
        ranked.append({
            "company": breach.get("company"),
            "ticker": breach.get("ticker"),
            "sector": breach.get("sector"),
            "severity": breach.get("severity"),
            "breach_date": breach.get("breach_date"),
            "overall_score": score["overall_score"],
            "grade": score["grade"],
            "risk_tier": score["risk_tier"],
            "risk_color": score["risk_color"]
        })

    reverse = order != 'asc'
    ranked.sort(key=lambda x: x["overall_score"], reverse=reverse)

    return jsonify({
        "leaderboard": ranked[:limit],
        "total": len(ranked),
        "limit": limit,
        "order": 'asc' if not reverse else 'desc',
        "note": "Static score based on breach metadata only (severity, sector, records affected). Use /api/v1/intelligence/score/<query> or /api/v1/market/analyze for market-enriched scores."
    }), 200

# ============================================================================
# API ROUTES - ANALYSIS & INSIGHTS
# ============================================================================

@app.route('/api/v1/analysis/patterns', methods=['GET'])
@handle_errors
def breach_patterns():
    """
    Get breach patterns and statistics.

    Returns:
        Breach counts by sector, severity, and year
    """
    sector_counts = {}
    severity_counts = {}
    year_counts = {}

    for breach in app.breaches:
        # By sector
        sector = breach.get("sector", "Unknown")
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # By severity
        severity = breach.get("severity", "Unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # By year
        try:
            breach_date = breach.get("breach_date", "2000-01-01")
            year = breach_date[:4]
            year_counts[year] = year_counts.get(year, 0) + 1
        except:
            pass

    return jsonify({
        "total_breaches": len(app.breaches),
        "by_sector": sector_counts,
        "by_severity": severity_counts,
        "by_year": year_counts
    }), 200

@app.route('/api/v1/analysis/sector/<sector>', methods=['GET'])
@handle_errors
def breaches_by_sector(sector: str):
    """
    Get all breaches in a specific sector.

    Args:
        sector: Industry sector name

    Returns: List of breaches in that sector
    """
    sector_lower = sector.lower()
    sector_breaches = [
        b for b in app.breaches
        if b.get("sector", "").lower() == sector_lower
    ]

    if not sector_breaches:
        return jsonify({
            "sector": sector,
            "breaches": [],
            "count": 0
        }), 200

    summary = [
        {
            "company": b.get("company"),
            "ticker": b.get("ticker"),
            "breach_date": b.get("breach_date"),
            "severity": b.get("severity")
        }
        for b in sector_breaches
    ]

    return jsonify({
        "sector": sector,
        "breaches": summary,
        "count": len(sector_breaches)
    }), 200

# ============================================================================
# API ROUTES - PDF EXPORT (Future Feature)
# ============================================================================

@app.route('/api/v1/export/pdf/<query>', methods=['GET'])
@handle_errors
def export_breach_pdf(query: str):
    """
    Export breach analysis as PDF (future feature).

    Args:
        query: Company name or ticker

    Note: Requires prior analysis. This is a placeholder for future implementation.
    """
    breach = find_breach(query, app.breaches)

    if not breach:
        return jsonify({"error": "Breach not found"}), 404

    try:
        # TODO: Implement PDF generation
        # pdf_path = generate_breach_report(breach, correlation_result)
        # return send_file(pdf_path, as_attachment=True)

        return jsonify({
            "message": "PDF export feature coming soon",
            "breach": breach.get("company")
        }), 501  # Not Implemented

    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        return jsonify({"error": "PDF generation failed"}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(e):
    """Handle 400 Bad Request."""
    return jsonify({
        "error": "Bad request",
        "message": str(e)
    }), 400

@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found."""
    return jsonify({
        "error": "Endpoint not found",
        "message": "Check the API documentation at /api/v1"
    }), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server Error."""
    logger.error(f"Server error: {e}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.before_request
def log_request():
    """Log incoming requests."""
    if request.method != 'OPTIONS':
        logger.debug(f"{request.method} {request.path}")

@app.after_request
def log_response(response):
    """Log response status."""
    if request.method != 'OPTIONS':
        logger.debug(f"Response: {response.status_code}")
    return response

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'

    logger.info(f"🚀 Starting BreachAlpha Backend")
    logger.info(f"   Host: {host}:{port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Breaches: {len(app.breaches)}")

    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
