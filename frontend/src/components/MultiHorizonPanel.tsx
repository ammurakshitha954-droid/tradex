"use client";

import React from "react";
import { Clock, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";
import { MultiHorizonAnalysis, HorizonSignal } from "../types";

interface MultiHorizonPanelProps {
  horizons: MultiHorizonAnalysis | undefined;
}

export const MultiHorizonPanel: React.FC<MultiHorizonPanelProps> = ({ horizons }) => {
  if (!horizons) return null;

  const renderHorizonCard = (title: string, signal: HorizonSignal) => {
    const isBuy = signal.action === "BUY";
    const isSell = signal.action === "SELL";
    const colorClass = isBuy
      ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
      : isSell
      ? "text-rose-400 border-rose-500/30 bg-rose-500/10"
      : "text-amber-400 border-amber-500/30 bg-amber-500/10";

    return (
      <div className="terminal-card p-4 space-y-3 bg-[#0d131f] border-[#182335]">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-semibold text-xs text-slate-200">{title}</span>
          </div>
          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${colorClass}`}>
            {signal.action} ({(signal.conviction * 100).toFixed(0)}%)
          </span>
        </div>

        <div className="space-y-1.5 text-[11px]">
          <div className="text-slate-400 font-medium">Key Drivers:</div>
          <ul className="space-y-1">
            {signal.drivers.slice(0, 2).map((d, i) => (
              <li key={i} className="text-slate-300 flex items-start space-x-1.5">
                <span className="text-emerald-400 shrink-0">•</span>
                <span>{d}</span>
              </li>
            ))}
          </ul>

          <div className="text-slate-400 font-medium pt-1">Risks & Friction:</div>
          <ul className="space-y-1">
            {signal.risks.slice(0, 1).map((r, i) => (
              <li key={i} className="text-rose-300 flex items-start space-x-1.5">
                <span className="text-rose-400 shrink-0">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  return (
    <div className="terminal-card p-5 bg-[#0a0f17] border-[#192438] space-y-4">
      <div className="flex items-center justify-between border-b border-[#162032] pb-3">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold">
            MULTI-HORIZON REASONING ENGINE
          </span>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="text-slate-400">Agreement Score:</span>
          <span className={`font-bold ${horizons.horizon_agreement ? "text-emerald-400" : "text-amber-400"}`}>
            {(horizons.agreement_score * 100).toFixed(0)}%
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">Strongest:</span>
          <span className="text-blue-400 font-bold">{horizons.strongest_horizon}</span>
        </div>
      </div>

      {/* 3 Horizon Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {renderHorizonCard("Short-Term (1-5 Days)", horizons.short_term)}
        {renderHorizonCard("Medium-Term (2-8 Weeks)", horizons.medium_term)}
        {renderHorizonCard("Long-Term (3-12 Months)", horizons.long_term)}
      </div>

      {/* Conflict & Synthesis Banner */}
      <div className="p-3 rounded bg-[#101726] border border-[#1d2a42] text-xs font-mono flex items-start space-x-2.5">
        {horizons.horizon_agreement ? (
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        )}
        <div className="space-y-0.5">
          <span className="text-slate-200 font-bold">{horizons.conflict_summary}</span>
          <p className="text-slate-400 text-[11px]">{horizons.decision_impact}</p>
        </div>
      </div>
    </div>
  );
};
