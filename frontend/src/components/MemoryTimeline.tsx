"use client";

import React, { useState, useEffect } from "react";
import { Database, Filter, CheckCircle2, AlertOctagon, Lightbulb, Search } from "lucide-react";
import { MemoryRecord } from "../types";
import { api } from "../lib/api";

export const MemoryTimeline: React.FC = () => {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [filterSymbol, setFilterSymbol] = useState<string>("ALL");
  const [filterRegime, setFilterRegime] = useState<string>("ALL");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api
      .getMemories()
      .then((data) => {
        setMemories(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filtered = memories.filter((m) => {
    if (filterSymbol !== "ALL" && m.symbol !== filterSymbol) return false;
    if (filterRegime !== "ALL" && m.regime !== filterRegime) return false;
    return true;
  });

  const getQualityBadge = (label: string) => {
    if (label.includes("GOOD_DECISION_GOOD_OUTCOME")) {
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    }
    if (label.includes("GOOD_DECISION_BAD_OUTCOME")) {
      return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    }
    if (label.includes("BAD_DECISION_GOOD_OUTCOME")) {
      return "bg-amber-500/10 text-amber-400 border-amber-500/30";
    }
    return "bg-rose-500/10 text-rose-400 border-rose-500/30";
  };

  return (
    <div className="terminal-card p-6 bg-[#0a0f18] border-[#182338] space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-mono uppercase tracking-wider text-slate-100 font-bold">
            CONTEXTUAL DECISION MEMORY & SELF-CORRECTION LOGS
          </span>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="text-slate-400">Symbol:</span>
          <select
            value={filterSymbol}
            onChange={(e) => setFilterSymbol(e.target.value)}
            className="p-1 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          >
            <option value="ALL">All Assets</option>
            <option value="NVDA">NVDA</option>
            <option value="AAPL">AAPL</option>
            <option value="MSFT">MSFT</option>
            <option value="SPY">SPY</option>
          </select>

          <span className="text-slate-400 ml-2">Regime:</span>
          <select
            value={filterRegime}
            onChange={(e) => setFilterRegime(e.target.value)}
            className="p-1 rounded bg-[#0d1422] border border-[#1b273c] text-white"
          >
            <option value="ALL">All Regimes</option>
            <option value="BULL_TRENDING">BULL_TRENDING</option>
            <option value="BEAR_TRENDING">BEAR_TRENDING</option>
            <option value="HIGH_VOLATILITY">HIGH_VOLATILITY</option>
            <option value="TRANSITION_UNCERTAIN">TRANSITION_UNCERTAIN</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-slate-400 animate-pulse">
          Loading Contextual Decision History...
        </div>
      ) : (
        <div className="space-y-3 font-mono text-xs">
          {filtered.map((m: MemoryRecord) => (
            <div
              key={m.id}
              className="p-4 rounded bg-[#0c121e] border border-[#182338] hover:border-[#22334e] transition-all space-y-2.5"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-2">
                <div className="flex items-center space-x-2.5">
                  <span className="text-sm font-bold text-white">{m.symbol}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      m.decision === "BUY"
                        ? "bg-emerald-500/15 text-emerald-400"
                        : m.decision === "SELL"
                        ? "bg-rose-500/15 text-rose-400"
                        : m.decision === "HOLD"
                        ? "bg-amber-500/15 text-amber-400"
                        : "bg-slate-500/15 text-slate-400"
                    }`}
                  >
                    {m.decision}
                  </span>
                  <span className="text-slate-400 text-[11px]">
                    Conf: {(m.confidence * 100).toFixed(0)}% | Uncert: {(m.uncertainty * 100).toFixed(0)}%
                  </span>
                  <span className="text-purple-400 text-[11px]">[{m.regime}]</span>
                </div>

                <div className="flex items-center space-x-2 text-[11px]">
                  <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getQualityBadge(m.decision_quality_label)}`}>
                    {m.decision_quality_label.replace(/_/g, " ")}
                  </span>
                  <span className="text-slate-500">{new Date(m.timestamp).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="text-[11px] text-slate-300">
                <strong className="text-slate-400">Context:</strong> {m.dominant_evidence}
              </div>

              <div className="p-2.5 rounded bg-[#080d16] border border-slate-800/80 flex items-start space-x-2 text-[11px]">
                <Lightbulb className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="text-amber-300 font-semibold">
                    VALIDATED LESSON ({m.validation_status}):
                  </div>
                  <p className="text-slate-300">{m.validated_lesson || "Standard market tracking."}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
