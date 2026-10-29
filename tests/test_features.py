"""Pulse2026 Quantitative Feature Engineering Unit Tests."""

from datetime import date

import pytest

from features.kalshi_pricing import (
    calculate_kalshi_price_and_margin,
    calculate_sigmoid_liquidity_weight,
    evaluate_arbitrage_divergence,
)
from features.poll_aggregation import aggregate_polls, calculate_poll_weight
from features.social_scoring import (
    approximate_views_for_text,
    calculate_author_discount,
    calculate_calibrated_engagement_weight,
    calculate_continuous_velocity_flux,
)


def test_author_diminishing_returns():
    """Verify author discount scales inversely with square root of post count."""
    assert calculate_author_discount(1) == 1.0
    assert pytest.approx(calculate_author_discount(4), 1e-4) == 0.50
    assert pytest.approx(calculate_author_discount(16), 1e-4) == 0.25


def test_text_platform_view_proxy():
    """Verify text networks (Reddit/Bluesky) calculate view proxy from interactions."""
    assert approximate_views_for_text(likes=20, comments=5, multiplier=10.0) == 250
    # Zero interaction fallback
    assert approximate_views_for_text(likes=0, comments=0, multiplier=10.0) == 10


def test_ewss_platform_calibration():
    """Verify platform weights discount youth-skewed platforms relative to YouTube."""
    yt_weight = calculate_calibrated_engagement_weight(
        platform="youtube", views=1000, likes=50, comments=10, shares=5
    )
    tt_weight = calculate_calibrated_engagement_weight(
        platform="tiktok", views=1000, likes=50, comments=10, shares=5
    )
    # YouTube (C_p=0.85) should be weighted higher than TikTok (C_p=0.40)
    assert yt_weight > tt_weight
    assert pytest.approx(yt_weight / tt_weight, 1e-2) == (0.85 / 0.40)


def test_continuous_velocity_flux():
    """Verify continuous velocity flux calculation."""
    # Zero hours elapsed defaults to 1.0
    assert calculate_continuous_velocity_flux(delta_engagement=100, delta_hours=0) == 1.0
    # Positive flux increases multiplier
    v = calculate_continuous_velocity_flux(delta_engagement=500, delta_hours=10)
    assert v > 1.0


def test_poll_exponential_decay():
    """Verify 14-day half-life halves poll weight exactly after 14 days."""
    w0 = calculate_poll_weight(days_old=0, sample_size=1000, pollster_rating=1.0)
    w14 = calculate_poll_weight(days_old=14, sample_size=1000, pollster_rating=1.0)
    assert pytest.approx(w14 / w0, 1e-4) == 0.50


def test_poll_aggregation_and_student_t_probability():
    """Verify weighted margin calculation and symmetric win probability conversion."""
    polls = [
        {"poll_id": "p1", "sample_size": 1000, "dem_pct": 52.0, "rep_pct": 48.0, "end_date": "2026-10-01"},
        {"poll_id": "p2", "sample_size": 1000, "dem_pct": 50.0, "rep_pct": 50.0, "end_date": "2026-10-01"},
    ]
    res = aggregate_polls(polls, current_date=date(2026, 10, 1))
    assert pytest.approx(res["weighted_dem_margin"], 1e-2) == 2.0
    # Dem margin +2.0 should yield win prob > 0.50
    assert res["poll_win_prob"] > 0.50


def test_kalshi_pricing_liquid_vs_spread_penalty():
    """Verify liquid markets use VWAP and illiquid markets penalize wide spreads."""
    # Liquid market (>500 contracts)
    liquid = calculate_kalshi_price_and_margin(
        yes_bid=52, yes_ask=54, volume_24h=1200, vwap_24h=53.0
    )
    assert liquid["spread_penalty_applied"] == 0.0
    assert liquid["implied_prob"] == 0.53

    # Illiquid market (<=500 contracts) with wide spread (40 to 60)
    illiquid = calculate_kalshi_price_and_margin(
        yes_bid=40, yes_ask=60, volume_24h=100, vwap_24h=50.0, spread_penalty_gamma=0.5
    )
    assert illiquid["spread_penalty_applied"] == 1.0
    # Mid = 0.50, spread = 0.20, penalty = 0.5 * 0.2 = 0.1, result = 0.50 * 0.90 = 0.45
    assert pytest.approx(illiquid["implied_prob"], 1e-2) == 0.45


def test_kalshi_sigmoid_liquidity():
    """Verify sigmoid inflection: volume ~5000 yields L_r ~ 0.50."""
    l_r = calculate_sigmoid_liquidity_weight(volume_24h=2500, open_interest=2500, tau_contracts=5000.0)
    assert pytest.approx(l_r, 1e-2) == 0.50
    # Zero volume approaches 0.0
    l_zero = calculate_sigmoid_liquidity_weight(volume_24h=0, open_interest=0, tau_contracts=5000.0)
    assert l_zero < 0.01


def test_arbitrage_radar_and_volume_freeze_guard():
    """Verify arbitrage detection and freeze guard on volume surges."""
    # Mispricing without volume surge -> Alert
    alert_res = evaluate_arbitrage_divergence(
        model_win_prob=0.62,
        kalshi_win_prob=0.50,  # 12% divergence
        liquidity_weight=0.60,
        hourly_volume=100,
        volume_24h_ma=100,
        threshold=0.08,
    )
    assert alert_res["alert"] is True
    assert alert_res["status"] == "ARBITRAGE_ALERT"

    # Same mispricing during 4x volume surge -> Frozen
    frozen_res = evaluate_arbitrage_divergence(
        model_win_prob=0.62,
        kalshi_win_prob=0.50,
        liquidity_weight=0.60,
        hourly_volume=450,
        volume_24h_ma=100,  # 4.5x surge
        threshold=0.08,
        volume_surge_ratio=3.0,
    )
    assert frozen_res["alert"] is False
    assert frozen_res["status"] == "UNCONFIRMED_VOLATILITY"
