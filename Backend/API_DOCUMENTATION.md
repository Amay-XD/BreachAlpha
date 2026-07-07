# BreachAlpha API Documentation

## Base URL
```
http://localhost:5000/api/v1
```

## Authentication
All endpoints that modify data (POST, PUT, DELETE) require:
```
Header: X-API-Key: <your-api-key>
```

---

## Breaches Endpoints

### GET /breaches
Retrieve all breaches with filtering and pagination.

**Query Parameters:**
- `sector` (string): Filter by sector
- `severity` (string): Filter by severity (Critical, High, Medium)
- `start_date` (string): Filter from date (YYYY-MM-DD)
- `end_date` (string): Filter to date (YYYY-MM-DD)
- `search` (string): Search in company name or summary
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 50, max: 100)

**Example:**
```bash
curl "http://localhost:5000/api/v1/breaches?sector=Technology&severity=Critical&page=1"
```

**Response:**
```json
{
  "breaches": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "pages": 3
  },
  "filters": {...}
}
```

### GET /breaches/<company_name>
Get breach details by company name.

**Example:**
```bash
curl "http://localhost:5000/api/v1/breaches/Equifax"
```

### GET /breaches/ticker/<ticker>
Get breach details by ticker symbol.

**Example:**
```bash
curl "http://localhost:5000/api/v1/breaches/ticker/EFX"
```

### GET /breaches/sector/<sector>
Get all breaches in a specific sector.

**Example:**
```bash
curl "http://localhost:5000/api/v1/breaches/sector/Financial%20Services"
```

### GET /breaches/stats
Get aggregate statistics about breaches.

**Response:**
```json
{
  "total_breaches": 18,
  "total_records_affected": 2500000000,
  "sectors": {...},
  "severities": {...},
  "by_year": {...}
}
```

### POST /breaches
Add a new breach (requires authentication).

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "company": "Company Name",
  "ticker": "NYSE:XXX",
  "breach_date": "2023-09-15",
  "type": "Ransomware",
  "records_affected": "1M",
  "sector": "Technology",
  "attack_vector": "Social engineering",
  "severity": "Critical",
  "summary": "Description of breach and impact."
}
```

---

## Analysis Endpoints

### GET /analysis/patterns
Analyze breach patterns and trends.

**Query Parameters:**
- `year` (integer): Filter by year
- `sector` (string): Filter by sector

**Response:**
```json
{
  "total_breaches_in_period": 10,
  "most_common_attack_vectors": {...},
  "breach_types": {...}
}
```

### GET /analysis/attack-vectors
Analyze most common attack vectors.

### GET /analysis/sector-risk
Calculate risk scores by sector.

### GET /analysis/timeline
Get timeline of breaches over time.

**Query Parameters:**
- `granularity` (string): 'year', 'quarter', 'month' (default: 'year')

### GET /analysis/severity-distribution
Get distribution of breach severity levels.

---

## Market Impact Endpoints

### GET /market/impact/<company_name>
Get market impact analysis for a company's breach.

**Response:**
```json
{
  "company": "Equifax",
  "ticker": "NYSE:EFX",
  "breach_date": "2017-09-07",
  "price_before_breach": 146.50,
  "price_after_breach": 141.20,
  "price_change_percent": -3.61,
  "analysis_period": "2017-08-08 to 2017-10-07"
}
```

### GET /market/recovery/<company_name>
Analyze breach recovery timeline and metrics.

### GET /market/financial-impact/<company_name>
Calculate estimated financial impact of breach.

**Response:**
```json
{
  "company": "Equifax",
  "total_estimated_impact": 700000000,
  "cost_breakdown": {
    "breach_remediation_cost": ...,
    "incident_response_cost": ...,
    "estimated_regulatory_fines": ...
  }
}
```

### GET /market/sector-impact
Get aggregate market impact by sector.

---

## Error Responses

**400 Bad Request**
```json
{
  "error": "Validation failed",
  "details": [...]
}
```

**401 Unauthorized**
```json
{
  "error": "Missing or invalid API key"
}
```

**404 Not Found**
```json
{
  "error": "Resource not found",
  "company": "Unknown Company"
}
```

**429 Too Many Requests**
```json
{
  "error": "Rate limit exceeded"
}
```

---

## Rate Limiting

- **Default**: 200 requests per day, 50 per hour
- **Rate limit headers** are included in all responses

---

## Examples

### Get all critical breaches in 2023
```bash
curl "http://localhost:5000/api/v1/breaches?severity=Critical&start_date=2023-01-01&end_date=2023-12-31"
```

### Get sector risk assessment
```bash
curl "http://localhost:5000/api/v1/analysis/sector-risk"
```

### Get market impact for specific company
```bash
curl "http://localhost:5000/api/v1/market/impact/Equifax"
```

### Add new breach (with authentication)
```bash
curl -X POST http://localhost:5000/api/v1/breaches \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '@breach_data.json'
```
