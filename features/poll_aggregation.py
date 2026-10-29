"""Pulse2026 Public Polling Aggregation Math."""

import math
from datetime import date
from typing import Any

from scipy.stats import t as student_t


def calculate_poll_weight(
    days_old: float,
    sample_size: int,
    pollster_rating: float = 1.0,
    population_type: str = "LV",
    half_life_days: float = 14.0,
    sample_size_cap: int = 3000,
    sample_size_denom: float = 1000.0,
) -> float:
    """Calculate exponential decay and quality weight for a single poll."""
    lambda_decay = math.log(2.0) / max(half_life_days, 1.0)
    time_decay = math.exp(-lambda_decay * max(days_old, 0.0))

    effective_sample = min(max(sample_size, 100), sample_size_cap)
    sample_scaling = math.sqrt(effective_sample / sample_size_denom)

    pop_multipliers = {"LV": 1.25, "RV": 1.00, "A": 0.75}
    pop_mult = pop_multipliers.get(population_type.upper(), 1.00)

    return float(time_decay * sample_scaling * pollster_rating * pop_mult)


def aggregate_polls(
    polls: list[dict[str, Any]],
    current_date: date | None = None,
    half_life_days: float = 14.0,
    student_t_df: int = 5,
    sigma_poll: float = 4.5,
) -> dict[str, float]:
    """Calculate weighted polling mean margin and Student-t win probability.

    Returns dict with:
    - weighted_dem_margin: mu_poll in percentage points
    - poll_win_prob: P_poll,r in [0.001, 0.999]
    - total_weight: sum of poll weights
    - poll_count: number of included polls
    """
    if not polls:
        return {
            "weighted_dem_margin": 0.0,
            "poll_win_prob": 0.50,
            "total_weight": 0.0,
            "poll_count": 0,
        }

    now_date = current_date or date.today()
    sum_weighted_margin = 0.0
    sum_weights = 0.0

    for p in polls:
        end_d = p.get("end_date")
        if isinstance(end_d, str):
            from datetime import datetime
            end_d = datetime.strptime(end_d, "%Y-%m-%d").date()

        days_old = max(0, (now_date - end_d).days) if end_d else 0
        w = calculate_poll_weight(
            days_old=days_old,
            sample_size=int(p.get("sample_size", 800)),
            pollster_rating=float(p.get("pollster_rating", 1.0)),
            population_type=str(p.get("population_type", "LV")),
            half_life_days=half_life_days,
        )

        margin = float(p.get("dem_pct", 50.0)) - float(p.get("rep_pct", 50.0))
        sum_weighted_margin += w * margin
        sum_weights += w

    if sum_weights <= 0:
        return {
            "weighted_dem_margin": 0.0,
            "poll_win_prob": 0.50,
            "total_weight": 0.0,
            "poll_count": len(polls),
        }

    mu_poll = sum_weighted_margin / sum_weights
    # Convert margin to win probability via Student-t CDF
    z = mu_poll / max(sigma_poll, 0.1)
    win_prob = float(student_t.cdf(z, df=student_t_df))
    # Clamp probability to prevent numerical extremes
    clamped_prob = min(max(win_prob, 0.001), 0.999)

    return {
        "weighted_dem_margin": round(float(mu_poll), 4),
        "poll_win_prob": round(float(clamped_prob), 4),
        "total_weight": round(float(sum_weights), 4),
        "poll_count": len(polls),
    }
