"use client";

import React, { useState } from "react";
import { Activity, Play, TrendingUp, AlertTriangle, Layers, ArrowRight } from "lucide-react";
import { BacktestResult } from "../types";
import { api } from "../lib/api";

export const BacktestWorkspace: React.FC = () => {
  const [symbol, setSymbol] = useState("SPY");
  const [strategy, setStrategy] = useState("full_adaptive");
  const [capital, setCapital] = useState(100000);
  const [txCostBps, setTxCostBps] = useState(10.0);
  const [slippageBps, setSlippageBps] = useState(5.0);
  const [useAbstention, setUseAbstention] = useState(true);
  const [maxPosPct, setMaxPosPct] = useState(10.0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.runBacktest({
        symbol,
        strategy,
        initial_capital: Number(capital),
        transaction_cost_bps: Number(txCostBps),
        slippage_bps: Number(slippageBps),
        max_position_size_pct: Number(maxPosPct),
        use_abstention: useAbstention,
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="terminal-card p-6 bg-[#0a0f18] border-[#182338] space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-mono uppercase tracking-wider text-slate-100 font-bold">
            STRATEGY BACKTESTING & WALK-FORWARD LAB
          </span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Realistic Execution Friction: Slippage + Commissions + 70/30 In-Sample Split
        </span>
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleRun} className="grid grid-cols-2 md:grid-cols-7 gap-3 text-xs font-mono items-end">
        <div>
          <label className="text-[10px] text-slate-400 uppercase">Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full mt-1 p-2 rounded bg-[#0d1422] border border-[#1b273c] text-white font-bold"
          />
        </div>

        <div>
          <label className="text-[10px] text-slate-400 uppercase">Strategy</label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="w-full mt-1 p-2 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          >
            <option value="full_adaptive">Full Proposed System</option>
            <option value="buy_and_hold">Buy & Hold</option>
            <option value="dual_sma">Dual SMA (20/50)</option>
            <option value="rsi_macd">RSI + MACD</option>
            <option value="ml_random_forest">Random Forest ML</option>
          </select>
        </div>

        <div>
          <label className="text-[10px] text-slate-400 uppercase">Capital ($)</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(Number(e.target.value))}
            className="w-full mt-1 p-2 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          />
        </div>

        <div>
          <label className="text-[10px] text-slate-400 uppercase">Cost (BPS)</label>
          <input
            type="number"
            step="1"
            value={txCostBps}
            onChange={(e) => setTxCostBps(Number(e.target.value))}
            className="w-full mt-1 p-2 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          />
        </div>

        <div>
          <label className="text-[10px] text-slate-400 uppercase">Slippage (BPS)</label>
          <input
            type="number"
            step="1"
            value={slippageBps}
            onChange={(e) => setSlippageBps(Number(e.target.value))}
            className="w-full mt-1 p-2 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          />
        </div>

        <div className="flex items-center space-x-2 pb-2">
          <input
            type="checkbox"
            id="abstain-toggle"
            checked={useAbstention}
            onChange={(e) => setUseAbstention(e.target.checked)}
            className="rounded bg-slate-900 border-slate-700"
          />
          <label htmlFor="abstain-toggle" className="text-[11px] text-slate-300 select-none">
            Abstention
          </label>
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full p-2 rounded bg-blue-600 hover:bg-blue-500 font-bold text-white text-xs flex items-center justify-center space-x-1.5 transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>RUN SIMULATION</span>
          </button>
        </div>
      </form>

      {/* Backtest Results */}
      {result && (
        <div className="space-y-5 font-mono text-xs">
          {/* Key Metrics Row */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
            <div className="p-3 rounded bg-[#0d1524] border border-[#1b2a45]">
              <div className="text-slate-400 text-[10px] uppercase">Final Equity</div>
              <div className="text-base font-bold text-emerald-400 mt-1">
                ${result.final_equity.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-400">
                {result.total_return_pct > 0 ? "+" : ""}
                {result.total_return_pct.toFixed(1)}% Return
              </div>
            </div>

            <div className="p-3 rounded bg-[#0d1524] border border-[#1b2a45]">
              <div className="text-slate-400 text-[10px] uppercase">Sharpe Ratio</div>
              <div className="text-base font-bold text-blue-400 mt-1">
                {result.sharpe_ratio.toFixed(2)}
              </div>
              <div className="text-[10px] text-slate-400">
                Sortino: {result.sortino_ratio.toFixed(2)}
              </div>
            </div>

            <div className="p-3 rounded bg-[#0d1524] border border-[#1b2a45]">
              <div className="text-slate-400 text-[10px] uppercase">Max Drawdown</div>
              <div className="text-base font-bold text-rose-400 mt-1">
                {result.max_drawdown_pct.toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-400">
                Calmar: {result.calmar_ratio.toFixed(2)}
              </div>
            </div>

            <div className="p-3 rounded bg-[#0d1524] border border-[#1b2a45]">
              <div className="text-slate-400 text-[10px] uppercase">Win Rate & Trades</div>
              <div className="text-base font-bold text-slate-200 mt-1">
                {result.win_rate_pct.toFixed(0)}%
              </div>
              <div className="text-[10px] text-slate-400">
                {result.total_trades} trades / PF: {result.profit_factor.toFixed(2)}
              </div>
            </div>

            <div className="p-3 rounded bg-[#0d1524] border border-[#1b2a45]">
              <div className="text-slate-400 text-[10px] uppercase">Abstentions</div>
              <div className="text-base font-bold text-amber-400 mt-1">
                {result.abstentions_count}
              </div>
              <div className="text-[10px] text-slate-400">Trades avoided</div>
            </div>

            <div className="p-3 rounded bg-[#0d1524] border border-[#1b2a45]">
              <div className="text-slate-400 text-[10px] uppercase">In/Out Sample Sharpe</div>
              <div className="text-base font-bold text-purple-400 mt-1">
                {result.in_sample_sharpe.toFixed(2)} / {result.out_of_sample_sharpe.toFixed(2)}
              </div>
              <div className="text-[10px] text-slate-400">IS vs OOS stability</div>
            </div>
          </div>

          {/* Equity Curve Table / Progression */}
          <div className="p-4 rounded bg-[#0d1422] border border-[#1a263c] space-y-3">
            <div className="flex items-center justify-between text-xs font-bold text-slate-200">
              <span>EQUITY CURVE PROGRESSION & REGIME MARKERS</span>
              <span className="text-[10px] text-slate-400">
                Friction paid: ${result.total_costs_paid.toFixed(2)}
              </span>
            </div>

            <div className="max-h-60 overflow-y-auto font-mono text-[11px]">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                    <th className="pb-1.5">Date</th>
                    <th className="pb-1.5">Equity</th>
                    <th className="pb-1.5">Drawdown</th>
                    <th className="pb-1.5">Price</th>
                    <th className="pb-1.5 text-right">Regime</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {result.equity_curve.map((pt, i) => (
                    <tr key={i} className="hover:bg-slate-800/20">
                      <td className="py-1 text-slate-300">{pt.date}</td>
                      <td className="py-1 font-bold text-emerald-400">${pt.equity.toLocaleString()}</td>
                      <td className="py-1 text-rose-400">{pt.drawdown_pct}%</td>
                      <td className="py-1 text-slate-400">${pt.benchmark_price}</td>
                      <td className="py-1 text-right text-purple-400">{pt.regime}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
