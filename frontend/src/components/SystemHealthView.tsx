"use client";

import React, { useState, useEffect } from "react";
import { Activity, Server, Cpu, ShieldCheck, Database, RefreshCw, CheckCircle2 } from "lucide-react";
import { SystemHealth } from "../types";
import { api } from "../lib/api";

export const SystemHealthView: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = () => {
    setLoading(true);
    api
      .getSystemHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="terminal-card p-6 bg-[#0a0f18] border-[#182338] space-y-6 font-mono text-xs">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#162133] pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-emerald-400" />
          <span className="text-sm uppercase tracking-wider text-slate-100 font-bold">
            SYSTEM HEALTH & OBSERVABILITY STATUS
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>SYSTEM: {health?.status || "OPERATIONAL"}</span>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-1 rounded bg-[#131b2a] hover:bg-[#1a2538] text-slate-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {health && (
        <div className="space-y-6">
          {/* Services Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {Object.entries(health.services).map(([serviceName, data]) => (
              <div
                key={serviceName}
                className="p-3.5 rounded bg-[#0d1422] border border-[#1b273d] flex flex-col justify-between space-y-2"
              >
                <div>
                  <div className="text-[10px] text-slate-400 uppercase truncate">
                    {serviceName.replace(/_/g, " ")}
                  </div>
                  <div className="text-sm font-bold text-white mt-1 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{data.status}</span>
                  </div>
                </div>
                <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-800">
                  {data.latency_ms && `Latency: ${data.latency_ms}ms`}
                  {data.freshness_seconds && `Freshness: ${data.freshness_seconds}s`}
                  {data.regimes_supported && `Regimes: ${data.regimes_supported}`}
                  {data.models_registered && `Models: ${data.models_registered}`}
                  {data.records_indexed && `Records: ${data.records_indexed}`}
                  {data.mode && `${data.mode}`}
                  {data.model && `Model: ${data.model}`}
                </div>
              </div>
            ))}
          </div>

          {/* Architecture Provenance & Model Versions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded bg-[#0e1626] border border-[#1e2e4a] space-y-2">
              <div className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Model Versions & Pipeline Provenance
              </div>
              <div className="space-y-1 text-[11px] text-slate-300">
                {Object.entries(health.model_versions).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-0.5 border-b border-slate-800/40">
                    <span className="text-slate-400">{k.replace(/_/g, " ")}:</span>
                    <span className="text-blue-400 font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded bg-[#0e1626] border border-[#1e2e4a] space-y-2">
              <div className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Production Performance Telemetry
              </div>
              <div className="space-y-1 text-[11px] text-slate-300">
                {Object.entries(health.system_metrics).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-0.5 border-b border-slate-800/40">
                    <span className="text-slate-400">{k.replace(/_/g, " ")}:</span>
                    <span className="text-emerald-400 font-bold">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
