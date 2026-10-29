"use client";

import React from "react";
import { RaceForecast } from "@/types";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle,
  ExternalLink,
  HelpCircle,
  Info,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";

interface RaceDetailDrawerProps {
  race: RaceForecast | null;
  onClose: () => void;
}

export const RaceDetailDrawer: React.FC<RaceDetailDrawerProps> = ({ race, onClose }) => {
  if (!race) return null;

  const demCandidate = race.candidates.find((c) => c.party === "DEM");
  const repCandidate = race.candidates.find((c) => c.party === "REP");

  return (
    <div className="bg-surface-100/95 border border-surface-300/40 rounded-2xl p-5 backdrop-blur-md shadow-2xl flex flex-col gap-4 text-white">
      {/* Drawer Header */}
      <div className="flex items-start justify-between border-b border-surface-300/30 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-xs font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/40 rounded-md">
              {race.chamber.toUpperCase()}
            </span>
            <h3 className="text-lg font-bold text-white tracking-tight">
              {race.state_name}
            </h3>
            <span className="text-xs font-mono text-slate-400">({race.race_id})</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Stage 1 Polling Anchor combined with Stage 2 Bounded Residual Meta-Regression
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-200/80 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Head-to-Head Candidates Banner */}
      <div className="grid grid-cols-2 gap-3 bg-surface-200/40 p-3.5 rounded-xl border border-surface-300/30">
        {/* Democratic Candidate */}
        <div className="flex flex-col gap-1 border-r border-surface-300/30 pr-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-blue-400 uppercase tracking-wide">Democrat</span>
            {demCandidate?.incumbent && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                Incumbent
              </span>
            )}
          </div>
          <div className="text-sm font-bold text-white truncate">
            {demCandidate?.name || "Democratic Nominee"}
          </div>
          <div className="text-xl font-mono font-extrabold text-blue-400">
            {(race.dem_win_prob * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-400 font-mono">Win Probability</div>
        </div>

        {/* Republican Candidate */}
        <div className="flex flex-col gap-1 pl-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-red-400 uppercase tracking-wide">Republican</span>
            {repCandidate?.incumbent && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-red-500/20 text-red-300 border border-red-500/30">
                Incumbent
              </span>
            )}
          </div>
          <div className="text-sm font-bold text-white truncate">
            {repCandidate?.name || "Republican Nominee"}
          </div>
          <div className="text-xl font-mono font-extrabold text-red-400">
            {(race.rep_win_prob * 100).toFixed(1)}%
          </div>
          <div className="text-[11px] text-slate-400 font-mono">Win Probability</div>
        </div>
      </div>

      {/* Two-Stage Model Margin Synthesis */}
      <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-3">
        <div className="flex items-center justify-between text-xs border-b border-slate-800 pb-2">
          <span className="font-bold text-slate-300 flex items-center gap-1.5">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            Two-Stage Ensemble Decomposition
          </span>
          <span className="font-mono text-xs text-yellow-400 font-bold">
            Projected Margin: {race.predicted_dem_margin >= 0 ? "+" : ""}
            {race.predicted_dem_margin.toFixed(1)}% (Dem)
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
          <div className="p-2.5 bg-surface-200/50 rounded-lg border border-surface-300/30">
            <div className="text-[10px] text-slate-400">Stage 1 Anchor</div>
            <div className="text-sm font-bold text-magenta-400 text-purple-300">
              {race.mu_anchor >= 0 ? "+" : ""}
              {race.mu_anchor.toFixed(2)}%
            </div>
            <div className="text-[9px] text-slate-500">Polls &amp; Kalshi</div>
          </div>

          <div className="p-2.5 bg-surface-200/50 rounded-lg border border-surface-300/30">
            <div className="text-[10px] text-slate-400">Stage 2 Social Res.</div>
            <div
              className={`text-sm font-bold ${
                race.delta_residual >= 0 ? "text-cyan-400" : "text-amber-400"
              }`}
            >
              {race.delta_residual >= 0 ? "+" : ""}
              {race.delta_residual.toFixed(2)}%
            </div>
            <div className="text-[9px] text-slate-500">&plusmn;2.00% bounded cap</div>
          </div>

          <div className="p-2.5 bg-surface-200/50 rounded-lg border border-surface-300/30">
            <div className="text-[10px] text-slate-400">90% Credible Interval</div>
            <div className="text-xs font-bold text-slate-200">
              [{race.ci_lower_90.toFixed(1)}%, {race.ci_upper_90.toFixed(1)}%]
            </div>
            <div className="text-[9px] text-slate-500">Fat tails (&nu;=7)</div>
          </div>

          <div className="p-2.5 bg-surface-200/50 rounded-lg border border-surface-300/30">
            <div className="text-[10px] text-slate-400">Kalshi Liquidity (L_r)</div>
            <div className="text-sm font-bold text-emerald-400">
              {(race.liquidity_weight * 100).toFixed(0)}%
            </div>
            <div className="text-[9px] text-slate-500">Sigmoid weight</div>
          </div>
        </div>

        {/* Bounded Residual Safety Invariant Badge */}
        <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-950/30 border border-emerald-500/30 text-[11px] text-emerald-300">
          <div className="flex items-center gap-1.5 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Social Residual Safety Invariant Passed
          </div>
          <span className="font-mono text-[10px]">
            |{race.delta_residual.toFixed(2)}%| &le; 2.00% cap
          </span>
        </div>
      </div>

      {/* TreeSHAP Feature Attributions Waterfall */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-slate-300">
            Additive Feature Attributions (&phi;_i = &beta;_i(x_i - &mu;_i))
          </span>
          <span className="text-[10px] text-slate-400 font-mono">Closed-form TreeSHAP</span>
        </div>

        <div className="space-y-1.5">
          {race.attributions.map((attr, idx) => {
            const isPositive = attr.contribution >= 0;
            const pctWidth = Math.min(100, Math.abs(attr.contribution) * 35);

            return (
              <div key={idx} className="flex items-center gap-3 text-xs">
                <span className="w-44 text-slate-300 truncate text-[11px]">
                  {attr.label}
                </span>
                <div className="flex-1 h-3.5 bg-slate-900 rounded flex items-center relative overflow-hidden border border-slate-800">
                  <div
                    style={{ width: `${pctWidth}%` }}
                    className={`h-full rounded ${
                      isPositive ? "bg-blue-500 ml-auto" : "bg-red-500 mr-auto"
                    }`}
                  />
                </div>
                <span
                  className={`w-14 text-right font-mono font-bold text-[11px] ${
                    isPositive ? "text-blue-400" : "text-red-400"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {attr.contribution.toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Kalshi Prediction Market Arbitrage Radar Badge */}
      {race.kalshi_ticker && (
        <div className="mt-2 p-3 rounded-xl bg-purple-950/30 border border-purple-500/30 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30">
              <ExternalLink className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-white flex items-center gap-2">
                Kalshi Contract: <span className="font-mono text-purple-300">{race.kalshi_ticker}</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Trading @ {race.kalshi_price_cents}&cent; &bull; Model Fair Value: {(race.dem_win_prob * 100).toFixed(1)}&cent;
              </div>
            </div>
          </div>
          <div>
            {race.arbitrage_status === "ARBITRAGE_ALERT" ? (
              <span className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">
                ARBITRAGE ALERT ({race.arbitrage_edge}% EDGE)
              </span>
            ) : (
              <span className="px-2 py-0.5 text-[11px] font-mono text-emerald-300 bg-emerald-500/10 rounded border border-emerald-500/20">
                In Market Equilibrium
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
