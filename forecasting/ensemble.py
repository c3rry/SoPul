"""Pulse2026 Two-Stage Margin Ensemble & Correlated Monte Carlo Simulator."""

import math
from typing import Any

import numpy as np
from scipy.stats import t as student_t
from sklearn.linear_model import ElasticNet


class EnsembleForecaster:
    """Two-stage margin ensemble model with hard residual bound and Monte Carlo simulation."""

    def __init__(
        self,
        delta_max_margin: float = 2.00,
        sigma_race_total: float = 4.60,
        student_t_df: int = 5,
        elasticnet_alpha: float = 0.1,
        elasticnet_l1_ratio: float = 0.5,
    ):
        self.delta_max_margin = delta_max_margin
        self.sigma_race_total = sigma_race_total
        self.student_t_df = student_t_df
        self.meta_regressor = ElasticNet(
            alpha=elasticnet_alpha,
            l1_ratio=elasticnet_l1_ratio,
            random_state=42,
        )
        self.is_fitted = False
        self.feature_means = np.zeros(7)
        self.feature_names = [
            "mu_anchor",
            "delta_social",
            "delta_v_flux",
            "var_ideo",
            "kalshi_trend_7d",
            "days_to_election",
            "incumbent",
        ]

    def compute_anchor_margin(
        self,
        mu_poll: float,
        mu_kalshi: float,
        liquidity_weight: float,
    ) -> float:
        """Stage 1: Liquidity-adjusted anchor margin fusion."""
        l_r = min(max(liquidity_weight, 0.0), 1.0)
        return float((l_r * mu_kalshi) + ((1.0 - l_r) * mu_poll))

    def fit_meta_regressor(self, X: np.ndarray, y_residuals: np.ndarray) -> None:
        """Fit Stage 2 ElasticNet meta-regressor on historical or synthetic feature matrix."""
        if len(X) == 0:
            return
        self.meta_regressor.fit(X, y_residuals)
        self.feature_means = np.mean(X, axis=0)
        self.is_fitted = True

    def predict_residual(self, x: np.ndarray) -> float:
        """Compute Stage 2 bounded residual with tanh compression."""
        if not self.is_fitted:
            # Fallback prior: mild social impact proportional to delta_social
            raw_pred = 0.15 * x[1]
        else:
            raw_pred = float(self.meta_regressor.predict(x.reshape(1, -1))[0])

        # Enforce strict hard margin cap: |delta y| <= delta_max_margin
        scaled = raw_pred / self.delta_max_margin
        bounded_residual = self.delta_max_margin * math.tanh(scaled)
        return float(bounded_residual)

    def predict_race_forecast(
        self,
        race_id: str,
        mu_poll: float,
        mu_kalshi: float,
        liquidity_weight: float,
        delta_social: float = 0.0,
        delta_v_flux: float = 0.0,
        var_ideo: float = 0.25,
        kalshi_trend_7d: float = 0.0,
        days_to_election: float = 180.0,
        incumbent: float = 0.0,
    ) -> dict[str, Any]:
        """Produce point forecast, margins, confidence intervals, and win probabilities."""
        mu_anchor = self.compute_anchor_margin(mu_poll, mu_kalshi, liquidity_weight)

        x = np.array([
            mu_anchor,
            delta_social,
            delta_v_flux,
            var_ideo,
            kalshi_trend_7d,
            days_to_election,
            incumbent,
        ])

        delta_residual = self.predict_residual(x)
        predicted_dem_margin = mu_anchor + delta_residual

        # Win probability derived via calibrated Student-t CDF
        z = predicted_dem_margin / max(self.sigma_race_total, 0.1)
        dem_win_prob = float(student_t.cdf(z, df=self.student_t_df))
        dem_win_prob = min(max(dem_win_prob, 0.001), 0.999)
        rep_win_prob = 1.0 - dem_win_prob

        # 90% confidence interval (5th to 95th percentile)
        z_90 = float(student_t.ppf(0.95, df=self.student_t_df))
        ci_half_width = z_90 * self.sigma_race_total
        ci_lower_90 = predicted_dem_margin - ci_half_width
        ci_upper_90 = predicted_dem_margin + ci_half_width

        return {
            "race_id": race_id,
            "mu_anchor": round(mu_anchor, 4),
            "delta_residual": round(delta_residual, 4),
            "predicted_dem_margin": round(predicted_dem_margin, 4),
            "dem_win_prob": round(dem_win_prob, 4),
            "rep_win_prob": round(rep_win_prob, 4),
            "ci_lower_90": round(ci_lower_90, 4),
            "ci_upper_90": round(ci_upper_90, 4),
            "features": x,
        }

    def run_monte_carlo_simulation(
        self,
        modeled_races: list[dict[str, Any]],
        num_runs: int = 10000,
        national_sigma: float = 0.035,
        safe_house_rep: int = 195,
        safe_house_dem: int = 185,
        safe_senate_rep: int = 46,
        safe_senate_dem: int = 44,
    ) -> dict[str, Any]:
        """Execute correlated Monte Carlo draws combining battlegrounds with safe-seat baselines."""
        n_races = len(modeled_races)
        if n_races == 0:
            return {}

        np.random.seed(42)
        # Shared national generic political error
        national_shocks = np.random.normal(0, national_sigma, size=num_runs)

        house_dem_seats = np.zeros(num_runs) + safe_house_dem
        senate_dem_seats = np.zeros(num_runs) + safe_senate_dem

        race_sim_dem_wins = {r["race_id"]: 0 for r in modeled_races}

        for r in modeled_races:
            base_margin = r.get("predicted_dem_margin", 0.0) / 100.0  # convert to decimal
            chamber = r.get("chamber", "Senate")

            # Independent race error + shared national shock
            race_shocks = np.random.normal(0, 0.045, size=num_runs)
            simulated_margins = base_margin + national_shocks + race_shocks
            dem_wins = simulated_margins > 0

            race_sim_dem_wins[r["race_id"]] = int(np.sum(dem_wins))

            if chamber.lower() == "house":
                house_dem_seats += dem_wins.astype(int)
            elif chamber.lower() == "senate":
                senate_dem_seats += dem_wins.astype(int)

        p_house_majority = float(np.mean(house_dem_seats >= 218))
        p_senate_majority = float(np.mean(senate_dem_seats >= 50))

        return {
            "num_runs": num_runs,
            "p_house_dem_majority": round(p_house_majority, 4),
            "p_senate_dem_majority": round(p_senate_majority, 4),
            "house_dem_seats_mean": round(float(np.mean(house_dem_seats)), 1),
            "house_dem_seats_p10": int(np.percentile(house_dem_seats, 10)),
            "house_dem_seats_p90": int(np.percentile(house_dem_seats, 90)),
            "senate_dem_seats_mean": round(float(np.mean(senate_dem_seats)), 1),
            "senate_dem_seats_p10": int(np.percentile(senate_dem_seats, 10)),
            "senate_dem_seats_p90": int(np.percentile(senate_dem_seats, 90)),
        }
