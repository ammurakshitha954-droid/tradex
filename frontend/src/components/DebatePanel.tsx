"use client";

import React from "react";
import { Scale, AlertTriangle, CheckCircle, Split } from "lucide-react";
import { ModelCouncilResult, EvidenceConflictAnalysis, ModelVote } from "../types";

interface DebatePanelProps {
  council: ModelCouncilResult | undefined;
  conflict: EvidenceConflictAnalysis | undefined;
}

export const DebatePanel: React.FC<DebatePanelProps> = ({ council, conflict }) => {
  if (!council || !conflict) return null;

  return (
    <div className="terminal-card p-5 bg-[#0a0f18] border-[#182338] space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <Scale className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200 font-bold">
            MODEL COUNCIL DEBATE & DISAGREEMENT MATRIX
          </span>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono">
          <span>
            Conflict:{" "}
            <strong
              className={
                conflict.conflict_severity === "LOW"
                  ? "text-emerald-400"
                  : conflict.conflict_severity === "MILD"
                  ? "text-amber-400"
                  : "text-rose-400"
              }
            >
              {conflict.conflict_severity}
            </strong>
          </span>
          <span className="text-slate-600">|</span>
          <span>
            Entropy: <strong className="text-purple-400">{(conflict.entropy_score * 100).toFixed(0)}%</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span>
            Penalty: <strong className="text-amber-400">-{(conflict.uncertainty_penalty * 100).toFixed(0)}%</strong>
          </span>
        </div>
      </div>

      {/* Model Council Vote Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5 text-xs font-mono">
        {council.votes.map((vote: ModelVote, idx: number) => {
          const isBuy = vote.signal === "BUY";
          const isSell = vote.signal === "SELL";
          const isHold = vote.signal === "HOLD";

          const badgeColor = isBuy
            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            : isSell
            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
            : "bg-amber-500/10 text-amber-400 border-amber-500/30";

          return (
            <div key={idx} className="p-3 rounded bg-[#0e1422] border border-[#19243a] flex flex-col justify-between space-y-2">
              <div>
                <div className="text-[10px] text-slate-400 truncate">{vote.model_name}</div>
                <div className="flex items-center justify-between mt-1">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${badgeColor}`}>
                    {vote.signal}
                  </span>
                  <span className="text-slate-400 text-[10px]">{(vote.conviction * 100).toFixed(0)}%</span>
                </div>
              </div>
              <p className="text-[10px] text-slate-300 line-clamp-3 pt-1 border-t border-slate-800">
                {vote.primary_rationale}
              </p>
            </div>
          );
        })}
      </div>

      {/* Conflict Narrative */}
      <div className="p-4 rounded bg-[#0f1524] border border-[#1d2942] space-y-3 text-xs font-mono">
        <div className="flex items-center space-x-2 text-slate-200 font-semibold">
          <Split className="w-4 h-4 text-purple-400" />
          <span>EVIDENCE CONFLICT ATTRIBUTION:</span>
        </div>
        <p className="text-slate-300 text-xs leading-relaxed">{conflict.conflict_explanation}</p>

        {/* Pairwise Oppositions */}
        {conflict.conflict_pairs.filter(p => p.severity !== "NONE").length > 0 && (
          <div className="pt-2 border-t border-slate-800 space-y-1.5">
            <div className="text-[11px] text-slate-400 font-medium">Pairwise Tensions:</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
              {conflict.conflict_pairs
                .filter(p => p.severity !== "NONE")
                .map((pair, i) => (
                  <div key={i} className="p-2 rounded bg-[#090d14] border border-slate-800 text-slate-300 flex items-start space-x-1.5">
                    <span className={pair.severity === "STRONG" ? "text-rose-400 font-bold" : "text-amber-400 font-bold"}>
                      [{pair.severity}]
                    </span>
                    <span>{pair.description}</span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
