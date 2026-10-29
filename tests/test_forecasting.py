"""Pulse2026 Forecasting & Simulation Unit Tests."""

import numpy as np
import pytest

from forecasting.backtest import BacktestHarness
from forecasting.ensemble import EnsembleForecaster
from forecasting.explainability import ExplainabilityEngine


def test_anchor_margin_calculation():
    """Verify Stage 1 liquidity-weighted interpolation between polling and Kalshi margin."""
    forecaster = EnsembleForecaster()
    # High liquidity (0.80): Kalshi margin (+4.0) dominates poll (+1.0)
    mu_anchor = forecaster.compute_anchor_margin(mu_poll=1.0, mu_kalshi=4.0, liquidity_weight=0.80)
    assert pytest.approx(mu_anchor, 1e-4) == (0.80 * 4.0 + 0.20 * 1.0)  # 3.4

    # Zero liquidity (0.0): 100% polling
    mu_zero = forecaster.compute_anchor_margin(mu_poll=2.5, mu_kalshi=10.0, liquidity_weight=0.0)
    assert mu_zero == 2.5


def test_hard_margin_cap_enforcement():
    """Verify Stage 2 residual strictly satisfies |delta y| <= 2.00% regardless of input size."""
    forecaster = EnsembleForecaster(delta_max_margin=2.00)

    # Extreme positive input features
    x_high = np.array([5.0, 100.0, 50.0, 1.0, 0.20, 10.0, 1.0])
    res_high = forecaster.predict_residual(x_high)
    assert res_high <= 2.00

    # Extreme negative input features
    x_low = np.array([-5.0, -100.0, 50.0, 1.0, -0.20, 10.0, -1.0])
    res_low = forecaster.predict_residual(x_low)
    assert res_low >= -2.00


def test_point_forecast_and_confidence_intervals():
    """Verify forecast produces consistent bounds and 90% confidence intervals."""
    forecaster = EnsembleForecaster()
    fc = forecaster.predict_race_forecast(
        race_id="2026_SEN_GA",
        mu_poll=2.0,
        mu_kalshi=3.0,
        liquidity_weight=0.5,
        delta_social=0.5,
    )

    assert fc["race_id"] == "2026_SEN_GA"
    assert 0.0 < fc["dem_win_prob"] < 1.0
    assert pytest.approx(fc["dem_win_prob"] + fc["rep_win_prob"], 1e-4) == 1.0
    assert fc["ci_lower_90"] < fc["predicted_dem_margin"] < fc["ci_upper_90"]


def test_monte_carlo_chamber_simulation():
    """Verify Monte Carlo simulation incorporates safe seats and returns probabilities in [0, 1]."""
    forecaster = EnsembleForecaster()
    modeled_races = [
        {"race_id": "2026_SEN_GA", "chamber": "Senate", "predicted_dem_margin": 1.5},
        {"race_id": "2026_SEN_MI", "chamber": "Senate", "predicted_dem_margin": 2.5},
        {"race_id": "2026_HOUSE_MI_07", "chamber": "House", "predicted_dem_margin": 0.5},
    ]

    mc = forecaster.run_monte_carlo_simulation(
        modeled_races=modeled_races,
        num_runs=1000,
        safe_house_rep=195,
        safe_house_dem=185,
        safe_senate_rep=46,
        safe_senate_dem=44,
    )

    assert 0.0 <= mc["p_house_dem_majority"] <= 1.0
    assert 0.0 <= mc["p_senate_dem_majority"] <= 1.0
    assert mc["house_dem_seats_p10"] <= mc["house_dem_seats_mean"] <= mc["house_dem_seats_p90"]
    assert mc["senate_dem_seats_p10"] <= mc["senate_dem_seats_mean"] <= mc["senate_dem_seats_p90"]


def test_closed_form_feature_attribution_and_narrative():
    """Verify closed-form feature attribution and narrative generation."""
    feature_names = ["mu_anchor", "delta_social", "delta_v_flux"]
    engine = ExplainabilityEngine(feature_names=feature_names)

    coefs = np.array([1.0, 0.4, 0.1])
    x = np.array([2.5, 1.2, 0.5])
    means = np.array([2.0, 1.0, 0.5])

    attr = engine.compute_attributions(coefs, x, means)
    assert pytest.approx(attr["mu_anchor"], 1e-4) == 0.50
    assert pytest.approx(attr["delta_social"], 1e-4) == 0.08
    assert attr["delta_v_flux"] == 0.0

    narrative = engine.generate_narrative(
        predicted_margin=2.58,
        dem_win_prob=0.71,
        attributions=attr,
        mu_anchor=2.50,
        delta_residual=0.08,
    )
    assert "Democratic lead of 2.6%" in narrative
    assert "mu_anchor" in narrative


def test_backtest_brier_and_log_loss():
    """Verify Brier score and log-loss evaluation calculations."""
    harness = BacktestHarness()
    # Perfect forecast
    perfect_brier = harness.calculate_brier_score([1.0, 0.0], [1, 0])
    assert perfect_brier == 0.0

    # Uncertain forecast
    mid_brier = harness.calculate_brier_score([0.5, 0.5], [1, 0])
    assert mid_brier == 0.25

    # Log-loss
    loss = harness.calculate_log_loss([0.9, 0.1], [1, 0])
    assert loss < 0.20
