"use client";

import React, { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  PauseCircle,
  AlertOctagon,
  ShieldCheck,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  XCircle,
  Layers,
  Percent,
} from "lucide-react";
import { DecisionRecord, DecisionAction } from "../types";

interface DecisionCardProps {
  decision: DecisionRecord | null;
  isLoading: boolean;
  onReanalyze: () => void;
}

export const DecisionCard: React.FC<DecisionCardProps> = ({ decision, isLoading, onReanalyze }) => {
  const [activeTab, setActiveTab] = useState<"why" | "why_not" | "evidence">("why");

  if (!decision && isLoading) {
    return (
      <div className="terminal-card p-6 flex flex-col items-center justify-center min-h-[360px] animate-pulse">
        <div className="w-12 h-12 rounded-full border-2 border-blue-500 border-t-transparent animate-spin mb-3"></div>
        <p className="font-mono text-sm text-slate-300">Synthesizing Multi-Factor Evidence & Council Votes...</p>
        <span className="text-xs text-slate-400 mt-1">GATHER → UNDERSTAND → REGIME → CONFLICT → UNCERTAINTY → RISK GUARDIAN</span>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="terminal-card p-6 text-center text-slate-400">
        <p>No decision data available. Select an asset or trigger analysis.</p>
      </div>
    );
  }

  const act = decision.final_decision;
  const isBuy = act === "BUY";
  const isSell = act === "SELL";
  const isHold = act === "HOLD";
  const isAbstain = act === "NO_TRADE";

  const actionBadge = isBuy
    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 glow-buy"
    : isSell
    ? "bg-rose-500/20 text-rose-300 border-rose-500/40 glow-sell"
    : isHold
    ? "bg-amber-500/20 text-amber-300 border-amber-500/40 glow-hold"
    : "bg-slate-500/20 text-slate-200 border-slate-500/40 glow-abstain";

  const actionIcon = isBuy ? (
    <TrendingUp className="w-5 h-5 text-emerald-400" />
  ) : isSell ? (
    <TrendingDown className="w-5 h-5 text-rose-400" />
  ) : isHold ? (
    <PauseCircle className="w-5 h-5 text-amber-400" />
  ) : (
    <AlertOctagon className="w-5 h-5 text-slate-400" />
  );

  const riskStatus = decision.risk_guardian.decision;
  const riskBadge =
    riskStatus === "APPROVE"
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
      : riskStatus === "REDUCE"
      ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
      : "bg-rose-500/10 text-rose-400 border-rose-500/30";

  return (
    <div className="terminal-card border-[#1f2b40] bg-gradient-to-b from-[#0f1523] to-[#0a0e18] shadow-2xl p-6 rounded-lg space-y-6">
      {/* Header: Symbol, Decision, Risk Guardian Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#1b2537] pb-4">
        <div className="flex items-center space-x-3">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-black tracking-tight text-white">{decision.symbol}</span>
              <span className="text-sm font-mono text-slate-400">${decision.current_price.toFixed(2)}</span>
            </div>
            <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-2 mt-0.5">
              <span>REGIME: {decision.market_regime}</span>
              <span>•</span>
              <span>MODEL: {decision.model_version}</span>
            </div>
          </div>
        </div>

        {/* Big Action Badge */}
        <div className="flex items-center space-x-3">
          <div className={`px-4 py-2 rounded-md border flex items-center space-x-2.5 font-black text-lg tracking-wider ${actionBadge}`}>
            {actionIcon}
            <span>{decision.final_decision}</span>
          </div>

          {/* Risk Guardian Badge */}
          <div className={`px-3 py-1.5 rounded border text-xs font-mono flex items-center space-x-1.5 ${riskBadge}`}>
            {riskStatus === "APPROVE" ? (
              <ShieldCheck className="w-4 h-4" />
            ) : (
              <ShieldAlert className="w-4 h-4" />
            )}
            <span>RISK GUARDIAN: {riskStatus}</span>
          </div>
        </div>
      </div>

      {/* Metrics Row: Confidence, Uncertainty, Allocation, Horizon consensus */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3 rounded bg-[#121927] border border-[#1b263b]">
          <div className="text-slate-400 text-[10px] uppercase">Calibrated Confidence</div>
          <div className="text-xl font-bold text-blue-400 mt-1">
            {(decision.calibrated_confidence * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-blue-500 h-full rounded-full"
              style={{ width: `${decision.calibrated_confidence * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="p-3 rounded bg-[#121927] border border-[#1b263b]">
          <div className="text-slate-400 text-[10px] uppercase">Composite Uncertainty</div>
          <div className="text-xl font-bold text-amber-400 mt-1">
            {(decision.composite_uncertainty * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-amber-500 h-full rounded-full"
              style={{ width: `${decision.composite_uncertainty * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="p-3 rounded bg-[#121927] border border-[#1b263b]">
          <div className="text-slate-400 text-[10px] uppercase">Approved Allocation</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            {decision.approved_position_pct.toFixed(1)}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Expected Return: {decision.expected_return_pct > 0 ? "+" : ""}
            {decision.expected_return_pct.toFixed(1)}%
          </div>
        </div>

        <div className="p-3 rounded bg-[#121927] border border-[#1b263b]">
          <div className="text-slate-400 text-[10px] uppercase">Council Consensus</div>
          <div className="text-sm font-bold text-slate-200 mt-1">
            {decision.council.consensus_signal} ({decision.conflict.conflict_severity} conflict)
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Agreement: {(decision.conflict.agreement_score * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Tabs: WHY THIS DECISION vs WHY NOT */}
      <div className="space-y-3">
        <div className="flex border-b border-[#1b263b] text-xs font-mono">
          <button
            onClick={() => setActiveTab("why")}
            className={`pb-2 px-3 border-b-2 font-semibold transition-all ${
              activeTab === "why"
                ? "border-emerald-500 text-emerald-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            WHY THIS DECISION? (DOMINANT EVIDENCE)
          </button>
          <button
            onClick={() => setActiveTab("why_not")}
            className={`pb-2 px-3 border-b-2 font-semibold transition-all ${
              activeTab === "why_not"
                ? "border-rose-500 text-rose-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            WHY NOT? (CONFLICTS & ABSTENTION REASONS)
          </button>
          <button
            onClick={() => setActiveTab("evidence")}
            className={`pb-2 px-3 border-b-2 font-semibold transition-all ${
              activeTab === "evidence"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            MULTI-HORIZON & MACRO SYNTHESIS
          </button>
        </div>

        {/* Tab 1: WHY THIS DECISION */}
        {activeTab === "why" && (
          <div className="p-4 rounded bg-[#0b101a] border border-[#172236] space-y-2.5">
            <div className="text-xs font-semibold text-slate-200">
              Primary Evidence Synthesis:
            </div>
            <ul className="space-y-2">
              {decision.explanation.why_this_decision.map((point, i) => (
                <li key={i} className="flex items-start space-x-2 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Tab 2: WHY NOT */}
        {activeTab === "why_not" && (
          <div className="p-4 rounded bg-[#130b10] border border-[#301622] space-y-2.5">
            <div className="text-xs font-semibold text-rose-300">
              Downside Risks, Model Disagreements & Abstention Triggers:
            </div>
            <ul className="space-y-2">
              {decision.explanation.why_not.map((point, i) => (
                <li key={i} className="flex items-start space-x-2 text-xs text-rose-200/90">
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
            {isAbstain && (
              <div className="mt-3 p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 font-mono">
                <strong>ABSTENTION ACTIVE:</strong> Capital preserved. Avoiding uncalibrated risk
                is prioritized over forced market exposure.
              </div>
            )}
          </div>
        )}

        {/* Tab 3: HORIZON & MACRO SYNTHESIS */}
        {activeTab === "evidence" && (
          <div className="p-4 rounded bg-[#0b101a] border border-[#172236] space-y-3 text-xs">
            <div>
              <span className="font-semibold text-slate-200">Time-Horizon Tension:</span>
              <p className="text-slate-300 mt-0.5">{decision.explanation.horizon_tension_analysis}</p>
            </div>
            <div>
              <span className="font-semibold text-slate-200">Macro Regime Mandate:</span>
              <p className="text-slate-300 mt-0.5">{decision.explanation.macro_regime_implication}</p>
            </div>
            <div>
              <span className="font-semibold text-slate-200">Risk Governance Ruling:</span>
              <p className="text-slate-300 mt-0.5">{decision.explanation.risk_governance_takeaway}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
