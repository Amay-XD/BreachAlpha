import { useEffect, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import type { CSSProperties, ReactNode } from "react";
import {
  AlertTriangle, ArrowLeft, ArrowUpRight, BrainCircuit, Building2, CalendarDays, ChartNoAxesCombined,
  Database, Gauge, Landmark, LockKeyhole, Radar, RefreshCw, Route as RouteIcon, ShieldAlert, Sparkles,
  WifiOff,
} from "lucide-react";
import { analyzeBreachMarket, getBreachPatterns } from "./api";
import type { AnalyzeBreachFoundResponse, BreachPatternsResponse } from "./api";
import { Layout, Search, Loader } from "./ui";
import Charts from "./charts";

const statistics = [
  ["40+", "Years of breach history"],
  ["3,800+", "Market-moving incidents"],
  ["11", "Executive risk signals"],
  ["24/7", "Intelligence availability"],
] as const;

const features = [
  { icon: Radar, title: "Breach-to-market signal", text: "Pinpoint how a disclosed incident shaped investor confidence, not just headlines." },
  { icon: BrainCircuit, title: "Executive intelligence", text: "Translate technical exposure into a concise view of financial and business risk." },
  { icon: ChartNoAxesCombined, title: "Relative market impact", text: "Read company performance against the market context surrounding an incident." },
];

function Home() {
  const navigate = useNavigate();
  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    try {
      const savedSearches: unknown = JSON.parse(window.localStorage.getItem("breachalpha-recent-searches") ?? "[]");
      return Array.isArray(savedSearches) && savedSearches.every((item) => typeof item === "string") ? savedSearches : [];
    } catch { return []; }
  });

  const searchCompany = (query: string) => {
    const updatedSearches = [query, ...recentSearches.filter((item) => item.toLowerCase() !== query.toLowerCase())].slice(0, 4);
    setRecentSearches(updatedSearches);
    window.localStorage.setItem("breachalpha-recent-searches", JSON.stringify(updatedSearches));
    navigate(`/company/${encodeURIComponent(query)}`);
  };

  return (
    <Layout>
      <main>
        <section className="hero" id="top">
          <div className="hero-noise" /><div className="hero-orb orb-one" /><div className="hero-orb orb-two" /><div className="hero-lines" />
          <div className="hero-copy">
            <div className="section-kicker"><span /> BREACH-TO-MARKET INTELLIGENCE</div>
            <h1>Every breach tells a story.<br /><em>We reveal its market impact.</em></h1>
            <p>Search historical cyber incidents and receive AI-powered executive intelligence reports on financial impact, business risk, and market response.</p>
          </div>
          <Search onSearch={searchCompany} recentSearches={recentSearches} />
          <div className="hero-footnote"><span className="live-indicator" /> ANALYZING THE SIGNAL BETWEEN CYBER RISK AND MARKET RESPONSE</div>
        </section>
        <section className="stat-section" aria-label="Platform statistics">{statistics.map(([number, label]) => <div className="stat" key={label}><strong>{number}</strong><span>{label}</span></div>)}</section>
        <section className="content-section why-section" id="methodology">
          <div className="section-intro"><p className="eyebrow">WHY BREACHALPHA</p><h2>Cyber events are business events.</h2><p>Most breach data ends at the incident. BreachAlpha follows the signal into investor sentiment, business resilience, and executive decision-making.</p></div>
          <div className="signal-card"><div className="signal-card-top"><span>INTELLIGENCE PATH</span><span>01—04</span></div><div className="signal-path">
            <div><ShieldAlert size={18} /><b>Incident</b><small>Historical breach</small></div><i />
            <div><Database size={18} /><b>Context</b><small>Exposure data</small></div><i />
            <div><ChartNoAxesCombined size={18} /><b>Impact</b><small>Market response</small></div><i />
            <div><Sparkles size={18} /><b>Intelligence</b><small>Executive view</small></div>
          </div></div>
        </section>
        <section className="content-section product-section"><div className="section-heading-row"><div><p className="eyebrow">PRODUCT CAPABILITIES</p><h2>Clarity for the questions that matter.</h2></div><a href="#top">Explore the platform <ArrowUpRight size={16} /></a></div>
          <div className="feature-grid">{features.map(({ icon: Icon, title, text }, index) => <article className="feature-card" key={title}><div className="feature-card-head"><span>0{index + 1}</span><Icon size={21} /></div><h3>{title}</h3><p>{text}</p><span className="feature-link">Built for decision makers <ArrowUpRight size={15} /></span></article>)}</div>
        </section>
        <section className="content-section technology-section"><div className="technology-copy"><p className="eyebrow">TRUSTED SIGNALS</p><h2>Built for clear thinking under pressure.</h2><p>Purpose-built intelligence that keeps the journey from breach to boardroom brief concise, credible, and comprehensible.</p></div><div className="technology-grid"><div><LockKeyhole size={18} /><span>SECURE BY DESIGN</span><strong>Protected research environment</strong></div><div><Database size={18} /><span>HISTORICAL CONTEXT</span><strong>Structured breach intelligence</strong></div><div><Sparkles size={18} /><span>AI SYNTHESIS</span><strong>Executive-ready narrative</strong></div></div></section>
      </main>
      <footer className="footer"><div className="footer-brand"><ShieldAlert size={17} /> BREACH<span>ALPHA</span></div><p>Cyber risk, translated into market intelligence.</p><span>© 2026 BREACHALPHA</span></footer>
      <p className="site-disclaimer">This is a portfolio project built for educational and demonstration purposes. Information may contain inaccuracies. Always verify findings using official sources before making financial, legal, or security decisions.</p>
    </Layout>
  );
}

type CompanyPageState = "loading" | "ready" | "empty" | "not-found" | "offline" | "error";

function Company() {
  const { company } = useParams();
  const companyName = company ?? "Company";
  const [pageState, setPageState] = useState<CompanyPageState>("loading");
  const [report, setReport] = useState<AnalyzeBreachFoundResponse | null>(null);
  const [patterns, setPatterns] = useState<BreachPatternsResponse | null>(null);
  const [message, setMessage] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let isCurrent = true;
    let minimumLoadingTimer = 0;
    let finishMinimumLoading: () => void;
    const minimumLoadingPeriod = new Promise<void>((resolve) => {
      finishMinimumLoading = resolve;
      minimumLoadingTimer = window.setTimeout(resolve, 6_500);
    });

    async function loadCompanyIntelligence() {
      setPageState("loading");
      setReport(null);
      setPatterns(null);

      void getBreachPatterns()
        .then((response) => { if (isCurrent) setPatterns(response); })
        .catch(() => { if (isCurrent) setPatterns(null); });

      try {
        const response = await analyzeBreachMarket(companyName);
        await minimumLoadingPeriod;
        if (!isCurrent) return;

        if (response.found) {
          setReport(response);
          setPageState("ready");
          return;
        }

        if ("analysis" in response) {
          setMessage(response.analysis);
          setPageState("empty");
        } else {
          setMessage(response.error);
          setPageState("error");
        }
      } catch (error) {
        await minimumLoadingPeriod;
        if (!isCurrent) return;

        if (axios.isAxiosError(error)) {
          if (!error.response) {
            setMessage("The BreachAlpha backend could not be reached. Confirm the Flask service is running and try again.");
            setPageState("offline");
          } else if (error.response.status === 404) {
            setMessage(`API endpoint not found (HTTP 404): ${error.response.data?.error ?? "The server received this request but does not expose the requested route."}`);
            setPageState("not-found");
          } else if (error.response.status === 400) {
            setMessage(`Invalid request (HTTP 400): ${error.response.data?.error ?? "The intelligence engine rejected this search query."}`);
            setPageState("error");
          } else if (error.response.status >= 500) {
            setMessage(`Backend analysis failed (HTTP ${error.response.status}): ${error.response.data?.error ?? "The intelligence engine could not complete this analysis."}`);
            setPageState("error");
          } else {
            setMessage(`Request failed (HTTP ${error.response.status}): ${error.response.data?.error ?? "Market intelligence could not be generated right now."}`);
            setPageState("error");
          }
          return;
        }

        setMessage("An unexpected error interrupted this intelligence request.");
        setPageState("error");
      }
    }

    void loadCompanyIntelligence();
    return () => { isCurrent = false; window.clearTimeout(minimumLoadingTimer); finishMinimumLoading(); };
  }, [companyName, retryCount]);

  const retry = () => setRetryCount((count) => count + 1);

  return (
    <Layout>
      <main className="company-page">
        <div className="company-page-header">
          <Link to="/" className="back-link"><ArrowLeft size={16} /> Research another company</Link>
          <div className="company-header-actions"><span className="page-label">COMPANY INTELLIGENCE</span></div>
        </div>

        {pageState === "loading" && <CompanyAnalysisLoader companyName={companyName} />}
        {pageState === "ready" && report && <CompanyReport report={report} patterns={patterns} />}
        {pageState === "empty" && <CompanyState icon={<Database size={24} />} title="No breach intelligence found" message={message} />}
        {pageState === "not-found" && <CompanyState icon={<RouteIcon size={24} />} title="Company route not found" message={message} retry={retry} />}
        {pageState === "offline" && <CompanyState icon={<WifiOff size={24} />} title="Backend offline" message={message} retry={retry} />}
        {pageState === "error" && <CompanyState icon={<AlertTriangle size={24} />} title="Intelligence request failed" message={message} retry={retry} />}
      </main>
    </Layout>
  );
}

function CompanyReport({ report, patterns }: { report: AnalyzeBreachFoundResponse; patterns: BreachPatternsResponse | null }) {
  const { result, intelligence } = report;
  const records = typeof result.records_affected === "number"
    ? new Intl.NumberFormat("en-US").format(result.records_affected)
    : result.records_affected ?? "Not reported";

  return (
    <div className="company-report">
      <section className="company-hero-panel">
        <div>
          <div className="company-identity"><Building2 size={16} /> {result.sector ?? "Industry not reported"}</div>
          <h1>{result.company ?? "Company intelligence"}</h1>
          <p>{intelligence.summary}</p>
          <div className="company-tags">
            <span className="severity-tag">{result.severity ?? "Unknown"} severity</span>
            {result.ticker && <span>{result.ticker}</span>}
            <span><CalendarDays size={14} /> {result.breach_date ?? "Date not reported"}</span>
          </div>
        </div>
        <div id="risk-score" className="score-panel" style={{ "--risk-color": intelligence.risk_color, "--risk-progress": `${intelligence.overall_score * 3.6}deg` } as CSSProperties}>
          <span>EXECUTIVE RISK SCORE</span>
          <div className="score-gauge"><strong>{intelligence.overall_score}</strong><small>/ 100</small></div>
          <div><b>{intelligence.grade}</b><em>{intelligence.risk_tier}</em></div>
        </div>
      </section>

      <section className="company-detail-grid" aria-label="Incident details">
        <article><Database size={18} /><span>AFFECTED RECORDS</span><strong>{records}</strong></article>
        <article><ShieldAlert size={18} /><span>ATTACK VECTOR</span><strong>{result.attack_vector ?? "Not reported"}</strong></article>
        <article><Landmark size={18} /><span>INDUSTRY</span><strong>{result.sector ?? "Not reported"}</strong></article>
        <article><Gauge size={18} /><span>RECOVERY</span><strong>{result.recovery_text}</strong></article>
      </section>

      <section className="report-grid">
        <article className="report-card executive-summary">
          <p className="eyebrow">EXECUTIVE SUMMARY</p>
          <h2>{intelligence.summary}</h2>
          <p>{report.analysis}</p>
        </article>
        <article className="report-card risk-breakdown">
          <p className="eyebrow">RISK SCORE BREAKDOWN</p>
          <div className="factor-list">
            {intelligence.factors.map((factor) => (
              <div className="factor-row" key={factor.key}>
                <span>{factor.label}</span>
                <div className="factor-meter"><i style={{ width: `${factor.score ?? 0}%` }} /></div>
                <b>{factor.available ? factor.score : "—"}</b>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="report-grid lower-report-grid">
        <article className="report-card incident-timeline">
          <p className="eyebrow">INCIDENT TIMELINE</p>
          <div className="timeline-entry"><span>01</span><div><b>Breach disclosure</b><p>{result.breach_date ?? "Disclosure date not reported"}</p></div></div>
          <div className="timeline-entry"><span>02</span><div><b>Market analysis window</b><p>30 days before and after the reported incident.</p></div></div>
          <div className="timeline-entry"><span>03</span><div><b>Recovery assessment</b><p>{result.recovery_text}</p></div></div>
          <div className="timeline-entry"><span>04</span><div><b>Present intelligence view</b><p>Executive assessment generated from the current backend response.</p></div></div>
        </article>
        <article className="report-card financial-impact">
          <p className="eyebrow">FINANCIAL IMPACT</p>
          <div className="impact-stat"><span>COMPANY MOVE</span><strong>{result.company_pct_change}%</strong></div>
          <div className="impact-stat"><span>MARKET MOVE</span><strong>{result.market_pct_change}%</strong></div>
          <div className="impact-stat impact-highlight"><span>RELATIVE IMPACT</span><strong>{result.relative_impact}pp</strong></div>
        </article>
      </section>

      <section className="report-grid lower-report-grid">
        <article className="report-card market-analysis">
          <p className="eyebrow">MARKET ANALYSIS</p>
          <p>The backend classified this incident with a {result.severity ?? "not reported"} severity and calculated relative performance against the S&amp;P 500 over its documented analysis window.</p>
          <div className="market-data-note"><span /> {intelligence.market_data_used ? "Live market data was used for this assessment." : "Static breach metadata was used for this assessment."}</div>
        </article>
        <article className="report-card recommendation-card">
          <p className="eyebrow">RECOMMENDATION</p>
          <h3>No structured recommendation available.</h3>
          <p>The documented backend returns an executive analysis narrative but does not expose a distinct recommendation field. This area remains intentionally unfilled rather than fabricating guidance.</p>
        </article>
      </section>

      <Charts patterns={patterns} />

      <footer className="company-report-footer">
        <a href="https://github.com/Amay-XD/BreachAlpha" target="_blank" rel="noopener noreferrer"><GithubMark /> GitHub Repository</a>
        <div className="company-report-notices">
          <p>This is a portfolio project built for educational and demonstration purposes. Information may contain inaccuracies. Always verify findings using official sources before making financial, legal, or security decisions.</p>
          <p className="market-data-warning">Market data notice: If the Alpha Vantage market-data feed is unavailable, BreachAlpha may use simulated data for demonstration purposes. Always verify market data independently before making financial decisions.</p>
        </div>
      </footer>
    </div>
  );
}

function CompanyAnalysisLoader({ companyName }: { companyName: string }) {
  return (
    <section className="company-analysis-loader" aria-label={`Analyzing intelligence for ${companyName}`}>
      <div className="analysis-loader-mark"><span /><span /><span /></div>
      <p className="eyebrow">BREACHALPHA / EXECUTIVE INTELLIGENCE</p>
      <h1>Building the intelligence brief for <em>{companyName}.</em></h1>
      <div className="analysis-loader-steps" aria-label="Analysis progress">
        <span>Connecting intelligence engine</span><span>Collecting historical breaches</span><span>Analyzing financial correlation</span><span>Calculating intelligence score</span><span>Generating executive summary</span><span>Rendering dashboard</span>
      </div>
      <p>Report assembly is deliberate. This typically takes a few seconds.</p>
    </section>
  );
}

function CompanyState({ icon, title, message, retry }: { icon: ReactNode; title: string; message: string; retry?: () => void }) {
  return (
    <section className="company-state">
      <div className="company-state-icon">{icon}</div>
      <p className="eyebrow">COMPANY INTELLIGENCE</p>
      <h1>{title}</h1>
      <p>{message}</p>
      <div className="company-state-actions">
        {retry && <button type="button" onClick={retry}><RefreshCw size={15} /> Retry request</button>}
        <Link to="/"><ArrowLeft size={15} /> Return to search</Link>
      </div>
    </section>
  );
}

function GithubMark() {
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.54 1.04 1.54 1.04.9 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.64-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.99 1.03-2.69-.1-.25-.45-1.28.1-2.67 0 0 .84-.27 2.75 1.03a9.5 9.5 0 0 1 5 0c1.9-1.3 2.74-1.03 2.74-1.03.55 1.39.2 2.42.1 2.67.65.7 1.03 1.6 1.03 2.69 0 3.84-2.34 4.68-4.57 4.93.36.31.68.9.68 1.81v2.68c0 .27.18.58.69.48A10 10 0 0 0 12 2Z" /></svg>;
}


export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => { const timer = window.setTimeout(() => setIsLoading(false), 1450); return () => window.clearTimeout(timer); }, []);
  if (isLoading) return <Loader />;
  return <Routes><Route path="/" element={<Home />} /><Route path="/company/:company" element={<Company />} /><Route path="*" element={<Home />} /></Routes>;
}
