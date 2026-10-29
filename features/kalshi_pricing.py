"""Pulse2026 Kalshi Market Pricing, Sigmoid Liquidity & Spread Penalties."""

import math
from typing import Any

from scipy.stats import t as student_t


def calculate_kalshi_price_and_margin(
    yes_bid: int,
    yes_ask: int,
    volume_24h: int,
    vwap_24h: float,
    min_volume_threshold: int = 500,
    spread_penalty_gamma: float = 0.5,
    sigma_poll: float = 4.5,
    student_t_df: int = 5,
    epsilon: float = 0.001,
) -> dict[str, float]:
    """Calculate implied win probability and inverted margin from Kalshi contracts.

    Returns dict with:
    - implied_prob: P_kalshi,r in [epsilon, 1 - epsilon]
    - implied_margin: mu_kalshi in percentage points
    - spread_penalty_applied: boolean (1.0 or 0.0)
    """
    bid = max(0, min(100, yes_bid))
    ask = max(bid, min(100, yes_ask))
    spread = (ask - bid) / 100.0

    if volume_24h > min_volume_threshold:
        # Liquid contract uses 24h VWAP
        raw_prob = vwap_24h / 100.0
        penalty_applied = 0.0
    else:
        # Illiquid contract uses mid-market price with spread penalty
        mid_prob = (bid + ask) / 200.0
        raw_prob = mid_prob * (1.0 - (spread_penalty_gamma * spread))
        penalty_applied = 1.0

    # Numerical clamping to avoid inf in ppf
    clamped_prob = min(max(raw_prob, epsilon), 1.0 - epsilon)

    # Invert Student-t CDF to derive implied vote margin percentage
    z = float(student_t.ppf(clamped_prob, df=student_t_df))
    implied_margin = z * sigma_poll

    return {
        "implied_prob": round(float(clamped_prob), 4),
        "implied_margin": round(float(implied_margin), 4),
        "spread_penalty_applied": penalty_applied,
    }


def calculate_sigmoid_liquidity_weight(
    volume_24h: int,
    open_interest: int,
    tau_contracts: float = 5000.0,
    k: float = 1.2,
) -> float:
    """Compute sigmoid liquidity confidence weight L_r,t in [0.0, 1.0]."""
    total_market_flux = max(volume_24h + open_interest, 0)
    log_flux = math.log(1.0 + total_market_flux)
    log_tau = math.log(tau_contracts)

    exponent = -k * (log_flux - log_tau)
    # Numerical stability check for exp
    if exponent > 50.0:
        return 0.0
    elif exponent < -50.0:
        return 1.0

    l_r = 1.0 / (1.0 + math.exp(exponent))
    return round(float(l_r), 4)


def evaluate_arbitrage_divergence(
    model_win_prob: float,
    kalshi_win_prob: float,
    liquidity_weight: float,
    hourly_volume: int | None = None,
    volume_24h_ma: float | None = None,
    threshold: float = 0.08,
    min_liquidity: float = 0.40,
    volume_surge_ratio: float = 3.0,
) -> dict[str, Any]:
    """Evaluate 3-to-7 day positional arbitrage opportunity with volume freeze guards.

    Returns dict with divergence, alert flag, and status code.
    """
    delta_arb = model_win_prob - kalshi_win_prob
    abs_delta = abs(delta_arb)

    is_mispriced = (abs_delta >= threshold) and (liquidity_weight >= min_liquidity)

    # Check volume surge freeze guard
    volume_surge = False
    if hourly_volume is not None and volume_24h_ma is not None and volume_24h_ma > 0:
        if hourly_volume >= (volume_surge_ratio * volume_24h_ma):
            volume_surge = True

    status = "NOMINAL"
    if volume_surge:
        status = "UNCONFIRMED_VOLATILITY"
        alert = False
    elif is_mispriced:
        status = "ARBITRAGE_ALERT"
        alert = True
    else:
        alert = False

    return {
        "delta_arb": round(float(delta_arb), 4),
        "abs_delta": round(float(abs_delta), 4),
        "is_mispriced": is_mispriced,
        "volume_surge": volume_surge,
        "alert": alert,
        "status": status,
    }
