"""Pulse2026 Social Scoring & Feature Engineering Math."""

import math


def calculate_author_discount(post_count_7d: int) -> float:
    """Calculate diminishing returns discount factor for prolific authors."""
    count = max(1, post_count_7d)
    return 1.0 / math.sqrt(count)


def approximate_views_for_text(likes: int, comments: int, multiplier: float = 10.0) -> int:
    """Approximate passive audience views for text-based platforms (Reddit, Bluesky)."""
    return int(max(likes + comments, 1) * multiplier)


def calculate_calibrated_engagement_weight(
    platform: str,
    views: int,
    likes: int,
    comments: int,
    shares: int,
    author_post_count_7d: int = 1,
    platform_weights: dict[str, float] | None = None,
) -> float:
    """Compute platform-calibrated Engagement-Weighted Sentiment Score (EWSS) weight W_i*."""
    default_platform_weights = {
        "youtube": 0.85,
        "reddit": 0.50,
        "tiktok": 0.40,
        "bluesky": 0.60,
    }
    pw = platform_weights or default_platform_weights
    c_p = pw.get(platform.lower(), 0.50)

    # Text platform view proxy
    if platform.lower() in ("reddit", "bluesky") and views <= 0:
        eff_views = approximate_views_for_text(likes, comments)
    else:
        eff_views = max(views, 0)

    w_author = calculate_author_discount(author_post_count_7d)
    log_views = math.log(1.0 + eff_views)

    # Interaction resonance ratio
    weighted_interactions = likes + (2.0 * comments) + (3.0 * shares)
    resonance_ratio = weighted_interactions / max(float(eff_views), 100.0)

    return float(c_p * w_author * log_views * resonance_ratio)


def calculate_continuous_velocity_flux(
    delta_engagement: float,
    delta_hours: float,
) -> float:
    """Calculate continuous engagement velocity flux multiplier V_i."""
    if delta_hours <= 0:
        return 1.0
    flux = max(delta_engagement, 0.0) / max(delta_hours, 0.1)
    return float(1.0 + math.log(1.0 + flux))


def calculate_controversy_penalty(
    likes: int,
    comments: int,
    threshold: float = 0.25,
) -> float:
    """Calculate controversy ratio penalty rho_i in [0.5, 1.0]."""
    ratio = float(comments) / max(float(likes), 1.0)
    if ratio > threshold:
        return 0.5
    return 1.0


def calculate_candidate_net_social_score(
    mention_scores: list[dict[str, float]],
    lambda_prior: float = 50.0,
) -> float:
    """Calculate candidate net social score NSS_c,d with prior shrinkage.

    mention_scores is a list of dicts with:
    - weight: W_i*
    - velocity: V_i
    - controversy: rho_i
    - stance: S_stance in [-1.0, +1.0]
    """
    if not mention_scores:
        return 0.0

    numerator = 0.0
    denominator = 0.0

    for item in mention_scores:
        w = item.get("weight", 1.0)
        v = item.get("velocity", 1.0)
        rho = item.get("controversy", 1.0)
        s = item.get("stance", 0.0)

        effective_w = w * v
        numerator += effective_w * rho * s
        denominator += effective_w

    return float(numerator / (denominator + lambda_prior))


def calculate_partisan_differential(nss_dem: float, nss_rep: float) -> float:
    """Calculate candidate net social score differential."""
    return float(nss_dem - nss_rep)
