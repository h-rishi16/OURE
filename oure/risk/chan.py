"""
OURE Risk Calculation - Chan's Analytical Method
================================================
Implements Chan's analytical formulation for the probability of collision (Pc)
using an isotropic Rician approximation/infinite series, which is highly efficient
and avoids the need for numerical integration or Foster's approximations in many regimes.
"""

from __future__ import annotations

import logging
from math import exp

import numpy as np
from scipy.special import gammainc

from .foster import MonteCarloSampler, PcMethod

logger = logging.getLogger("oure.risk.chan")


class ChanPcCalculator:
    """
    Computes Probability of Collision (Pc) using Chan's method (1997).
    Converts the 2D Gaussian integral into an equivalent isotropic formulation
    expressed as an infinite series.
    """

    def __init__(
        self,
        hard_body_radius_km: float,
        series_terms: int = 10,
        use_mc_fallback: bool = True,
    ):
        self.R = hard_body_radius_km
        self.series_terms = series_terms
        self.use_mc_fallback = use_mc_fallback
        self.method = PcMethod.FOSTER_SERIES  # reusing enum for 'series' type methods

    def compute(
        self, b_miss: np.ndarray, C_2d: np.ndarray, propagation_age_hours: float = 0.0
    ) -> float:
        """
        Computes the Probability of Collision (Pc) using Chan's equivalent isotropic series.
        """
        miss_distance = np.linalg.norm(b_miss)
        if self.use_mc_fallback and (
            propagation_age_hours > 8.0 or miss_distance < 3.0 * self.R
        ):
            logger.debug("ChanPcCalculator: Using MONTE_CARLO fallback.")
            self.method = PcMethod.MONTE_CARLO
            return MonteCarloSampler.compute_pc(b_miss, C_2d, self.R)

        return self._chan_series(b_miss, C_2d)

    def _chan_series(self, b: np.ndarray, C: np.ndarray) -> float:
        """
        Chan's isotropic series expansion.
        """
        det_C = np.linalg.det(C)
        if det_C <= 1e-20:
            return 1.0 if np.linalg.norm(b) <= self.R else 0.0

        C_inv = np.linalg.pinv(C)

        # u = 1/2 * b^T * C^-1 * b
        u = 0.5 * float(b @ C_inv @ b)
        u = max(u, 1e-12)

        eigenvalues, _ = np.linalg.eigh(C)
        lam1, lam2 = sorted(np.abs(eigenvalues) + 1e-15)

        # Isotropic scale
        # v = R^2 / (2 * sqrt(det(C)))
        v = self.R**2 / (2 * np.sqrt(lam1 * lam2))

        # Guard against log(0) for extremely small covariances
        v_log = max(v, 1e-300)

        pc = 0.0
        for m in range(self.series_terms):
            from math import lgamma

            # log(v^m / m! * e^-v)
            log_weight = -v + m * np.log(v_log) - lgamma(m + 1)
            weight = exp(log_weight)

            gamma_term = gammainc(m + 1, u)
            pc += float(weight * gamma_term)

        return float(np.clip(pc, 0.0, 1.0))
