"use client";

import React from "react";
import { HelpCircle, AlertOctagon, Target, ShieldAlert, ArrowRight, Zap } from "lucide-react";
import { CounterfactualAnalysis } from "../types";

interface CounterfactualPanelProps {
  counterfactuals: CounterfactualAnalysis | undefined;
}

export const CounterfactualPanel: React.FC<CounterfactualPanelProps> = ({ counterfactuals }) => {
  if (!counterfactuals) return null;

  const base = counterfactuals.base_case;
  const adverse = counterfactuals.adverse_case;
  const severe = counterfactuals.severe_case;

  return (
    <div className="terminal-card p-5 bg-[#0a0f18] border-[#182338] space-y-5">
      {/* Title & Concept Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <HelpCircle className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200 font-bold">
            "WHAT WOULD CHANGE MY MIND?" // COUNTERFACTUAL ENGINE
          </span>
        </div>
        <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-3">
          <span>Stop Loss: <strong className="text-rose-400">${counterfactuals.stop_loss_level.toFixed(2)}</strong></span>
          <span>Take Profit: <strong className="text-emerald-400">${counterfactuals.take_profit_level.toFixed(2)}</strong></span>
        </div>
      </div>

      {/* 3 Scenario Projection Cards: Base, Adverse, Severe */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
        {/* Base Case */}
        <div className="p-3.5 rounded bg-[#0d1522] border border-[#1b2a42] space-y-2">
          <div className="flex items-center justify-between text-slate-300">
            <span className="font-semibold text-emerald-400">{base.name}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
              {base.probability_pct}% prob
            </span>
          </div>
          <div className="text-lg font-bold text-white">${base.price_target.toFixed(2)}</div>
          <div className="text-[11px] text-slate-400 flex justify-between">
            <span>Expected: {base.expected_return_pct > 0 ? "+" : ""}{base.expected_return_pct}%</span>
            <span>Portf: {base.portfolio_impact_pct > 0 ? "+" : ""}{base.portfolio_impact_pct}%</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight pt-1 border-t border-slate-800">
            {base.trigger_conditions[0]}
          </p>
        </div>

        {/* Adverse Case */}
        <div className="p-3.5 rounded bg-[#171118] border border-[#381e28] space-y-2">
          <div className="flex items-center justify-between text-slate-300">
            <span className="font-semibold text-amber-400">{adverse.name}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">
              {adverse.probability_pct}% prob
            </span>
          </div>
          <div className="text-lg font-bold text-white">${adverse.price_target.toFixed(2)}</div>
          <div className="text-[11px] text-slate-400 flex justify-between">
            <span className="text-rose-400">{adverse.expected_return_pct}%</span>
            <span className="text-rose-400">Portf: {adverse.portfolio_impact_pct}%</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight pt-1 border-t border-slate-800">
            {adverse.trigger_conditions[0]}
          </p>
        </div>

        {/* Severe Shock Case */}
        <div className="p-3.5 rounded bg-[#190d12] border border-[#441a24] space-y-2">
          <div className="flex items-center justify-between text-slate-300">
            <span className="font-semibold text-rose-400">{severe.name}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400">
              {severe.probability_pct}% prob
            </span>
          </div>
          <div className="text-lg font-bold text-white">${severe.price_target.toFixed(2)}</div>
          <div className="text-[11px] text-slate-400 flex justify-between">
            <span className="text-rose-400">{severe.expected_return_pct}%</span>
            <span className="text-rose-400">Portf: {severe.portfolio_impact_pct}%</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight pt-1 border-t border-slate-800">
            {severe.trigger_conditions[0]}
          </p>
        </div>
      </div>

      {/* Explicit Invalidation Conditions (What Would Change My Mind?) */}
      <div className="p-4 rounded bg-[#101420] border border-[#1c273c] space-y-2.5">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>PRE-DEFINED INVALIDATION TRIGGERS (EXIT / ABSTAIN RULESET):</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono text-slate-300">
          {counterfactuals.invalidation_conditions.map((cond, idx) => (
            <div key={idx} className="flex items-start space-x-2 p-2 rounded bg-[#0b0e16] border border-[#162030]">
              <span className="text-amber-400 font-bold shrink-0">#{idx + 1}</span>
              <span className="text-slate-300 text-[11px]">{cond}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
