"use client";

import React from "react";
import { MonteCarloSummary } from "@/types";
import { Award, ShieldAlert, TrendingUp } from "lucide-react";

interface ChamberBalanceBarProps {
  monteCarlo: MonteCarloSummary;
}

export const ChamberBalanceBar: React.FC<ChamberBalanceBarProps> = ({ monteCarlo }) => {
  const { senate, house } = monteCarlo;

  return (
    <div className="bg-surface-100/90 border border-surface-300/40 rounded-2xl p-5 backdrop-blur-md shadow-2xl flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-300/30 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-xl">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              10,000-Draw Chamber Balance of Power
            </h3>
            <p className="text-xs text-slate-400">
              Student-t fat-tail errors ($\nu = 7$) with correlated national and demographic covariance shocks
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[11px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            N = 10,000 Correlated Draws
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Senate Balance Bar */}
        <div className="bg-surface-200/40 border border-surface-300/30 rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              U.S. Senate (100 Seats)
            </span>
            <span className="text-slate-400 font-mono">
              Threshold: <strong className="text-white">50 seats</strong> for majority
            </span>
          </div>

          {/* Bar Visual */}
          <div className="relative w-full h-8 bg-slate-900 rounded-lg overflow-hidden flex border border-slate-700/60 shadow-inner">
            {/* Democratic Seats */}
            <div
              style={{ width: `${(senate.expected_dem_seats / 100) * 100}%` }}
              className="h-full bg-gradient-to-r from-blue-700 to-blue-500 flex items-center justify-start pl-2 text-white font-mono font-bold text-xs"
            >
              {senate.expected_dem_seats.toFixed(1)} Dem
            </div>

            {/* Republican Seats */}
            <div
              style={{ width: `${(senate.expected_rep_seats / 100) * 100}%` }}
              className="h-full bg-gradient-to-r from-red-500 to-red-700 flex items-center justify-end pr-2 text-white font-mono font-bold text-xs"
            >
              {senate.expected_rep_seats.toFixed(1)} Rep
            </div>

            {/* 50 Seats Marker */}
            <div
              style={{ left: "50%" }}
              className="absolute top-0 bottom-0 w-0.5 bg-yellow-400 z-10 shadow-[0_0_8px_rgba(250,204,21,1)]"
            >
              <span className="absolute -top-5 -translate-x-1/2 text-[9px] font-mono font-bold text-yellow-300 bg-slate-950 px-1 rounded border border-yellow-500/50">
                50 Majority
              </span>
            </div>
          </div>

          {/* Probability & Interval Stats */}
          <div className="grid grid-cols-3 gap-2 pt-1 text-center font-mono">
            <div className="p-2 rounded-lg bg-blue-950/40 border border-blue-500/30">
              <div className="text-[10px] text-slate-400">Dem Majority</div>
              <div className="text-sm font-bold text-blue-400">
                {(senate.dem_control_prob * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-2 rounded-lg bg-surface-300/20 border border-surface-300/30">
              <div className="text-[10px] text-slate-400">80% Interval</div>
              <div className="text-xs font-bold text-white mt-0.5">
                [{senate.credible_interval_80[0]} - {senate.credible_interval_80[1]}]
              </div>
            </div>
            <div className="p-2 rounded-lg bg-red-950/40 border border-red-500/30">
              <div className="text-[10px] text-slate-400">Rep Majority</div>
              <div className="text-sm font-bold text-red-400">
                {(senate.rep_control_prob * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        {/* House Balance Bar */}
        <div className="bg-surface-200/40 border border-surface-300/30 rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              U.S. House of Representatives (435 Seats)
            </span>
            <span className="text-slate-400 font-mono">
              Threshold: <strong className="text-white">218 seats</strong> for majority
            </span>
          </div>

          {/* Bar Visual */}
          <div className="relative w-full h-8 bg-slate-900 rounded-lg overflow-hidden flex border border-slate-700/60 shadow-inner">
            {/* Democratic Seats */}
            <div
              style={{ width: `${(house.expected_dem_seats / 435) * 100}%` }}
              className="h-full bg-gradient-to-r from-blue-700 to-blue-500 flex items-center justify-start pl-2 text-white font-mono font-bold text-xs"
            >
              {house.expected_dem_seats.toFixed(1)} Dem
            </div>

            {/* Republican Seats */}
            <div
              style={{ width: `${(house.expected_rep_seats / 435) * 100}%` }}
              className="h-full bg-gradient-to-r from-red-500 to-red-700 flex items-center justify-end pr-2 text-white font-mono font-bold text-xs"
            >
              {house.expected_rep_seats.toFixed(1)} Rep
            </div>

            {/* 218 Seats Marker */}
            <div
              style={{ left: `${(218 / 435) * 100}%` }}
              className="absolute top-0 bottom-0 w-0.5 bg-yellow-400 z-10 shadow-[0_0_8px_rgba(250,204,21,1)]"
            >
              <span className="absolute -top-5 -translate-x-1/2 text-[9px] font-mono font-bold text-yellow-300 bg-slate-950 px-1 rounded border border-yellow-500/50">
                218 Majority
              </span>
            </div>
          </div>

          {/* Probability & Interval Stats */}
          <div className="grid grid-cols-3 gap-2 pt-1 text-center font-mono">
            <div className="p-2 rounded-lg bg-blue-950/40 border border-blue-500/30">
              <div className="text-[10px] text-slate-400">Dem Majority</div>
              <div className="text-sm font-bold text-blue-400">
                {(house.dem_control_prob * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-2 rounded-lg bg-surface-300/20 border border-surface-300/30">
              <div className="text-[10px] text-slate-400">80% Interval</div>
              <div className="text-xs font-bold text-white mt-0.5">
                [{house.credible_interval_80[0]} - {house.credible_interval_80[1]}]
              </div>
            </div>
            <div className="p-2 rounded-lg bg-red-950/40 border border-red-500/30">
              <div className="text-[10px] text-slate-400">Rep Majority</div>
              <div className="text-sm font-bold text-red-400">
                {(house.rep_control_prob * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
