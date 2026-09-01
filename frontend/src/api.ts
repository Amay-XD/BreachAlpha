/**
 * BreachAlpha API response models.
 *
 * These types mirror fields emitted by the Flask application. Dataset-backed
 * fields are nullable because the backend reads them with `dict.get()`.
 */

export type Nullable<T> = T | null;

export interface BreachSummary {
  company: Nullable<string>;
  ticker: Nullable<string>;
  breach_date: Nullable<string>;
  sector: Nullable<string>;
  severity: Nullable<string>;
  records_affected: Nullable<number | string>;
}

export interface BreachRecord extends BreachSummary {
  type?: Nullable<string>;
  attack_vector?: Nullable<string>;
  [key: string]: unknown;
}

export interface Pagination {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface HealthResponse {
  status: "healthy";
  service: "BreachAlpha";
  version: "1.1.0";
  breaches_loaded: number;
  timestamp: string;
}

export interface ApiInfoResponse {
  service: "BreachAlpha - Breach-to-Market Impact & Intelligence Engine";
  version: "1.1.0";
  endpoints: {
    health: "GET /health";
    api_info: "GET /api/v1";
    list_breaches: "GET /api/v1/breaches/";
    get_breach: "GET /api/v1/breaches/<query>";
    analyze_breach: "POST /api/v1/market/analyze";
    breach_patterns: "GET /api/v1/analysis/patterns";
    breach_sector: "GET /api/v1/analysis/sector/<sector>";
    export_pdf: "GET /api/v1/export/pdf/<query>";
    intelligence_score: "GET /api/v1/intelligence/score/<query>";
    intelligence_leaderboard: "GET /api/v1/intelligence/leaderboard";
  };
}

export interface ListBreachesResponse {
  breaches: BreachSummary[];
  pagination: Pagination;
}

export interface GetBreachResponse {
  breach: BreachRecord;
}

export interface AnalyzeBreachRequest {
  query: string;
}

export interface CorrelationResult {
  company: Nullable<string>;
  ticker: Nullable<string>;
  breach_date: Nullable<string>;
  breach_type: Nullable<string>;
  records_affected: Nullable<number | string>;
  sector: Nullable<string>;
  severity: Nullable<string>;
  attack_vector: Nullable<string>;
  company_pct_change: number;
  market_pct_change: number;
  relative_impact: number;
  recovery_days: Nullable<number>;
  recovery_text: string;
}

export interface IntelligenceFactor {
  key:
    | "severity"
    | "market_impact"
    | "recovery_speed"
    | "records_affected"
    | "sector_risk";
  label: string;
  score: Nullable<number>;
  weight_pct: number;
  available: boolean;
}

export interface IntelligenceScore {
  overall_score: number;
  grade: "A+" | "A" | "B" | "C" | "D" | "F";
  risk_tier: "Severe" | "High" | "Elevated" | "Moderate" | "Low";
  risk_color: string;
  factors: IntelligenceFactor[];
  summary: string;
  methodology_version: "1.0";
  market_data_used: boolean;
}

export interface AnalyzeBreachFoundResponse {
  found: true;
  result: CorrelationResult;
  analysis: string;
  intelligence: IntelligenceScore;
  pdf_report: Nullable<string>;
}

export interface AnalyzeBreachNotFoundResponse {
  found: false;
  query: string;
  analysis: string;
}

export interface AnalyzeBreachUnavailableResponse {
  found: false;
  error: string;
}

export type AnalyzeBreachResponse =
  | AnalyzeBreachFoundResponse
  | AnalyzeBreachNotFoundResponse
  | AnalyzeBreachUnavailableResponse;

export interface GetIntelligenceScoreResponse {
  found: true;
  company: Nullable<string>;
  ticker: Nullable<string>;
  intelligence: IntelligenceScore;
}

export interface LeaderboardEntry {
  company: Nullable<string>;
  ticker: Nullable<string>;
  sector: Nullable<string>;
  severity: Nullable<string>;
  breach_date: Nullable<string>;
  overall_score: number;
  grade: "A+" | "A" | "B" | "C" | "D" | "F";
  risk_tier: "Severe" | "High" | "Elevated" | "Moderate" | "Low";
  risk_color: string;
}

export interface IntelligenceLeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  total: number;
  limit: number;
  order: "asc" | "desc";
  note: string;
}

export interface BreachPatternsResponse {
  total_breaches: number;
  by_sector: Record<string, number>;
  by_severity: Record<string, number>;
  by_year: Record<string, number>;
}

export interface BreachesBySectorResponse {
  sector: string;
  breaches: Array<
    Pick<BreachSummary, "company" | "ticker" | "breach_date" | "severity">
  >;
  count: number;
}

export interface PdfExportNotImplementedResponse {
  message: "PDF export feature coming soon";
  breach: Nullable<string>;
}

export interface ApiErrorResponse {
  error: string;
  message?: string;
  query?: string;
  suggestion?: string;
}


import axios from "axios";
/**
 * The single, visible HTTP client for the Flask backend.
 * VITE_API_BASE_URL is optional so a deployed frontend can target its backend
 * without changing source code.
 */
const backendBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000";

const api = axios.create({
  baseURL: import.meta.env.DEV ? "/backend" : backendBaseUrl,
  timeout: 30_000,
});

export async function health(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
}

export async function analyzeBreachMarket(query: string): Promise<AnalyzeBreachResponse> {
  const body: AnalyzeBreachRequest = { query };
  const response = await api.post<AnalyzeBreachResponse>("/api/v1/market/analyze", body);
  return response.data;
}

export async function getBreachPatterns(): Promise<BreachPatternsResponse> {
  const response = await api.get<BreachPatternsResponse>("/api/v1/analysis/patterns");
  return response.data;
}
