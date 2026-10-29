"""Pulse2026 Historical Backtesting & Calibration Assessment Harness."""

from typing import Any

import numpy as np


class BacktestHarness:
    """Historical cross-validation and calibration evaluator for probabilistic forecasts."""

    @staticmethod
    def calculate_brier_score(predictions: list[float], outcomes: list[int]) -> float:
        """Calculate Brier score: mean squared error between probability and binary outcome."""
        if not predictions or len(predictions) != len(outcomes):
            return 0.0
        preds = np.array(predictions)
        outs = np.array(outcomes)
        return float(np.mean((preds - outs) ** 2))

    @staticmethod
    def calculate_log_loss(predictions: list[float], outcomes: list[int], eps: float = 1e-15) -> float:
        """Calculate binary cross-entropy log-loss with numerical clipping."""
        if not predictions or len(predictions) != len(outcomes):
            return 0.0
        preds = np.clip(np.array(predictions), eps, 1.0 - eps)
        outs = np.array(outcomes)
        losses = - (outs * np.log(preds) + (1.0 - outs) * np.log(1.0 - preds))
        return float(np.mean(losses))

    @staticmethod
    def generate_calibration_curve(
        predictions: list[float],
        outcomes: list[int],
        num_bins: int = 5,
    ) -> list[dict[str, Any]]:
        """Compute reliability diagram bins: mean predicted vs. empirical observed win rate."""
        if not predictions:
            return []

        preds = np.array(predictions)
        outs = np.array(outcomes)
        bin_edges = np.linspace(0.0, 1.0, num_bins + 1)
        calibration_bins: list[dict[str, Any]] = []

        for i in range(num_bins):
            lower = bin_edges[i]
            upper = bin_edges[i + 1]
            if i == num_bins - 1:
                mask = (preds >= lower) & (preds <= upper)
            else:
                mask = (preds >= lower) & (preds < upper)

            bin_preds = preds[mask]
            bin_outs = outs[mask]

            count = len(bin_preds)
            mean_pred = float(np.mean(bin_preds)) if count > 0 else (lower + upper) / 2.0
            observed_rate = float(np.mean(bin_outs)) if count > 0 else 0.0

            calibration_bins.append({
                "bin_range": f"[{lower:.1f}, {upper:.1f})",
                "count": count,
                "mean_predicted": round(mean_pred, 4),
                "observed_win_rate": round(observed_rate, 4),
            })

        return calibration_bins
