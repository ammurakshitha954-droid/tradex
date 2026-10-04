"use client";

import React, { useState } from "react";
import {
  Briefcase,
  ShieldCheck,
  ShieldAlert,
  PieChart as PieIcon,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Play,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { PortfolioState, PortfolioPosition, RiskGuardianDecision } from "../types";
import { api } from "../lib/api";

interface PortfolioPanelProps {
  portfolio: PortfolioState | null;
  onRefreshPortfolio: () => void;
}

export const PortfolioPanel: React.FC<PortfolioPanelProps> = ({ portfolio, onRefreshPortfolio }) => {
  const [testSymbol, setTestSymbol] = useState("NVDA");
  const [testAction, setTestAction] = useState("BUY");
  const [testSize, setTestSize] = useState(6.0);
  const [testSector, setTestSector] = useState("Technology");
  const [testVol, setTestVol] = useState(28.0);
  const [testUncertainty, setTestUncertainty] = useState(0.30);
  const [simResult, setSimResult] = useState<RiskGuardianDecision | null>(null);
  const [simLoading, setSimLoading] = useState(false);

  if (!portfolio) {
    return (
      <div className="terminal-card p-6 text-center text-xs font-mono text-slate-400">
        Loading portfolio analytics...
      </div>
    );
  }

  const handleTestRiskGuardian = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimLoading(true);
    try {
      const res = await api.checkRisk({
        symbol: testSymbol,
        action: testAction,
        proposed_position_pct: Number(testSize),
        asset_sector: testSector,
        asset_volatility_pct: Number(testVol),
        uncertainty_score: Number(testUncertainty),
      });
      setSimResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setSimLoading(false);
    }
  };

  const isHhiHigh = portfolio.hhi_concentration_index > 2500;

  return (
    <div className="space-y-6">
      {/* Top Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
        <div className="terminal-card p-4 bg-[#0a0f18] border-[#182338]">
          <div className="text-slate-400 text-[10px] uppercase">Total Portfolio Equity</div>
          <div className="text-xl font-bold text-white mt-1">
            ${portfolio.total_equity.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Cash: ${portfolio.cash.toLocaleString()} (
            {((portfolio.cash / portfolio.total_equity) * 100).toFixed(1)}%)
          </div>
        </div>

        <div className="terminal-card p-4 bg-[#0a0f18] border-[#182338]">
          <div className="text-slate-400 text-[10px] uppercase">Annualized Volatility</div>
          <div className="text-xl font-bold text-purple-400 mt-1">
            {portfolio.portfolio_volatility_annualized.toFixed(1)}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            1-Day 95% CVaR: {portfolio.portfolio_cvar_95.toFixed(2)}%
          </div>
        </div>

        <div className="terminal-card p-4 bg-[#0a0f18] border-[#182338]">
          <div className="text-slate-400 text-[10px] uppercase">Concentration (HHI)</div>
          <div className={`text-xl font-bold mt-1 ${isHhiHigh ? "text-amber-400" : "text-emerald-400"}`}>
            {portfolio.hhi_concentration_index.toFixed(0)}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Top 3 Assets: {portfolio.top_3_concentration_pct.toFixed(1)}%
          </div>
        </div>

        <div className="terminal-card p-4 bg-[#0a0f18] border-[#182338]">
          <div className="text-slate-400 text-[10px] uppercase">Current Drawdown</div>
          <div className="text-xl font-bold text-rose-400 mt-1">
            {portfolio.current_drawdown_pct.toFixed(2)}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Peak: ${portfolio.peak_equity.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Holdings & Sector Exposures */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Holdings Table */}
        <div className="lg:col-span-2 terminal-card p-5 bg-[#0a0f18] border-[#182338] space-y-4">
          <div className="flex items-center justify-between border-b border-[#162133] pb-3">
            <div className="flex items-center space-x-2">
              <Briefcase className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-mono uppercase tracking-wider text-slate-200 font-bold">
                PORTFOLIO HOLDINGS & EXPOSURES
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              {portfolio.positions.length} Active Positions
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                  <th className="pb-2">Asset</th>
                  <th className="pb-2">Sector</th>
                  <th className="pb-2">Shares</th>
                  <th className="pb-2">Price</th>
                  <th className="pb-2">Market Val</th>
                  <th className="pb-2">Weight</th>
                  <th className="pb-2 text-right">PnL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {portfolio.positions.map((pos: PortfolioPosition) => {
                  const isUp = pos.unrealized_pnl_pct >= 0;
                  return (
                    <tr key={pos.symbol} className="hover:bg-[#101726] transition-colors">
                      <td className="py-2.5 font-bold text-white">{pos.symbol}</td>
                      <td className="py-2.5 text-slate-400 text-[11px]">{pos.sector}</td>
                      <td className="py-2.5 text-slate-300">{pos.shares}</td>
                      <td className="py-2.5 text-slate-300">${pos.current_price.toFixed(2)}</td>
                      <td className="py-2.5 text-slate-200 font-medium">${pos.market_value.toLocaleString()}</td>
                      <td className="py-2.5 text-blue-400">{pos.weight_pct}%</td>
                      <td className={`py-2.5 text-right font-medium ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                        {isUp ? "+" : ""}{pos.unrealized_pnl_pct.toFixed(2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sector Exposure Breakdown */}
        <div className="terminal-card p-5 bg-[#0a0f18] border-[#182338] space-y-4">
          <div className="flex items-center space-x-2 border-b border-[#162133] pb-3">
            <PieIcon className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-mono uppercase tracking-wider text-slate-200 font-bold">
              SECTOR CONCENTRATION
            </span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {Object.entries(portfolio.sector_exposures).map(([sector, pct]) => {
              const isOverLimit = pct > 25.0; // 25% limit
              return (
                <div key={sector} className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-300">{sector}</span>
                    <span className={isOverLimit ? "text-rose-400 font-bold" : "text-slate-400"}>
                      {pct.toFixed(1)}% {isOverLimit && "(LIMIT > 25%)"}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${isOverLimit ? "bg-rose-500" : "bg-purple-500"}`}
                      style={{ width: `${Math.min(100, pct * 2.5)}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-3 rounded bg-[#0f1522] border border-[#1b263b] text-[11px] font-mono text-slate-400">
            <strong>Risk Rule:</strong> Single sector exposure capped at 25.0%. Excess allocation
            automatically triggers Risk Guardian REDUCE or REJECT.
          </div>
        </div>
      </div>

      {/* Interactive Risk Guardian Simulator */}
      <div className="terminal-card p-5 bg-[#0a0f18] border-[#182338] space-y-4 font-mono text-xs">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#162133] pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            <span className="text-xs uppercase tracking-wider text-slate-200 font-bold">
              INDEPENDENT RISK GUARDIAN AUDIT BENCH
            </span>
          </div>
          <span className="text-[11px] text-slate-400">
            Hard boundaries: Single Position ≤ 10%, Sector ≤ 25%, Drawdown Circuit Breaker ≤ 15%
          </span>
        </div>

        <form onSubmit={handleTestRiskGuardian} className="grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
          <div>
            <label className="text-[10px] text-slate-400 uppercase">Symbol</label>
            <input
              type="text"
              value={testSymbol}
              onChange={(e) => setTestSymbol(e.target.value.toUpperCase())}
              className="w-full mt-1 p-2 rounded bg-[#0e1420] border border-[#1d273a] text-white text-xs font-bold"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase">Action</label>
            <select
              value={testAction}
              onChange={(e) => setTestAction(e.target.value)}
              className="w-full mt-1 p-2 rounded bg-[#0e1420] border border-[#1d273a] text-white text-xs"
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
              <option value="HOLD">HOLD</option>
              <option value="NO_TRADE">NO_TRADE</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase">Proposed Size %</label>
            <input
              type="number"
              step="0.5"
              value={testSize}
              onChange={(e) => setTestSize(Number(e.target.value))}
              className="w-full mt-1 p-2 rounded bg-[#0e1420] border border-[#1d273a] text-white text-xs"
            />
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase">Sector</label>
            <select
              value={testSector}
              onChange={(e) => setTestSector(e.target.value)}
              className="w-full mt-1 p-2 rounded bg-[#0e1420] border border-[#1d273a] text-white text-xs"
            >
              <option value="Technology">Technology</option>
              <option value="Financial">Financial</option>
              <option value="Consumer Cyclical">Consumer Cyclical</option>
              <option value="Communication Services">Communication</option>
              <option value="Broad Market">Broad Market</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase">Asset Volatility %</label>
            <input
              type="number"
              value={testVol}
              onChange={(e) => setTestVol(Number(e.target.value))}
              className="w-full mt-1 p-2 rounded bg-[#0e1420] border border-[#1d273a] text-white text-xs"
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={simLoading}
              className="w-full p-2 rounded bg-indigo-600 hover:bg-indigo-500 font-bold text-white text-xs flex items-center justify-center space-x-1 transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>TEST RISK</span>
            </button>
          </div>
        </form>

        {/* Simulation Output Card */}
        {simResult && (
          <div
            className={`p-4 rounded border text-xs ${
              simResult.decision === "APPROVE"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : simResult.decision === "REDUCE"
                ? "bg-amber-500/10 border-amber-500/30 text-amber-300"
                : "bg-rose-500/10 border-rose-500/30 text-rose-300"
            }`}
          >
            <div className="flex items-center justify-between font-bold text-sm">
              <div className="flex items-center space-x-2">
                {simResult.decision === "APPROVE" ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-5 h-5 text-rose-400" />
                )}
                <span>
                  RISK GUARDIAN RULING: {simResult.decision} ({simResult.approved_position_pct}%
                  Approved)
                </span>
              </div>
              <span>Risk Score: {simResult.risk_score}/100</span>
            </div>
            <p className="mt-2 text-slate-200">{simResult.explanation}</p>
            {simResult.binding_constraints.length > 0 && (
              <ul className="mt-2 space-y-1 list-disc list-inside text-[11px] text-slate-300">
                {simResult.binding_constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
