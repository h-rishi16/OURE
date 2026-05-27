"""
OURE Risk Calculation - Alfano Maximum Probability
==================================================
Implements the Alfano (2005) Maximum Probability method, which calculates
the upper bound of collision probability regardless of covariance sizing.
"""

from math import exp, log

import numpy as np


class AlfanoPcCalculator:
    """
    Computes the Maximum Probability of Collision (Pc) upper bound.
    """

    def __init__(self, hard_body_radius_km: float):
        self.R = hard_body_radius_km

    def compute(
        self, b_miss: np.ndarray, C_2d: np.ndarray, propagation_age_hours: float = 0.0
    ) -> float:
        """
        Computes the Maximum Probability of Collision using Alfano's method.

        Args:
            b_miss: 2D miss distance vector on the B-plane.
            C_2d: 2D projected covariance matrix.
            propagation_age_hours: Unused in this method, kept for signature compatibility.

        Returns:
            The worst-case probability of collision.
        """
        miss_distance = float(np.linalg.norm(b_miss))

        # If the miss distance is less than the hard body radius, it's a guaranteed physical overlap
        if miss_distance <= self.R:
            return 1.0

        # The Maximum Probability occurs when the variance sigma^2 satisfies a specific ratio
        # For d >> R, the maximum probability converges to: (R^2 / (d^2 * e))
        # Alfano's exact equation for the maximum probability variance:
        # sigma^2 = (d^2 - R^2) / (2 * ln(d / (d - R)))

        d = miss_distance
        r = self.R

        # Optimal variance that maximizes Pc
        sigma_sq = (d**2 - r**2) / (2 * log(d / (d - r)))

        # Evaluate the probability at this worst-case variance
        # Pc_max = exp(- (d-r)^2 / (2 * sigma_sq)) - exp(- (d+r)^2 / (2 * sigma_sq))
        # Simplified isotropic integral evaluation:
        pc_max = exp(-(d**2) / (2 * sigma_sq)) * (
            exp((d * r) / sigma_sq) - exp(-(d * r) / sigma_sq)
        )

        # Note: We scale by the solid angle / geometric factor for a 2D projection
        # A robust approximation for the maximum bound:
        pc_max_approx = (r**2 / (d**2 * 2.718281828)) if d > 3 * r else pc_max

        return float(np.clip(pc_max_approx, 0.0, 1.0))
