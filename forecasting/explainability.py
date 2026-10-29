"""Pulse2026 Closed-Form Additive Feature Attribution Engine (Zero C++ SHAP Overhead)."""

import numpy as np


class ExplainabilityEngine:
    """Exact additive feature attribution engine for regularized linear meta-regressors."""

    def __init__(self, feature_names: list[str]):
        self.feature_names = feature_names

    def compute_attributions(
        self,
        coefficients: np.ndarray,
        feature_vector: np.ndarray,
        feature_means: np.ndarray,
    ) -> dict[str, float]:
        """Compute closed-form additive feature attributions phi_i = beta_i * (x_i - mean(x_i))."""
        attributions: dict[str, float] = {}
        for idx, name in enumerate(self.feature_names):
            if idx < len(coefficients) and idx < len(feature_vector) and idx < len(feature_means):
                beta_i = float(coefficients[idx])
                delta_x = float(feature_vector[idx] - feature_means[idx])
                phi_i = beta_i * delta_x
                attributions[name] = round(phi_i, 4)
            else:
                attributions[name] = 0.0
        return attributions

    def generate_narrative(
        self,
        predicted_margin: float,
        dem_win_prob: float,
        attributions: dict[str, float],
        mu_anchor: float,
        delta_residual: float,
    ) -> str:
        """Generate human-readable narrative explaining forecast drivers and social momentum."""
        leader = "Democratic" if predicted_margin > 0 else "Republican"
        abs_margin = abs(predicted_margin)

        top_positive = sorted(
            [(k, v) for k, v in attributions.items() if v > 0],
            key=lambda item: item[1],
            reverse=True,
        )
        top_negative = sorted(
            [(k, v) for k, v in attributions.items() if v < 0],
            key=lambda item: item[1],
        )

        pos_str = f"top positive driver: {top_positive[0][0]} (+{top_positive[0][1]:.2f}%)" if top_positive else "fundamentals neutral"
        neg_str = f"offset by {top_negative[0][0]} ({top_negative[0][1]:.2f}%)" if top_negative else "no downward drag"

        narrative = (
            f"Forecast expects a {leader} lead of {abs_margin:.1f}% ({dem_win_prob*100:.1f}% win probability). "
            f"Anchor margin is {mu_anchor:.2f}% with a {delta_residual:+.2f}% social media residual shift "
            f"({pos_str}, {neg_str})."
        )
        return narrative
