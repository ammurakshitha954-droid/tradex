"use client";

import React from "react";
import {
  LayoutDashboard,
  BrainCircuit,
  Scale,
  Network,
  History,
  Briefcase,
  PlayCircle,
  FlaskConical,
  Database,
  Activity,
  ChevronRight,
} from "lucide-react";

export type TabType =
  | "command_center"
  | "decision_card"
  | "ai_debate"
  | "market_brain"
  | "regime_timeline"
  | "portfolio_risk"
  | "decision_replay"
  | "backtesting"
  | "experiments"
  | "memory_lessons"
  | "system_health";

interface NavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const NAV_ITEMS: Array<{ id: TabType; label: string; icon: React.ElementType; badge?: string }> = [
  { id: "command_center", label: "AI Command Center", icon: LayoutDashboard },
  { id: "decision_card", label: "Asset Decision & Why Not", icon: BrainCircuit, badge: "CORE" },
  { id: "ai_debate", label: "AI Debate & Conflict", icon: Scale },
  { id: "market_brain", label: "Market Brain (Graph)", icon: Network },
  { id: "regime_timeline", label: "Regime Timeline", icon: History },
  { id: "portfolio_risk", label: "Portfolio & Risk Guardian", icon: Briefcase },
  { id: "decision_replay", label: "Decision Replay (Time-Travel)", icon: PlayCircle, badge: "RESEARCH" },
  { id: "backtesting", label: "Backtest Workspace", icon: Activity },
  { id: "experiments", label: "Ablation & Benchmarks", icon: FlaskConical },
  { id: "memory_lessons", label: "AI Memory & Errors", icon: Database },
  { id: "system_health", label: "System Health", icon: Activity },
];

export const Navigation: React.FC<NavigationProps> = ({ activeTab, onTabChange }) => {
  return (
    <nav className="w-64 bg-[#0a0e16] border-r border-[#1a2333] flex flex-col justify-between h-[calc(100vh-80px)] shrink-0 py-3">
      <div className="space-y-1 px-2 overflow-y-auto">
        <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
          DECISION INTELLIGENCE
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded text-xs font-medium transition-all ${
                isActive
                  ? "bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#121824]"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                    item.badge === "CORE"
                      ? "bg-indigo-500/20 text-indigo-300"
                      : "bg-emerald-500/20 text-emerald-300"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="p-3 mx-2 rounded border border-[#172132] bg-[#0c111a] text-[11px] font-mono text-slate-400 space-y-1">
        <div className="flex items-center justify-between text-slate-300">
          <span>MODEL VER:</span>
          <span className="text-blue-400 font-bold">v2.4-ADAPTIVE</span>
        </div>
        <div className="flex items-center justify-between">
          <span>CALCULATIONS:</span>
          <span className="text-emerald-400 font-medium">DETERMINISTIC</span>
        </div>
        <div className="flex items-center justify-between">
          <span>LLM REASONING:</span>
          <span className="text-purple-400 font-medium">STRUCTURED</span>
        </div>
      </div>
    </nav>
  );
};
