"use client";

import React from "react";
import { ArbitrageOpportunity } from "@/types";
import { AlertCircle, ArrowUpRight, DollarSign, Percent, ShieldCheck, Zap } from "lucide-react";

interface ArbitrageRadarProps {
  opportunities: ArbitrageOpportunity[];
  onSelectRaceId: (raceId: string) => void;
}

export const ArbitrageRadar: React.FC<ArbitrageRadarProps> = ({
  opportunities,
  onSelectRaceId,
}) => {
  return (
    <div className="bg-surface-100/90 border border-surface-300/40 rounded-2xl p-5 backdrop-blur-md shadow-2xl flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-surface-300/30 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-xl">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Kalshi Prediction Market Arbitrage Radar
            </h3>
            <p className="text-xs text-slate-400">
              Isolating structural retail mispricings with &ge; 8% model edge &amp; spread penalties applied
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-purple-300 bg-purple-500/10 px-2.5 py-1 rounded-full border border-purple-500/20">
            Divergence Threshold: &ge; 8.0%
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-surface-300/30 text-slate-400 font-mono text-[11px]">
              <th className="py-2.5 px-3">Ticker / Race</th>
              <th className="py-2.5 px-3">Contract Title</th>
              <th className="py-2.5 px-3 text-right">Kalshi Yes Price</th>
              <th className="py-2.5 px-3 text-right">Model Fair Value</th>
              <th className="py-2.5 px-3 text-right">Alpha Edge</th>
              <th className="py-2.5 px-3">Radar Status</th>
              <th className="py-2.5 px-3">Action Strategy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-300/20 font-mono">
            {opportunities.map((opp) => {
              const isAlert = opp.status === "ARBITRAGE_ALERT";
              return (
                <tr
                  key={opp.ticker}
                  onClick={() => onSelectRaceId(opp.race_id)}
                  className="hover:bg-surface-200/50 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-3">
                    <span className="font-bold text-white block">{opp.ticker}</span>
                    <span className="text-[10px] text-slate-400">{opp.state} &bull; {opp.chamber}</span>
                  </td>
                  <td className="py-3 px-3 font-sans text-slate-200 font-medium">
                    {opp.contract_title}
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-yellow-400">
                    {opp.kalshi_yes_price}&cent;
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-cyan-400">
                    {(opp.model_dem_prob * 100).toFixed(1)}&cent;
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-purple-300">
                    {opp.divergence_edge > 0 ? "+" : ""}
                    {opp.divergence_edge.toFixed(1)}%
                  </td>
                  <td className="py-3 px-3">
                    {isAlert ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">
                        <AlertCircle className="w-3 h-3" />
                        ARBITRAGE ALERT
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        <ShieldCheck className="w-3 h-3" />
                        MONITORING
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-sans text-[11px] text-slate-300">
                    <span className="font-semibold text-emerald-400">{opp.recommended_action}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
