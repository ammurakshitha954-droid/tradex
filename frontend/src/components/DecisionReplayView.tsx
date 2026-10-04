"use client";

import React, { useState, useEffect } from "react";
import {
  PlayCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { DecisionReplayData, MemoryRecord } from "../types";
import { api } from "../lib/api";

export const DecisionReplayView: React.FC = () => {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [replayData, setReplayData] = useState<DecisionReplayData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api
      .getMemories()
      .then((data) => {
        setMemories(data);
        if (data.length > 0) {
          setSelectedId(data[0].id);
          fetchReplay(data[0].id);
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const fetchReplay = (id: string) => {
    setLoading(true);
    api
      .getDecisionReplay(id)
      .then((data) => {
        setReplayData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  const handleSelect = (id: string) => {
    setSelectedId(id);
    fetchReplay(id);
  };

  const getQualityBadge = (label: string) => {
    if (label.includes("GOOD_DECISION_GOOD_OUTCOME")) {
      return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
    }
    if (label.includes("GOOD_DECISION_BAD_OUTCOME")) {
      return "bg-blue-500/15 text-blue-300 border-blue-500/30";
    }
    if (label.includes("BAD_DECISION_GOOD_OUTCOME")) {
      return "bg-amber-500/15 text-amber-300 border-amber-500/30";
    }
    return "bg-rose-500/15 text-rose-300 border-rose-500/30";
  };

  return (
    <div className="terminal-card p-6 bg-[#090e18] border-[#18233a] space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-4">
        <div className="flex items-center space-x-2">
          <PlayCircle className="w-5 h-5 text-emerald-400" />
          <span className="text-sm font-mono uppercase tracking-wider text-slate-100 font-bold">
            HISTORICAL DECISION REPLAY & ATTRIBUTION BENCH
          </span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Evaluates Process Integrity vs Outcome Luck & Validated Learning
        </span>
      </div>

      {/* Memory Record Selector Chips */}
      <div className="space-y-1.5 font-mono">
        <div className="text-[11px] text-slate-400 font-semibold uppercase">
          Select Historical Decision Event:
        </div>
        <div className="flex flex-wrap gap-2">
          {memories.map((m) => {
            const isSelected = m.id === selectedId;
            return (
              <button
                key={m.id}
                onClick={() => handleSelect(m.id)}
                className={`px-3 py-1.5 rounded text-xs transition-all border ${
                  isSelected
                    ? "bg-blue-600/25 border-blue-500 text-blue-300 font-bold"
                    : "bg-[#0f1524] border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>{m.symbol}</span>
                <span className="ml-1 text-[10px] text-slate-500">[{m.decision}]</span>
                <span className="ml-1 text-[10px] text-slate-400">
                  {new Date(m.timestamp).toLocaleDateString()}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-slate-400 animate-pulse">
          Loading Historical Contextual Decision Frame...
        </div>
      ) : replayData ? (
        <div className="space-y-5 font-mono text-xs">
          {/* Section 1 & 2: WHAT AI KNEW THEN vs WHAT AI DECIDED */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 1. What AI Knew Then */}
            <div className="p-4 rounded bg-[#0d1422] border border-[#1b283f] space-y-2.5">
              <div className="text-xs font-bold text-slate-200 flex items-center space-x-1.5 text-blue-400">
                <Clock className="w-4 h-4" />
                <span>1. WHAT AI KNEW THEN</span>
              </div>
              <div className="space-y-1 text-[11px] text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-400">Timestamp:</span>
                  <span>{new Date(replayData.decision_timestamp).toUTCString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Market Regime:</span>
                  <span className="text-purple-400 font-bold">
                    {replayData.what_ai_knew_then.market_regime}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Calibrated Confidence:</span>
                  <span className="text-blue-400 font-bold">
                    {(replayData.what_ai_knew_then.calibrated_confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Composite Uncertainty:</span>
                  <span className="text-amber-400 font-bold">
                    {(replayData.what_ai_knew_then.composite_uncertainty * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk Guardian Evaluation:</span>
                  <span className="text-emerald-400 font-bold">
                    {replayData.what_ai_knew_then.risk_guardian_evaluation} (
                    {replayData.what_ai_knew_then.approved_allocation_pct}% Alloc)
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-slate-300 pt-2 border-t border-slate-800">
                <strong>Dominant Evidence:</strong> {replayData.what_ai_knew_then.dominant_evidence}
              </p>
            </div>

            {/* 2. What AI Decided & Why */}
            <div className="p-4 rounded bg-[#0d1422] border border-[#1b283f] space-y-2.5">
              <div className="text-xs font-bold text-slate-200 flex items-center space-x-1.5 text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>2. WHAT AI DECIDED & WHY</span>
              </div>
              <div className="p-3 rounded bg-[#080d16] border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase">Action Authorized:</span>
                  <div className="text-lg font-black text-white">{replayData.what_ai_decided}</div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase">Target Security:</span>
                  <div className="text-lg font-bold text-blue-400">{replayData.symbol}</div>
                </div>
              </div>
              <p className="text-[11px] text-slate-300 pt-1 leading-relaxed">
                {replayData.why}
              </p>
            </div>
          </div>

          {/* Section 3 & 4: WHAT HAPPENED vs WAS THE DECISION GOOD? */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 3. What Happened */}
            <div className="p-4 rounded bg-[#0f1624] border border-[#1d2b45] space-y-2.5">
              <div className="text-xs font-bold text-slate-200 flex items-center space-x-1.5 text-purple-400">
                <TrendingUp className="w-4 h-4" />
                <span>3. WHAT HAPPENED (ACTUAL OUTCOME)</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="p-2.5 rounded bg-[#090d16] border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase">Subsequent Return</span>
                  <div className="text-base font-bold text-emerald-400 mt-0.5">
                    {typeof replayData.what_happened.subsequent_return_pct === "number"
                      ? `${replayData.what_happened.subsequent_return_pct > 0 ? "+" : ""}${replayData.what_happened.subsequent_return_pct}%`
                      : replayData.what_happened.subsequent_return_pct}
                  </div>
                </div>
                <div className="p-2.5 rounded bg-[#090d16] border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase">Maximum Drawdown</span>
                  <div className="text-base font-bold text-rose-400 mt-0.5">
                    {typeof replayData.what_happened.subsequent_drawdown_pct === "number"
                      ? `${replayData.what_happened.subsequent_drawdown_pct}%`
                      : replayData.what_happened.subsequent_drawdown_pct}
                  </div>
                </div>
              </div>
            </div>

            {/* 4. Was The Decision Good? */}
            <div className="p-4 rounded bg-[#0f1624] border border-[#1d2b45] space-y-2.5">
              <div className="text-xs font-bold text-slate-200 flex items-center space-x-1.5 text-amber-400">
                <Lightbulb className="w-4 h-4" />
                <span>4. WAS THE DECISION GOOD? (PROCESS VS LUCK)</span>
              </div>
              <div>
                <span
                  className={`px-2.5 py-1 rounded text-xs font-bold border inline-block ${getQualityBadge(
                    replayData.was_the_decision_good.classification
                  )}`}
                >
                  {replayData.was_the_decision_good.classification.replace(/_/g, " ")}
                </span>
              </div>
              <p className="text-[11px] text-slate-300 pt-1 leading-relaxed">
                {replayData.was_the_decision_good.process_vs_luck_analysis}
              </p>
            </div>
          </div>

          {/* Section 5: WHAT DID AI LEARN? */}
          <div className="p-4 rounded bg-[#121a2a] border border-[#233350] space-y-2">
            <div className="text-xs font-bold text-slate-200 flex items-center justify-between">
              <span className="text-blue-400">5. WHAT DID AI LEARN? (VALIDATED ERROR ATTRIBUTION)</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40">
                STATUS: {replayData.what_did_ai_learn.validation_status}
              </span>
            </div>
            <div className="text-[11px] text-slate-300 space-y-1">
              <div>
                <span className="text-slate-400 font-semibold">Error Attribution:</span>{" "}
                <strong className="text-amber-400">
                  {replayData.what_did_ai_learn.error_attribution}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 font-semibold">Validated Rule Update:</span>{" "}
                <span className="text-slate-200">{replayData.what_did_ai_learn.validated_lesson}</span>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
