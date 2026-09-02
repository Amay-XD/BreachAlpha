

# BreachAlpha 🛡️💹

> **Every breach tells a story.  
> We reveal its market impact.**

BreachAlpha is a cyber-risk intelligence engine that correlates historical data breaches with stock-market movements using AI-powered analysis and executive intelligence scoring.

It transforms a cybersecurity incident into an understandable financial-risk narrative — helping users explore breach severity, market impact, recovery behavior, and sector-level risk.

---

## 🌐 Live Demo

### 🚀 Frontend
https://breachalpha.vercel.app/

### 🔌 Backend API
https://breachalpha-lsbo.onrender.com

### ❤️ Backend Health
https://breachalpha-lsbo.onrender.com/health

### 📦 GitHub
https://github.com/Amay-XD/BreachAlpha

---

## ⚠️ Market Data Notice

**BreachAlpha MVP may use synthetic/simulated market data as a fallback when the Alpha Vantage market-data provider is unavailable or fails.**

This fallback is intentional for demonstration and system resilience.

The architecture is designed so the market-data layer can be replaced or connected to live financial data providers without changing the core intelligence engine.

> **Important:** BreachAlpha is a cybersecurity and financial intelligence prototype. Its outputs are for informational and demonstration purposes only and should not be treated as financial advice or as the sole basis for investment decisions.

---

## 🎯 What BreachAlpha Does

BreachAlpha connects two worlds:

**Cybersecurity incidents → Financial market impact**

Given a company or breach, the platform analyzes:

- Breach severity
- Records affected
- Market movement
- Relative performance against the S&P 500
- Recovery behavior
- Sector risk
- Historical breach patterns
- AI-generated executive intelligence

The goal is simple:

> **Turn a breach event into a measurable market-risk story.**

---

# ✨ Features

## 🔍 Breach Analysis

- Search historical 250+ data breaches
- Search and filter companies
- Instant breach intelligence
- Market-impact correlation
- Recovery timeline analysis
- Company-level metrics
- Breach severity assessment

---

## 🤖 AI-Powered Intelligence

BreachAlpha integrates **Mistral AI** to generate contextual analysis of breach-market relationships.

### AI capabilities

- Natural-language breach analysis
- Context-aware interpretation
- Breach severity assessment
- Sector impact interpretation
- Market-event explanation
- Executive-level summaries

---

## 🧠 Executive Cyber Risk Intelligence Score

BreachAlpha produces a **0–100 composite intelligence score**.

The score combines five major factors:

| Factor | Weight |
|---|---:|
| Breach Severity | 25% |
| Market Impact | 30% |
| Recovery Speed | 20% |
| Records Affected | 15% |
| Sector Risk | 10% |

### Output

- Overall score
- Grade from A+ to F
- Risk tier from Low → Severe
- Individual factor scores
- Weighted contribution breakdown

---

## 📈 Market Correlation Engine

The platform analyzes how a company's stock behaved around a breach event.

### Analysis includes

- Relative market impact
- Pre-breach performance
- Post-breach performance
- S&P 500 benchmark comparison
- Recovery timeline
- Relative underperformance
- Market-event interpretation

The system is designed to distinguish company-specific movement from broader market movement.

---

## 📊 Intelligence Dashboard

The frontend provides a centralized intelligence interface featuring:

- Company search
- Interactive market analysis
- Risk visualization
- Intelligence scoring
- Breach pattern analysis
- Sector analysis
- Executive summaries
- Market correlation visualization

---

# 🏗️ Architecture

```text
                         BREACHALPHA
                              │
                ┌─────────────┴─────────────┐
                │                           │
          React Frontend              Flask Backend
             Vercel                      Render
                │                           │
                │        REST API            │
                └──────────────┬────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              Breach Dataset          AI Engine
                    │                 Mistral AI
                    │                     │
                    └──────────┬──────────┘
                               │
                       Market Data Layer
                               │
                    ┌──────────┴──────────┐
                    │                     │
              Live Provider         Synthetic
              when available          Fallback
````

The market-data layer is intentionally abstracted so providers can be changed without redesigning the core intelligence engine.

---

# 🛠️ Tech Stack

## Backend

* **Python 3.9+**
* **Flask 3.0**
* **Mistral AI API**
* **Pandas**
* **NumPy**
* **yfinance**
* **Flask-CORS**
* **Gunicorn**
* **Render**

## Frontend

* **React**
* **Vite**
* **Axios**
* **CSS**
* **Vercel**

## Infrastructure

* **GitHub** — Source control
* **Render** — Backend deployment
* **Vercel** — Frontend deployment
* **REST API** — Frontend/backend communication

---

# 🚀 Quick Start

## Prerequisites

* Python 3.9+
* Node.js
* npm
* Git
* Mistral API key

---

## Backend

Clone the repository:

```bash
git clone https://github.com/Amay-XD/BreachAlpha.git
cd BreachAlpha
```

Create a virtual environment:

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Add your API credentials to `.env`.

Run the backend:

```bash
python run.py
```

Backend:

```text
http://127.0.0.1:5000
```

---

# 💻 Frontend

Move into the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the frontend environment file:

```bash
cp .env.example .env
```

For local development:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000
```

Start the frontend:

```bash
npm run dev
```

The Vite development server will provide the local frontend URL.

---

# 🧪 API

## Health & Information

```http
GET /health
GET /api/v1
```

## Breach Data

```http
GET /api/v1/breaches/
GET /api/v1/breaches/<query>
GET /api/v1/analysis/patterns
GET /api/v1/analysis/sector/<sector>
```

## Market & Intelligence

```http
POST /api/v1/market/analyze
GET /api/v1/intelligence/score/<query>
GET /api/v1/intelligence/leaderboard
```

---

# 📡 Example API Request

```bash
curl -X POST https://breachalpha-lsbo.onrender.com/api/v1/market/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"Equifax"}'
```

Example response structure:

```json
{
  "found": true,
  "result": {
    "company": "Equifax",
    "ticker": "EFX",
    "breach_date": "2017-09-07",
    "company_pct_change": -10.7,
    "market_pct_change": -0.5,
    "relative_impact": -10.2,
    "recovery_days": 45,
    "records_affected": 147000000,
    "severity": "critical"
  },
  "analysis": "AI-generated breach-market analysis",
  "intelligence": {
    "overall_score": 82.4,
    "grade": "A",
    "risk_tier": "High"
  }
}
```

---

# 🌍 Production Deployment

## Backend — Render

The production backend is deployed at:

```text
https://breachalpha-lsbo.onrender.com
```

Render runs the Flask application using Gunicorn.

Typical start command:

```bash
gunicorn -w 4 -b 0.0.0.0:$PORT run:app
```

### Required backend environment variables

```env
FLASK_ENV=production
SECRET_KEY=your_secure_secret
MISTRAL_API_KEY=your_mistral_api_key
CORS_ORIGINS=https://breachalpha.vercel.app
```

Never commit real credentials.

---

## Frontend — Vercel

The production frontend is deployed at:

```text
https://breachalpha.vercel.app/
```

Production API configuration:

```env
VITE_API_BASE_URL=https://breachalpha-lsbo.onrender.com
```

The frontend communicates with the Render backend through the REST API.

---

# 🔐 Security

BreachAlpha follows several basic security practices:

* Environment variables for secrets
* `.gitignore` protection for `.env`
* Restricted CORS origins
* Input validation
* Backend error handling
* No API keys stored in frontend source code

> **Never commit `.env` files or API credentials to GitHub.**

---

# 📊 Data Architecture

BreachAlpha currently uses a hybrid market-data approach.

### Primary

Live market-data provider when available.

### Fallback

Synthetic/simulated market data may be used when the external market-data provider is unavailable.

This allows the intelligence engine and UI to remain functional during development and demonstrations.

### Production direction

The data layer is designed to support real financial-data providers such as:

* Alpha Vantage
* Polygon
* Other compatible market-data providers

Provider integration can evolve independently from the core breach-intelligence and scoring systems.

---

# 🧠 Intelligence Pipeline

```text
Company Search
      │
      ▼
Breach Identification
      │
      ▼
Breach Metadata
      │
      ▼
Market Data Retrieval
      │
      ├── Live Data Available
      │         │
      │         ▼
      │      Market Analysis
      │
      └── Provider Failure
                │
                ▼
         Synthetic Fallback
                │
                ▼
        Market Correlation
                │
                ▼
      Executive Intelligence
                │
                ▼
          Risk Score
```

---

# 🗺️ Roadmap

Potential future improvements include:

* [ ] Expanded live financial-data integrations
* [ ] PostgreSQL database
* [ ] User authentication
* [ ] Saved searches
* [ ] Advanced filtering
* [ ] Portfolio impact analysis
* [ ] Historical trend analysis
* [ ] Breach notification alerts
* [ ] Email intelligence reports
* [ ] Real-time breach monitoring
* [ ] Mobile experience

---

# 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/amazing-feature
```

3. Commit your changes

```bash
git commit -m "Add amazing feature"
```

4. Push the branch

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request

---

# 📄 License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

---

# 👨‍💻 Author

**Amay Jogdand**

GitHub:

[https://github.com/Amay-XD](https://github.com/Amay-XD)

LinkedIn:

[www.linkedin.com/in/amay-jogdand]

---

# 🙏 Acknowledgments

* Mistral AI
* Render
* Vercel
* yfinance
* Flask
* React
* The open-source cybersecurity and financial-data communities

---

# 🎯 Project Status

**BreachAlpha MVP — Production Deployed**

* ✅ Frontend deployed
* ✅ Backend deployed
* ✅ REST API operational
* ✅ AI analysis integration
* ✅ Executive intelligence scoring
* ✅ Breach-market correlation
* ✅ Market-data fallback
* ✅ Production frontend/backend integration
* ✅ CORS configuration
* ✅ Responsive intelligence dashboard

---

## 🔗 Production Links

**Frontend**

[https://breachalpha.vercel.app/](https://breachalpha.vercel.app/)

**Backend**

[https://breachalpha-lsbo.onrender.com](https://breachalpha-lsbo.onrender.com)

**Health Check**

[https://breachalpha-lsbo.onrender.com/health](https://breachalpha-lsbo.onrender.com/health)

**GitHub Repository**

[https://github.com/Amay-XD/BreachAlpha](https://github.com/Amay-XD/BreachAlpha)

---

<div align="center">

### Every breach tells a story.

### We reveal its market impact.

Built with 🛡️ + 💹 + AI

</div>
```

