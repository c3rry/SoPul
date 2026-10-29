"use client";

import React, { useState } from "react";
import { USMap } from "@/components/USMap";
import { PipelineController } from "@/components/PipelineController";
import { ChamberBalanceBar } from "@/components/ChamberBalanceBar";
import { RaceDetailDrawer } from "@/components/RaceDetailDrawer";
import { ArbitrageRadar } from "@/components/ArbitrageRadar";
import { INITIAL_ARBITRAGE, INITIAL_MONTE_CARLO, INITIAL_RACES } from "@/data/races";
import { Chamber, RaceForecast } from "@/types";
import {
  Activity,
  BarChart2,
  CheckCircle,
  Database,
  ExternalLink,
  Flame,
  Globe,
  Radio,
  ShieldCheck,
  TrendingUp,
  Zap,
} from "lucide-react";

export default function HomePage() {
  const [races, setRaces] = useState<RaceForecast[]>(INITIAL_RACES);
  const [selectedRace, setSelectedRace] = useState<RaceForecast | null>(INITIAL_RACES[0]); // Default GA
  const [activeChamber, setActiveChamber] = useState<Chamber | "All">("All");
  const [isPipelineRunning, setIsPipelineRunning] = useState<boolean>(false);
  const [monteCarlo, setMonteCarlo] = useState(INITIAL_MONTE_CARLO);
  const [arbitrageList, setArbitrageList] = useState(INITIAL_ARBITRAGE);

  const handlePipelineComplete = (updatedRaces: RaceForecast[]) => {
    setRaces(updatedRaces);
    // Update currently selected race if it exists
    if (selectedRace) {
      const match = updatedRaces.find((r) => r.race_id === selectedRace.race_id);
      if (match) setSelectedRace(match);
    }
  };

  const handleSelectRaceId = (raceId: string) => {
    const match = races.find((r) => r.race_id === raceId);
    if (match) {
      setSelectedRace(match);
      // Scroll smoothly to detail drawer on mobile
      const el = document.getElementById("race-detail-section");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-surface-300/30 px-4 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-blue-500/20 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold tracking-tight text-white">
                  Pulse2026 <span className="text-slate-500">/</span> SoPul
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  LIVE MODEL
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                2026 U.S. Midterms Multi-Modal Quantitative Forecasting Engine
              </p>
            </div>
          </div>

          {/* Model Status Metrics Pillbox */}
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <div className="px-3 py-1.5 rounded-lg bg-surface-200/50 border border-surface-300/40 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-slate-400">Latency:</span>
              <strong className="text-white">0.23s</strong>
            </div>

            <div className="px-3 py-1.5 rounded-lg bg-surface-200/50 border border-surface-300/40 flex items-center gap-2">
              <span className="text-slate-400">Cost:</span>
              <strong className="text-emerald-400">$0 API Spend</strong>
            </div>

            <div className="px-3 py-1.5 rounded-lg bg-surface-200/50 border border-surface-300/40 flex items-center gap-2">
              <span className="text-slate-400">Cap Bound:</span>
              <strong className="text-cyan-400">&plusmn;2.00% Max</strong>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="max-w-7xl mx-auto w-full p-4 lg:p-8 flex flex-col gap-6 flex-1">
        {/* Metric Quick-Cards Ribbon */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-surface-100/70 border border-surface-300/30 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Marquee Battlegrounds</span>
              <BarChart2 className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-xl font-bold font-mono text-white">7 Races Modeled</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Senate, House MI-07, TX-Gov</div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-100/70 border border-surface-300/30 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Public Polling Datasets</span>
              <Database className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-xl font-bold font-mono text-emerald-400">28 Datasets</div>
            <div className="text-[10px] text-slate-500 mt-0.5">14d exponential decay weighted</div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-100/70 border border-surface-300/30 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Monte Carlo Simulations</span>
              <Activity className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-xl font-bold font-mono text-amber-400">10,000 Draws</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Demographic covariance shocks</div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-100/70 border border-surface-300/30 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Arbitrage Alpha Detected</span>
              <Zap className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-xl font-bold font-mono text-purple-300">+8.5% Edge</div>
            <div className="text-[10px] text-slate-500 mt-0.5">KXGOVTX26 Texas Governor</div>
          </div>
        </div>

        {/* Pipeline Execution Controller */}
        <PipelineController
          onPipelineComplete={handlePipelineComplete}
          isPipelineRunning={isPipelineRunning}
          setIsPipelineRunning={setIsPipelineRunning}
        />

        {/* Center Grid: Interactive US Map & Race Detail Drawer */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          {/* Map Column (7 cols on XL) */}
          <div className="xl:col-span-7 flex flex-col gap-4">
            <USMap
              races={races}
              selectedRace={selectedRace}
              onSelectRace={(r) => setSelectedRace(r)}
              activeChamber={activeChamber}
              onSelectChamber={(c) => setActiveChamber(c)}
              isPipelineRunning={isPipelineRunning}
            />
          </div>

          {/* Race Detail Drawer Column (5 cols on XL) */}
          <div id="race-detail-section" className="xl:col-span-5 flex flex-col gap-4">
            {selectedRace ? (
              <RaceDetailDrawer
                race={selectedRace}
                onClose={() => setSelectedRace(null)}
              />
            ) : (
              <div className="bg-surface-100/80 border border-surface-300/40 rounded-2xl p-8 backdrop-blur-md text-center flex flex-col items-center justify-center min-h-[380px] text-slate-400">
                <Globe className="w-12 h-12 text-blue-500/50 mb-3 animate-pulse" />
                <h4 className="text-base font-bold text-white mb-1">Select a Battleground State</h4>
                <p className="text-xs max-w-xs leading-relaxed">
                  Click on any highlighted state on the map (Georgia, Michigan, North Carolina, Maine, Texas) to inspect two-stage attribution mechanics and prediction market mispricing.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* 10,000-Draw Chamber Balance of Power */}
        <ChamberBalanceBar monteCarlo={monteCarlo} />

        {/* Kalshi Prediction Market Arbitrage Radar */}
        <ArbitrageRadar
          opportunities={arbitrageList}
          onSelectRaceId={handleSelectRaceId}
        />
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-surface-300/30 bg-slate-950/90 py-6 px-4 lg:px-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>
              Pulse2026 Core Architectural Invariants: $0 Public Ingestion &bull; Ephemeral Memory &bull; SHA-256 Handle Anonymization &bull; [-2%, +2%] Social Residual Bound.
            </span>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>Built for Vercel Deployment</span>
            <span>&bull;</span>
            <span className="font-mono">v1.0.0-rc</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
