"""Pulse2026 Quantitative Feature Engineering Package."""

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
    calculate_candidate_net_social_score,
    calculate_continuous_velocity_flux,
    calculate_controversy_penalty,
    calculate_partisan_differential,
)

__all__ = [
    "aggregate_polls",
    "approximate_views_for_text",
    "calculate_author_discount",
    "calculate_calibrated_engagement_weight",
    "calculate_candidate_net_social_score",
    "calculate_continuous_velocity_flux",
    "calculate_controversy_penalty",
    "calculate_kalshi_price_and_margin",
    "calculate_partisan_differential",
    "calculate_poll_weight",
    "calculate_sigmoid_liquidity_weight",
    "evaluate_arbitrage_divergence",
]
