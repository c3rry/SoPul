"use client";

import React, { useState } from "react";
import { US_STATE_PATHS } from "@/data/us-map-paths";
import { BASELINE_STATE_LEANS } from "@/data/races";
import { Chamber, RaceForecast } from "@/types";
import { CheckCircle2, ChevronRight, Sparkles } from "lucide-react";

interface USMapProps {
  races: RaceForecast[];
  selectedRace: RaceForecast | null;
  onSelectRace: (race: RaceForecast | null) => void;
  activeChamber: Chamber | "All";
  onSelectChamber: (chamber: Chamber | "All") => void;
  isPipelineRunning: boolean;
}

export const USMap: React.FC<USMapProps> = ({
  races,
  selectedRace,
  onSelectRace,
  activeChamber,
  onSelectChamber,
  isPipelineRunning,
}) => {
  const [hoveredState, setHoveredState] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  // Map of battleground races by state abbreviation
  const racesByState = React.useMemo(() => {
    const map: Record<string, RaceForecast> = {};
    for (const r of races) {
      if (activeChamber === "All" || r.chamber === activeChamber) {
        map[r.state] = r;
      }
    }
    return map;
  }, [races, activeChamber]);

  const getStateColor = (abbr: string) => {
    const race = racesByState[abbr];
    if (race) {
      const margin = race.predicted_dem_margin;
      if (margin > 8.0) return "#1e40af"; // Deep blue
      if (margin > 2.0) return "#2563eb"; // Blue
      if (margin >= 0.0) return "#60a5fa"; // Lean blue
      if (margin >= -2.0) return "#f87171"; // Lean red
      if (margin >= -8.0) return "#dc2626"; // Red
      return "#991b1b"; // Deep red
    }

    // Fallback to baseline
    const baseline = BASELINE_STATE_LEANS[abbr];
    if (baseline) {
      const margin = baseline.margin;
      if (margin > 12.0) return "#1e3a8a"; // Safe blue
      if (margin > 3.0) return "#2563eb";
      if (margin >= 0.0) return "#93c5fd";
      if (margin >= -3.0) return "#fca5a5";
      if (margin >= -12.0) return "#dc2626";
      return "#7f1d1d"; // Safe red
    }

    return "#334155"; // Neutral gray
  };

  const getHoveredInfo = () => {
    if (!hoveredState) return null;
    const race = racesByState[hoveredState];
    const baseline = BASELINE_STATE_LEANS[hoveredState];
    return { race, baseline };
  };

  const hoveredInfo = getHoveredInfo();

  // Small East Coast state shortcuts for easy clicking
  const eastCoastShortcuts = [
    { abbr: "ME", name: "Maine", isBattleground: true },
    { abbr: "NH", name: "New Hampshire", isBattleground: false },
    { abbr: "VT", name: "Vermont", isBattleground: false },
    { abbr: "MA", name: "Massachusetts", isBattleground: false },
    { abbr: "RI", name: "Rhode Island", isBattleground: false },
    { abbr: "CT", name: "Connecticut", isBattleground: false },
    { abbr: "NJ", name: "New Jersey", isBattleground: false },
    { abbr: "DE", name: "Delaware", isBattleground: false },
    { abbr: "MD", name: "Maryland", isBattleground: false },
  ];

  return (
    <div className="relative bg-surface-100/90 border border-surface-300/40 rounded-2xl p-4 md:p-6 backdrop-blur-md shadow-2xl flex flex-col">
      {/* Map Header and Chamber Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-4 border-b border-surface-300/30">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              2026 Interactive Battleground Map
            </h2>
            {isPipelineRunning && (
              <span className="px-2 py-0.5 text-xs font-mono bg-blue-500/20 text-blue-300 border border-blue-500/40 rounded-full animate-pulse">
                Live Re-Computing...
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Stage 1 Polling Anchor + Stage 2 DeBERTa Bounded Residuals ($\pm 2.0\%$). Click any battleground state to inspect attribution mechanics.
          </p>
        </div>

        {/* Chamber Selector Tabs */}
        <div className="flex items-center bg-surface-200/80 p-1 rounded-xl border border-surface-300/50">
          {(["All", "Senate", "House", "Governor"] as const).map((ch) => (
            <button
              key={ch}
              onClick={() => onSelectChamber(ch)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeChamber === ch
                  ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                  : "text-slate-400 hover:text-white hover:bg-surface-300/30"
              }`}
            >
              {ch}
            </button>
          ))}
        </div>
      </div>

      {/* Probability / Lean Legend */}
      <div className="flex items-center justify-between text-xs text-slate-400 mb-3 px-2">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-[#1e40af] border border-blue-400/30 inline-block" />
          <span className="font-mono">Solid Dem (&gt;70%)</span>
          <span className="w-3 h-3 rounded-sm bg-[#2563eb] border border-blue-400/30 inline-block ml-2" />
          <span className="font-mono">Lean Dem</span>
          <span className="w-3 h-3 rounded-sm bg-[#60a5fa] border border-blue-400/30 inline-block ml-2" />
          <span className="font-mono">Tilt Dem</span>
        </div>
        <div className="flex items-center gap-1.5 font-semibold text-yellow-400/90">
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 animate-ping inline-block" />
          <span>Glow = Key 2026 Battleground</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-[#f87171] border border-red-400/30 inline-block" />
          <span className="font-mono">Tilt Rep</span>
          <span className="w-3 h-3 rounded-sm bg-[#dc2626] border border-red-400/30 inline-block ml-2" />
          <span className="font-mono">Lean Rep</span>
          <span className="w-3 h-3 rounded-sm bg-[#991b1b] border border-red-400/30 inline-block ml-2" />
          <span className="font-mono">Solid Rep (&gt;70%)</span>
        </div>
      </div>

      {/* SVG Map Container */}
      <div
        className="relative w-full aspect-[960/600] max-h-[580px] bg-slate-950/60 rounded-xl border border-surface-300/30 p-2 overflow-hidden flex items-center justify-center"
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          setTooltipPos({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
          });
        }}
        onMouseLeave={() => {
          setHoveredState(null);
          setTooltipPos(null);
        }}
      >
        <svg
          viewBox="0 0 960 600"
          className="w-full h-full object-contain filter drop-shadow-md select-none"
        >
          <g>
            {US_STATE_PATHS.map((state) => {
              const isSelected = selectedRace?.state === state.abbr;
              const race = racesByState[state.abbr];
              const isBattleground = Boolean(race);
              const isHovered = hoveredState === state.abbr;
              const fillColor = getStateColor(state.abbr);

              return (
                <g key={state.abbr}>
                  <path
                    d={state.d}
                    fill={fillColor}
                    stroke={
                      isSelected
                        ? "#facc15"
                        : isHovered
                        ? "#ffffff"
                        : isBattleground
                        ? "#38bdf8"
                        : "#0f172a"
                    }
                    strokeWidth={isSelected ? 2.5 : isHovered ? 2.0 : isBattleground ? 1.5 : 0.6}
                    strokeLinejoin="round"
                    className={`transition-all duration-200 cursor-pointer ${
                      isBattleground ? "glow-active hover:opacity-95" : "hover:opacity-85"
                    }`}
                    onClick={() => {
                      if (race) {
                        onSelectRace(race);
                      }
                    }}
                    onMouseEnter={() => setHoveredState(state.abbr)}
                  />
                  {/* State Abbreviation Centroid Labels */}
                  {state.cx && state.cy && state.abbr !== "DC" && (
                    <text
                      x={state.cx}
                      y={state.cy}
                      textAnchor="middle"
                      dominantBaseline="central"
                      className={`text-[9px] font-bold pointer-events-none select-none transition-colors ${
                        isBattleground
                          ? "fill-white font-black drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]"
                          : "fill-slate-300/80 drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]"
                      }`}
                    >
                      {state.abbr}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>

        {/* Floating Tooltip */}
        {hoveredState && tooltipPos && (
          <div
            className="absolute z-30 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-3 bg-slate-900/95 border border-slate-700/80 rounded-xl p-3 shadow-2xl backdrop-blur-md min-w-[220px]"
            style={{
              left: `${Math.max(120, Math.min(tooltipPos.x, 840))}px`,
              top: `${Math.max(80, tooltipPos.y - 10)}px`,
            }}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2">
              <span className="font-bold text-white text-sm">
                {US_STATE_PATHS.find((s) => s.abbr === hoveredState)?.name || hoveredState} ({hoveredState})
              </span>
              {hoveredInfo?.race ? (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  {hoveredInfo.race.chamber.toUpperCase()} TOSS-UP
                </span>
              ) : (
                <span className="text-[10px] text-slate-400 font-mono">
                  {hoveredInfo?.baseline?.chamber_status || "Baseline"}
                </span>
              )}
            </div>

            {hoveredInfo?.race ? (
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-blue-400 font-medium">
                    {hoveredInfo.race.candidates.find((c) => c.party === "DEM")?.name || "Democrat"}
                  </span>
                  <span className="font-mono font-bold text-blue-300">
                    {(hoveredInfo.race.dem_win_prob * 100).toFixed(1)}% win
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-red-400 font-medium">
                    {hoveredInfo.race.candidates.find((c) => c.party === "REP")?.name || "Republican"}
                  </span>
                  <span className="font-mono font-bold text-red-300">
                    {(hoveredInfo.race.rep_win_prob * 100).toFixed(1)}% win
                  </span>
                </div>
                <div className="pt-1.5 border-t border-slate-800/80 flex justify-between text-[11px]">
                  <span className="text-slate-400">Projected Margin:</span>
                  <span
                    className={`font-mono font-bold ${
                      hoveredInfo.race.predicted_dem_margin >= 0 ? "text-blue-400" : "text-red-400"
                    }`}
                  >
                    {hoveredInfo.race.predicted_dem_margin >= 0 ? "+" : ""}
                    {hoveredInfo.race.predicted_dem_margin.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>Social Residual:</span>
                  <span className="text-cyan-400">
                    {hoveredInfo.race.delta_residual >= 0 ? "+" : ""}
                    {hoveredInfo.race.delta_residual.toFixed(2)}%
                  </span>
                </div>
                <p className="text-[10px] text-amber-300/90 pt-1 text-center font-medium">
                  Click to open feature attribution & arbitrage card
                </p>
              </div>
            ) : (
              <div className="text-xs text-slate-300 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-400">Baseline Margin:</span>
                  <span
                    className={`font-mono font-semibold ${
                      (hoveredInfo?.baseline?.margin || 0) >= 0 ? "text-blue-400" : "text-red-400"
                    }`}
                  >
                    {(hoveredInfo?.baseline?.margin || 0) >= 0 ? "+" : ""}
                    {hoveredInfo?.baseline?.margin.toFixed(1)}%
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 italic">Non-competitive regular seat</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* East Coast Micro-State Bar (High usability for small states) */}
      <div className="mt-4 pt-3 border-t border-surface-300/30 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-400 text-[11px] font-semibold uppercase tracking-wider">
          New England & Mid-Atlantic Quick Select:
        </span>
        {eastCoastShortcuts.map((st) => {
          const race = racesByState[st.abbr];
          const isSelected = selectedRace?.state === st.abbr;
          return (
            <button
              key={st.abbr}
              onClick={() => {
                if (race) onSelectRace(race);
                else setHoveredState(st.abbr);
              }}
              className={`px-2.5 py-1 rounded-md text-xs font-mono font-semibold transition-all border ${
                isSelected
                  ? "bg-amber-400 text-slate-950 border-amber-300 shadow-md scale-105"
                  : st.isBattleground
                  ? "bg-blue-600/30 text-blue-200 border-blue-500/50 hover:bg-blue-600/50"
                  : "bg-surface-200/60 text-slate-300 border-surface-300/40 hover:bg-surface-300/40"
              }`}
            >
              {st.abbr}
              {st.isBattleground && " ★"}
            </button>
          );
        })}
      </div>
    </div>
  );
};
