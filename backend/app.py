"""
BreachAlpha Backend - Production-Ready Flask Application
Breach-to-Market Impact Engine

A comprehensive AI-powered tool that correlates historical data breaches
with stock market movements to analyze financial impact.
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional, Tuple

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
        "version": "1.0.0",
        "breaches_loaded": len(app.breaches),
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1', methods=['GET'])
def api_info():
    """API information and available endpoints."""
    return jsonify({
        "service": "BreachAlpha - Breach-to-Market Impact Engine",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "api_info": "GET /api/v1",
            "list_breaches": "GET /api/v1/breaches/",
            "get_breach": "GET /api/v1/breaches/<query>",
            "analyze_breach": "POST /api/v1/market/analyze",
            "breach_patterns": "GET /api/v1/analysis/patterns"
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
            "analysis": "AI-generated text..."
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
    "pdf_report": pdf_report
}), 200

    except Exception as e:
        logger.error(f"Market analysis failed: {e}", exc_info=True)
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "found": False
        }), 502

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
