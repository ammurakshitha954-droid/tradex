"use client";

import React from "react";
import {
  Globe,
  Activity,
  BarChart3,
  Newspaper,
  Split,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import { DecisionRecord } from "../types";

interface MarketBrainProps {
  decision: DecisionRecord | null;
}

export const MarketBrain: React.FC<MarketBrainProps> = ({ decision }) => {
  if (!decision) return null;

  const regime = decision.market_regime;
  const isConflictHigh = decision.conflict.conflict_severity === "HIGH" || decision.conflict.conflict_severity === "EXTREME";
  const riskStatus = decision.risk_guardian.decision;

  return (
    <div className="terminal-card p-6 bg-[#090d16] border-[#18233a] space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200 font-bold">
            MARKET BRAIN // EVIDENCE PROPAGATION GRAPH
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          Traceable Pipeline: Data → Quantitative Features → Reasoning Council → Risk Control
        </span>
      </div>

      {/* Visual Flow Stages */}
      <div className="grid grid-cols-1 md:grid-cols-7 gap-2 items-center text-center font-mono">
        {/* Stage 1: Market Data */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-blue-400">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">1. Raw Market</div>
            <div className="text-xs font-bold text-slate-200">{decision.symbol}</div>
            <div className="text-[10px] text-slate-400">${decision.current_price.toFixed(2)}</div>
          </div>
          <div className="text-[9px] text-emerald-400 bg-emerald-500/10 rounded py-0.5">
            VERIFIED TICK
          </div>
        </div>

        {/* Stage 2: Regime */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-indigo-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">2. Regime</div>
            <div className="text-[11px] font-bold text-indigo-300 truncate">{regime}</div>
            <div className="text-[10px] text-slate-400">{(decision.regime_confidence * 100).toFixed(0)}% Conf</div>
          </div>
          <div className="text-[9px] text-indigo-300 bg-indigo-500/10 rounded py-0.5">
            PROBABILITY MAP
          </div>
        </div>

        {/* Stage 3: Technical Signals */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-emerald-400">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">3. Quantitative</div>
            <div className="text-[11px] font-bold text-emerald-300">
              {decision.council.votes[0]?.signal || "BUY"}
            </div>
            <div className="text-[10px] text-slate-400">RSI & Momentum</div>
          </div>
          <div className="text-[9px] text-emerald-300 bg-emerald-500/10 rounded py-0.5">
            DETERMINISTIC
          </div>
        </div>

        {/* Stage 4: News & Events */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-purple-400">
            <Newspaper className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">4. News Intel</div>
            <div className="text-[11px] font-bold text-purple-300">
              {decision.council.votes[4]?.signal || "HOLD"}
            </div>
            <div className="text-[10px] text-slate-400">Materiality Guard</div>
          </div>
          <div className="text-[9px] text-purple-300 bg-purple-500/10 rounded py-0.5">
            PROMPT-SAFE
          </div>
        </div>

        {/* Stage 5: Evidence Conflict */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-amber-400">
            <Split className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">5. Conflict</div>
            <div className={`text-[11px] font-bold ${isConflictHigh ? "text-rose-400" : "text-emerald-400"}`}>
              {decision.conflict.conflict_severity}
            </div>
            <div className="text-[10px] text-slate-400">
              {(decision.conflict.disagreement_score * 100).toFixed(0)}% Divergence
            </div>
          </div>
          <div className="text-[9px] text-amber-300 bg-amber-500/10 rounded py-0.5">
            ENTROPY SENSING
          </div>
        </div>

        {/* Stage 6: AI Conviction */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-blue-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">6. Decision</div>
            <div className="text-xs font-bold text-white">{decision.final_decision}</div>
            <div className="text-[10px] text-blue-400">
              {(decision.calibrated_confidence * 100).toFixed(0)}% Conf
            </div>
          </div>
          <div className="text-[9px] text-blue-300 bg-blue-500/10 rounded py-0.5">
            CALIBRATED
          </div>
        </div>

        {/* Stage 7: Risk Guardian Control */}
        <div className="p-3 rounded bg-[#0f1626] border border-[#1d2a45] space-y-1.5 min-h-[140px] flex flex-col justify-between">
          <div className="flex items-center justify-center text-indigo-400">
            {riskStatus === "APPROVE" ? (
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            ) : (
              <ShieldAlert className="w-5 h-5 text-amber-400" />
            )}
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase">7. Risk Guardian</div>
            <div className={`text-xs font-bold ${riskStatus === "APPROVE" ? "text-emerald-400" : "text-amber-400"}`}>
              {riskStatus}
            </div>
            <div className="text-[10px] text-slate-400">{decision.approved_position_pct}% Alloc</div>
          </div>
          <div className="text-[9px] text-indigo-300 bg-indigo-500/10 rounded py-0.5">
            HARD VETO
          </div>
        </div>
      </div>

      {/* Narrative Synthesis */}
      <div className="p-4 rounded bg-[#0c121d] border border-[#1b263b] text-xs font-mono space-y-1.5">
        <div className="text-slate-400 font-semibold uppercase text-[10px]">
          ACTIVE PIPELINE SYNTHESIS:
        </div>
        <p className="text-slate-200 leading-relaxed">
          {decision.explanation.summary}
        </p>
      </div>
    </div>
  );
};
