/**
 * Typed API Client for interacting with the FastAPI backend.
 */
import {
  MarketPulse,
  DecisionRecord,
  PortfolioState,
  DecisionReplayData,
  MemoryRecord,
  ExperimentReport,
  BacktestResult,
  SystemHealth
} from "../types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

export const api = {
  // Market Intelligence
  getMarketPulse: () => fetchJson<MarketPulse>("/market/pulse"),
  getSupportedSymbols: () => fetchJson<{ symbols: any[] }>("/market/symbols"),

  // Asset Overview & Charts
  getAssetOverview: (symbol: string) => fetchJson<any>(`/assets/${symbol}`),
  getAssetChart: (symbol: string, days = 180) => fetchJson<any>(`/assets/${symbol}/chart?days=${days}`),

  // Regime
  getCurrentRegime: (symbol = "SPY") => fetchJson<any>(`/regime/current?symbol=${symbol}`),
  getRegimeTimeline: (symbol = "SPY") => fetchJson<any>(`/regime/timeline?symbol=${symbol}`),

  // News Intelligence
  getNews: (symbol: string, limit = 10) => fetchJson<any>(`/news?symbol=${symbol}&limit=${limit}`),

  // Decisions
  getLatestDecision: (symbol: string) => fetchJson<DecisionRecord>(`/decisions/latest?symbol=${symbol}`),
  analyzeDecision: (symbol: string, lookback = 250, proposedPct = 5.0) =>
    fetchJson<DecisionRecord>("/decisions/analyze", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        lookback_days: lookback,
        proposed_position_pct: proposedPct,
      }),
    }),
  getDebateView: (symbol: string) => fetchJson<any>(`/decisions/debate?symbol=${symbol}`),

  // Portfolio & Risk Guardian
  getPortfolio: () => fetchJson<PortfolioState>("/portfolio"),
  checkRisk: (payload: {
    symbol: string;
    action: string;
    proposed_position_pct: number;
    asset_sector: string;
    asset_volatility_pct: number;
    uncertainty_score: number;
  }) =>
    fetchJson<any>("/portfolio/risk-check", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Contextual Memory & Replay
  getMemories: (symbol?: string) =>
    fetchJson<MemoryRecord[]>(symbol ? `/memory?symbol=${symbol}` : "/memory"),
  getDecisionReplay: (memoryId: string) =>
    fetchJson<DecisionReplayData>(`/memory/replay/${memoryId}`),

  // Research, Backtesting, & Ablations
  runBacktest: (config: any) =>
    fetchJson<BacktestResult>("/backtest", {
      method: "POST",
      body: JSON.stringify(config),
    }),
  getExperimentSuite: (symbol = "SPY", seed = 42) =>
    fetchJson<ExperimentReport>(`/experiments/suite?symbol=${symbol}&seed=${seed}`),

  // System Health
  getSystemHealth: () => fetchJson<SystemHealth>("/system/health"),
};
