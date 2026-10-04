"use client";

import React, { useState, useEffect } from "react";
import { History, Activity, Calendar, TrendingUp, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";

interface RegimePoint {
  timestamp: string;
  regime: string;
  confidence: number;
  volatility_annualized: number;
  close_price: number;
}

interface RegimeTimelineProps {
  symbol: string;
}

export const RegimeTimeline: React.FC<RegimeTimelineProps> = ({ symbol }) => {
  const [timeline, setTimeline] = useState<RegimePoint[]>([]);
  const [currentRegime, setCurrentRegime] = useState<string>("BULL_TRENDING");
  const [selectedPoint, setSelectedPoint] = useState<RegimePoint | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    api
      .getRegimeTimeline(symbol)
      .then((res) => {
        if (isMounted) {
          setTimeline(res.timeline || []);
          setCurrentRegime(res.current_regime || "SIDEWAYS_RANGING");
          if (res.timeline && res.timeline.length > 0) {
            setSelectedPoint(res.timeline[res.timeline.length - 1]);
          }
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [symbol]);

  const getRegimeColor = (reg: string) => {
    switch (reg) {
      case "BULL_TRENDING":
        return "bg-emerald-500 text-emerald-100 border-emerald-400";
      case "BEAR_TRENDING":
        return "bg-rose-500 text-rose-100 border-rose-400";
      case "CRISIS_STRESS":
        return "bg-red-700 text-white border-red-500";
      case "HIGH_VOLATILITY":
        return "bg-purple-500 text-purple-100 border-purple-400";
      case "LOW_VOLATILITY_COMPRESSION":
        return "bg-cyan-500 text-cyan-100 border-cyan-400";
      default:
        return "bg-amber-500 text-amber-100 border-amber-400";
    }
  };

  return (
    <div className="terminal-card p-5 bg-[#0a0f18] border-[#182338] space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200 font-bold">
            HISTORICAL MARKET REGIME TIMELINE // {symbol}
          </span>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Current State: <strong className="text-white">{currentRegime}</strong>
        </div>
      </div>

      {loading ? (
        <div className="py-12 text-center text-xs font-mono text-slate-400 animate-pulse">
          Loading Historical Regime Transition Matrix...
        </div>
      ) : (
        <>
          {/* Interactive Timeline Bar */}
          <div className="space-y-2">
            <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
              <span>{timeline[0]?.timestamp || "Past"}</span>
              <span>Click a historical regime block to inspect market conditions</span>
              <span>{timeline[timeline.length - 1]?.timestamp || "Present"}</span>
            </div>

            <div className="flex w-full h-9 rounded bg-[#070a10] border border-[#141d2d] overflow-hidden p-0.5 space-x-0.5">
              {timeline.map((point, idx) => {
                const isSelected = selectedPoint?.timestamp === point.timestamp;
                const regColor = getRegimeColor(point.regime);
                return (
                  <button
                    key={idx}
                    onClick={() => setSelectedPoint(point)}
                    title={`${point.timestamp}: ${point.regime} (${(point.confidence * 100).toFixed(0)}%)`}
                    className={`flex-1 h-full transition-all relative ${regColor.split(" ")[0]} opacity-80 hover:opacity-100 ${
                      isSelected ? "ring-2 ring-white scale-110 z-10 opacity-100" : ""
                    }`}
                  />
                );
              })}
            </div>
          </div>

          {/* Detailed Snapshot of Selected Point */}
          {selectedPoint && (
            <div className="p-4 rounded bg-[#0e1524] border border-[#1d2a42] space-y-3 font-mono text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-slate-300 font-bold">{selectedPoint.timestamp}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-slate-400">Classified Regime:</span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30 font-bold">
                    {selectedPoint.regime}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-300 text-[11px]">
                <div className="p-2.5 rounded bg-[#090d14] border border-slate-800">
                  <div className="text-slate-400">Asset Price</div>
                  <div className="text-sm font-bold text-white mt-0.5">${selectedPoint.close_price.toFixed(2)}</div>
                </div>
                <div className="p-2.5 rounded bg-[#090d14] border border-slate-800">
                  <div className="text-slate-400">Regime Confidence</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">
                    {(selectedPoint.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-2.5 rounded bg-[#090d14] border border-slate-800">
                  <div className="text-slate-400">Annualized Volatility</div>
                  <div className="text-sm font-bold text-purple-400 mt-0.5">
                    {(selectedPoint.volatility_annualized * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-2.5 rounded bg-[#090d14] border border-slate-800">
                  <div className="text-slate-400">Transition Risk</div>
                  <div className="text-sm font-bold text-amber-400 mt-0.5">
                    {selectedPoint.volatility_annualized > 0.28 ? "ELEVATED" : "STABLE"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Regime Legend */}
          <div className="flex flex-wrap items-center gap-3 pt-2 text-[10px] font-mono text-slate-400">
            <span className="font-semibold uppercase text-slate-400">LEGEND:</span>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span>
              <span>BULL_TRENDING</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span>
              <span>BEAR_TRENDING</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-red-700"></span>
              <span>CRISIS_STRESS</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-purple-500"></span>
              <span>HIGH_VOLATILITY</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500"></span>
              <span>SIDEWAYS / TRANSITION</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
