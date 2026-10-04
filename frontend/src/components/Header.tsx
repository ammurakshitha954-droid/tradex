"use client";

import React, { useState, useEffect } from "react";
import { Activity, ShieldCheck, RefreshCw, Cpu, Globe2, Radio } from "lucide-react";
import { MarketPulse, AssetQuote } from "../types";

interface HeaderProps {
  pulse: MarketPulse | null;
  onRefresh: () => void;
  isLoading: boolean;
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  pulse,
  onRefresh,
  isLoading,
  selectedSymbol,
  onSelectSymbol,
}) => {
  const [timeStr, setTimeStr] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString("en-US", { hour12: false, timeZoneName: "short" }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const regime = pulse?.market_regime || "TRANSITION_UNCERTAIN";
  const regimeColor =
    regime === "BULL_TRENDING"
      ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
      : regime === "BEAR_TRENDING" || regime === "CRISIS_STRESS"
      ? "text-rose-400 border-rose-500/30 bg-rose-500/10"
      : "text-amber-400 border-amber-500/30 bg-amber-500/10";

  return (
    <header className="border-b border-[#1a2333] bg-[#090d14]/95 backdrop-blur sticky top-0 z-50">
      {/* Top Bar: Brand, Regime & Engine Status */}
      <div className="flex items-center justify-between px-4 py-2 text-xs">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className="h-6 w-6 rounded bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center font-bold text-white shadow-sm">
              <Cpu className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="font-semibold tracking-wider text-slate-100 text-sm">
                ADAPTIVE AI
              </span>
              <span className="text-[10px] text-slate-400 font-mono ml-1.5 uppercase tracking-wider">
                DECISION-SUPPORT SYSTEM
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-1 pl-3 border-l border-slate-800 text-[11px] text-slate-400 font-mono">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>SYSTEM ONLINE</span>
            <span className="text-slate-600">|</span>
            <span>DETERMINISTIC QUANT LAYER</span>
          </div>
        </div>

        {/* Center: Market Regime Banner */}
        <div className="flex items-center space-x-2">
          <div className={`px-2.5 py-1 rounded border text-[11px] font-mono flex items-center space-x-1.5 ${regimeColor}`}>
            <Activity className="w-3.5 h-3.5" />
            <span className="font-semibold">MARKET REGIME: {regime}</span>
            <span className="text-slate-400 text-[10px]">
              ({pulse ? `${(pulse.regime_confidence * 100).toFixed(0)}%` : "N/A"})
            </span>
          </div>

          <div className="hidden lg:flex items-center px-2 py-1 rounded bg-[#111724] border border-[#1d273a] text-slate-300 font-mono text-[11px] space-x-1">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>RISK GUARDIAN:</span>
            <span className="text-emerald-400 font-semibold">ACTIVE</span>
          </div>
        </div>

        {/* Right: Time & Refresh Action */}
        <div className="flex items-center space-x-3">
          <div className="font-mono text-slate-400 text-[11px] flex items-center space-x-1">
            <Globe2 className="w-3 h-3 text-slate-500" />
            <span>{timeStr || "UTC"}</span>
          </div>

          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-[#131b2a] hover:bg-[#1a2538] border border-[#233149] text-slate-200 transition-colors text-xs font-mono"
            title="Refresh System Data"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin text-blue-400" : ""}`} />
            <span>SYNC</span>
          </button>
        </div>
      </div>

      {/* Ticker Tape */}
      <div className="bg-[#0b0f17] border-t border-[#141b27] px-4 py-1.5 overflow-x-auto flex items-center space-x-6 text-[11px] font-mono no-scrollbar">
        <div className="flex items-center space-x-1.5 text-slate-400 font-semibold uppercase tracking-wider shrink-0">
          <Radio className="w-3 h-3 text-blue-400" />
          <span>WATCHLIST:</span>
        </div>
        {pulse?.watchlist?.map((item: AssetQuote) => {
          const isSelected = item.symbol === selectedSymbol;
          const isUp = item.change >= 0;
          return (
            <button
              key={item.symbol}
              onClick={() => onSelectSymbol(item.symbol)}
              className={`flex items-center space-x-1.5 px-2 py-0.5 rounded shrink-0 transition-all ${
                isSelected
                  ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                  : "text-slate-300 hover:bg-[#131926]"
              }`}
            >
              <span className="font-bold">{item.symbol}</span>
              <span className="text-slate-200">${item.price.toFixed(2)}</span>
              <span className={isUp ? "text-emerald-400" : "text-rose-400"}>
                {isUp ? "+" : ""}
                {item.pct_change.toFixed(2)}%
              </span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
