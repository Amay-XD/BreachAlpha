from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
MODEL_ID = "llama-3.3-70b-versatile"

def build_prompt(result):
    return f"""
You are a financial security analyst.

Company: {result['company']} ({result['ticker']})
Breach date: {result['breach_date']}
Breach type: {result['breach_type']}
Stock price change (30 days around breach): {result['company_pct_change']}%
S&P 500 change (same period): {result['market_pct_change']}%
Relative underperformance: {result['relative_impact']} percentage points
Recovery: {result['recovery']}

Write a short analysis (under 300 words) explaining:
1. Did this breach appear to have measurable financial impact?
2. How does this compare to typical market movements?
3. What does the recovery time suggest?

Use a neutral, analytical tone. Frame findings as correlation, not causation —
use phrases like 'appears associated with' or 'occurred alongside', never
'caused' or 'resulted in'. Do not use words like 'devastating', 'catastrophic',
or 'plummeted' unless the numbers genuinely support extreme characterization.
Be factual. Do not speculate beyond the numbers given.
"""

def build_no_breach_prompt(query):
    return f"""
No major historical data breach is on record for '{query}' in this tool's dataset.
Write 2-3 sentences explaining that no major breach was found, and suggest the
user check official sources for the most current information.
"""

def analyze_breach_impact(result):
    prompt = build_prompt(result)
    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"

def analyze_no_breach(query):
    prompt = build_no_breach_prompt(query)
    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"
