"use client";

import React, { useState, useEffect } from "react";
import { FlaskConical, Play, CheckCircle2, TrendingUp, Info } from "lucide-react";
import { ExperimentReport, BaselineMetricRow } from "../types";
import { api } from "../lib/api";

export const ExperimentsWorkspace: React.FC = () => {
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [symbol, setSymbol] = useState("SPY");
  const [seed, setSeed] = useState(42);

  const fetchSuite = () => {
    setLoading(true);
    api
      .getExperimentSuite(symbol, seed)
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchSuite();
  }, [symbol, seed]);

  return (
    <div className="terminal-card p-6 bg-[#0a0f18] border-[#182338] space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <FlaskConical className="w-5 h-5 text-purple-400" />
          <span className="text-sm font-mono uppercase tracking-wider text-slate-100 font-bold">
            RESEARCH EXPERIMENTS: BASELINES & ABLATION STUDY
          </span>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="text-slate-400">Benchmark Asset:</span>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="p-1 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          >
            <option value="SPY">SPY (Broad S&P 500)</option>
            <option value="QQQ">QQQ (Nasdaq 100)</option>
            <option value="AAPL">AAPL</option>
            <option value="NVDA">NVDA</option>
          </select>
          <button
            onClick={fetchSuite}
            disabled={loading}
            className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-500 font-bold text-white text-xs"
          >
            {loading ? "RUNNING..." : "RE-RUN"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-slate-400 animate-pulse">
          Computing reproducible statistical matrix across 8 baselines and 8 ablation steps...
        </div>
      ) : report ? (
        <div className="space-y-6 font-mono text-xs">
          {/* Research Conclusion Banner */}
          <div className="p-4 rounded bg-[#101726] border border-[#1f2e4a] text-slate-200 space-y-1">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold">
              <CheckCircle2 className="w-4 h-4" />
              <span>PRIMARY RESEARCH FINDING & DEFENSE:</span>
            </div>
            <p className="text-[11px] leading-relaxed text-slate-300">
              {report.research_conclusion}
            </p>
          </div>

          {/* Table 1: Ablation Study (A through H) */}
          <div className="space-y-2">
            <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
              <span>ABLATION STUDY (INCREMENTAL ARCHITECTURAL EVALUATION)</span>
              <span className="text-[10px] text-slate-400">Progression from A (Minimal) to H (Full Adaptive)</span>
            </div>

            <div className="overflow-x-auto rounded border border-[#18253b] bg-[#0c121e]">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase bg-[#090d16]">
                    <th className="py-2.5 px-3">Ablation Step</th>
                    <th className="py-2.5 px-3">Sharpe</th>
                    <th className="py-2.5 px-3">Annual Ret</th>
                    <th className="py-2.5 px-3">Vol</th>
                    <th className="py-2.5 px-3">Max DD</th>
                    <th className="py-2.5 px-3">Win %</th>
                    <th className="py-2.5 px-3">Trades (Abstain)</th>
                    <th className="py-2.5 px-3">Marginal Insight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {report.ablations.map((row: BaselineMetricRow, idx: number) => {
                    const isFull = idx === report.ablations.length - 1;
                    return (
                      <tr
                        key={idx}
                        className={`hover:bg-[#11192a] transition-colors ${
                          isFull ? "bg-emerald-500/10 font-bold text-white" : "text-slate-300"
                        }`}
                      >
                        <td className="py-2 px-3 text-white font-medium">{row.name}</td>
                        <td className="py-2 px-3 text-emerald-400 font-bold">{row.sharpe_ratio}</td>
                        <td className="py-2 px-3 text-blue-400">{row.annualized_return_pct}%</td>
                        <td className="py-2 px-3 text-purple-400">{row.annualized_volatility_pct}%</td>
                        <td className="py-2 px-3 text-rose-400">{row.max_drawdown_pct}%</td>
                        <td className="py-2 px-3">{row.win_rate_pct}%</td>
                        <td className="py-2 px-3 text-slate-400">
                          {row.total_trades} ({row.abstentions_count})
                        </td>
                        <td className="py-2 px-3 text-[10px] text-slate-400 max-w-xs truncate">
                          {row.marginal_contribution_note}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Table 2: Baseline Benchmark Strategies (1 to 8) */}
          <div className="space-y-2">
            <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center justify-between">
              <span>BENCHMARK BASELINE COMPARISONS (8 STRATEGIES)</span>
              <span className="text-[10px] text-slate-400">Identical 10 bps friction & 5 bps slippage</span>
            </div>

            <div className="overflow-x-auto rounded border border-[#18253b] bg-[#0c121e]">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase bg-[#090d16]">
                    <th className="py-2.5 px-3">Strategy</th>
                    <th className="py-2.5 px-3">Sharpe</th>
                    <th className="py-2.5 px-3">Annual Ret</th>
                    <th className="py-2.5 px-3">Vol</th>
                    <th className="py-2.5 px-3">Max DD</th>
                    <th className="py-2.5 px-3">Profit Factor</th>
                    <th className="py-2.5 px-3">Qualitative Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {report.baselines.map((row: BaselineMetricRow, idx: number) => {
                    const isProposed = row.name.includes("Full Proposed");
                    return (
                      <tr
                        key={idx}
                        className={`hover:bg-[#11192a] transition-colors ${
                          isProposed ? "bg-blue-600/15 font-bold text-white" : "text-slate-300"
                        }`}
                      >
                        <td className="py-2 px-3 font-medium text-white">{row.name}</td>
                        <td className="py-2 px-3 text-emerald-400 font-bold">{row.sharpe_ratio}</td>
                        <td className="py-2 px-3 text-blue-400">{row.annualized_return_pct}%</td>
                        <td className="py-2 px-3 text-purple-400">{row.annualized_volatility_pct}%</td>
                        <td className="py-2 px-3 text-rose-400">{row.max_drawdown_pct}%</td>
                        <td className="py-2 px-3 text-slate-200">{row.profit_factor}</td>
                        <td className="py-2 px-3 text-[10px] text-slate-400 max-w-sm truncate">
                          {row.marginal_contribution_note}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
