export type Chamber = 'Senate' | 'House' | 'Governor';

export interface Candidate {
  name: string;
  party: 'DEM' | 'REP' | 'IND';
  incumbent?: boolean;
}

export interface FeatureAttribution {
  feature: string;
  label: string;
  contribution: number;
}

export interface RaceForecast {
  race_id: string;
  state: string;
  state_name: string;
  chamber: Chamber;
  district?: string;
  candidates: Candidate[];
  historical_lean: number; // Positive = Dem lean, Negative = Rep lean
  mu_poll: number; // Dem margin % in polls
  mu_kalshi: number; // Dem margin % implied by Kalshi
  liquidity_weight: number; // L_r [0, 1]
  mu_anchor: number; // Stage 1 anchor margin
  delta_social: number; // Raw social stance delta
  delta_residual: number; // Stage 2 regularized & bounded residual (within +-2.0%)
  predicted_dem_margin: number; // Final ensemble margin
  dem_win_prob: number; // Win probability [0, 1]
  rep_win_prob: number; // Win probability [0, 1]
  ci_lower_90: number; // 90% credible lower margin
  ci_upper_90: number; // 90% credible upper margin
  kalshi_ticker?: string;
  kalshi_price_cents?: number;
  arbitrage_edge?: number;
  arbitrage_status?: 'EQUILIBRIUM' | 'MONITORING' | 'ARBITRAGE_ALERT';
  attributions: FeatureAttribution[];
  last_updated?: string;
  status: 'pending' | 'processing' | 'finalized';
}

export interface PipelineStage {
  id: string;
  step_number: number;
  name: string;
  description: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  metric_summary?: string;
  logs: string[];
  duration_ms?: number;
}

export interface ChamberSimulation {
  dem_control_prob: number;
  rep_control_prob: number;
  expected_dem_seats: number;
  expected_rep_seats: number;
  threshold_majority: number;
  credible_interval_80: [number, number];
  safe_seats_dem: number;
  safe_seats_rep: number;
  contested_seats: number;
}

export interface MonteCarloSummary {
  senate: ChamberSimulation;
  house: ChamberSimulation;
  simulation_count: number;
}

export interface ArbitrageOpportunity {
  race_id: string;
  state: string;
  chamber: Chamber;
  ticker: string;
  contract_title: string;
  model_dem_prob: number;
  kalshi_implied_prob: number;
  kalshi_yes_price: number;
  kalshi_no_price: number;
  divergence_edge: number;
  status: 'ARBITRAGE_ALERT' | 'MONITORING';
  recommended_action: string;
  confidence: 'HIGH' | 'MEDIUM';
}
