"use client";

import React, { useState, useEffect } from "react";
import { Header } from "../components/Header";
import { Navigation, TabType } from "../components/Navigation";
import { DecisionCard } from "../components/DecisionCard";
import { MultiHorizonPanel } from "../components/MultiHorizonPanel";
import { CounterfactualPanel } from "../components/CounterfactualPanel";
import { DebatePanel } from "../components/DebatePanel";
import { MarketBrain } from "../components/MarketBrain";
import { RegimeTimeline } from "../components/RegimeTimeline";
import { PortfolioPanel } from "../components/PortfolioPanel";
import { DecisionReplayView } from "../components/DecisionReplayView";
import { BacktestWorkspace } from "../components/BacktestWorkspace";
import { ExperimentsWorkspace } from "../components/ExperimentsWorkspace";
import { MemoryTimeline } from "../components/MemoryTimeline";
import { SystemHealthView } from "../components/SystemHealthView";
import { MarketPulse, DecisionRecord, PortfolioState } from "../types";
import { api } from "../lib/api";
import { Activity, ShieldCheck, Cpu, ArrowUpRight, ArrowDownRight, Sparkles } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>("command_center");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("NVDA");
  const [pulse, setPulse] = useState<MarketPulse | null>(null);
  const [decision, setDecision] = useState<DecisionRecord | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDecisionLoading, setIsDecisionLoading] = useState<boolean>(false);

  const fetchGlobalState = async () => {
    setIsLoading(true);
    try {
      const [pulseData, portData] = await Promise.all([
        api.getMarketPulse().catch(() => null),
        api.getPortfolio().catch(() => null),
      ]);
      if (pulseData) setPulse(pulseData);
      if (portData) setPortfolio(portData);
    } catch (err) {
      console.error("Global state sync error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDecisionForSymbol = async (symbol: string) => {
    setIsDecisionLoading(true);
    try {
      const dec = await api.getLatestDecision(symbol);
      setDecision(dec);
    } catch (err) {
      console.error(`Failed to fetch decision for ${symbol}:`, err);
    } finally {
      setIsDecisionLoading(false);
    }
  };

  useEffect(() => {
    fetchGlobalState();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchDecisionForSymbol(selectedSymbol);
    }
  }, [selectedSymbol]);

  const handleSelectSymbol = (sym: string) => {
    setSelectedSymbol(sym);
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#080b10] text-[#f8fafc]">
      {/* Top Header & Ticker Tape */}
      <Header
        pulse={pulse}
        onRefresh={() => {
          fetchGlobalState();
          fetchDecisionForSymbol(selectedSymbol);
        }}
        isLoading={isLoading || isDecisionLoading}
        selectedSymbol={selectedSymbol}
        onSelectSymbol={handleSelectSymbol}
      />

      {/* Main Layout: Left Navigation + Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        <Navigation activeTab={activeTab} onTabChange={setActiveTab} />

        <main className="flex-1 p-6 overflow-y-auto max-h-[calc(100vh-80px)] space-y-6">
          {/* TAB 1: AI COMMAND CENTER */}
          {activeTab === "command_center" && (
            <div className="space-y-6">
              {/* Market Pulse Banner */}
              <div className="terminal-card p-5 bg-[#0a0f18] border-[#182338] flex flex-wrap items-center justify-between gap-4 font-mono">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-white uppercase tracking-wider">
                      BENCHMARK PULSE: {pulse?.benchmark || "SPY"}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/30">
                      REGIME: {pulse?.market_regime || "TRANSITION_UNCERTAIN"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                    {pulse?.key_macro_drivers?.[0] ||
                      "Market oscillating within normal range-bound dispersion bounds."}
                  </p>
                </div>

                <div className="flex items-center space-x-4 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Regime Stability</span>
                    <div className="text-base font-bold text-emerald-400">
                      {pulse ? `${(pulse.stability_score * 100).toFixed(0)}%` : "N/A"}
                    </div>
                  </div>
                  <div className="border-l border-slate-800 pl-4">
                    <span className="text-[10px] text-slate-400 uppercase">Market Breadth</span>
                    <div className="text-base font-bold text-blue-400">
                      {pulse ? `${pulse.market_breadth_advance_pct}% Adv` : "N/A"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Dominant AI Decision Card */}
              <DecisionCard
                decision={decision}
                isLoading={isDecisionLoading}
                onReanalyze={() => fetchDecisionForSymbol(selectedSymbol)}
              />

              {/* Multi-Horizon Panel */}
              <MultiHorizonPanel horizons={decision?.horizons} />

              {/* Counterfactual Panel ("What Would Change My Mind?") */}
              <CounterfactualPanel counterfactuals={decision?.counterfactuals} />
            </div>
          )}

          {/* TAB 2: ASSET DECISION CARD & COUNTERFACTUALS */}
          {activeTab === "decision_card" && (
            <div className="space-y-6">
              <DecisionCard
                decision={decision}
                isLoading={isDecisionLoading}
                onReanalyze={() => fetchDecisionForSymbol(selectedSymbol)}
              />
              <MultiHorizonPanel horizons={decision?.horizons} />
              <CounterfactualPanel counterfactuals={decision?.counterfactuals} />
            </div>
          )}

          {/* TAB 3: AI DEBATE & CONFLICT MATRIX */}
          {activeTab === "ai_debate" && (
            <div className="space-y-6">
              <DebatePanel council={decision?.council} conflict={decision?.conflict} />
              <MultiHorizonPanel horizons={decision?.horizons} />
            </div>
          )}

          {/* TAB 4: MARKET BRAIN GRAPH */}
          {activeTab === "market_brain" && (
            <div className="space-y-6">
              <MarketBrain decision={decision} />
              <DebatePanel council={decision?.council} conflict={decision?.conflict} />
            </div>
          )}

          {/* TAB 5: REGIME TIMELINE */}
          {activeTab === "regime_timeline" && (
            <div className="space-y-6">
              <RegimeTimeline symbol={selectedSymbol} />
            </div>
          )}

          {/* TAB 6: PORTFOLIO & RISK GUARDIAN */}
          {activeTab === "portfolio_risk" && (
            <div className="space-y-6">
              <PortfolioPanel portfolio={portfolio} onRefreshPortfolio={fetchGlobalState} />
            </div>
          )}

          {/* TAB 7: DECISION REPLAY */}
          {activeTab === "decision_replay" && (
            <div className="space-y-6">
              <DecisionReplayView />
            </div>
          )}

          {/* TAB 8: BACKTESTING WORKSPACE */}
          {activeTab === "backtesting" && (
            <div className="space-y-6">
              <BacktestWorkspace />
            </div>
          )}

          {/* TAB 9: EXPERIMENTS & ABLATION STUDY */}
          {activeTab === "experiments" && (
            <div className="space-y-6">
              <ExperimentsWorkspace />
            </div>
          )}

          {/* TAB 10: CONTEXTUAL MEMORY & LESSONS */}
          {activeTab === "memory_lessons" && (
            <div className="space-y-6">
              <MemoryTimeline />
            </div>
          )}

          {/* TAB 11: SYSTEM HEALTH */}
          {activeTab === "system_health" && (
            <div className="space-y-6">
              <SystemHealthView />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
