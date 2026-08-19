"""
OURE Core - Shared Utility Functions
=====================================
Domain-agnostic utilities shared across CLI, API, and other boundaries.
These were originally private CLI helpers but are needed by multiple layers.
"""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime
from typing import Any

import numpy as np

from oure.core.models import CovarianceMatrix, StateVector

logger = logging.getLogger("oure.core.utils")


def tle_to_initial_state(tle: Any) -> StateVector:
    """Convert a TLE record to an initial StateVector via Keplerian elements."""
    from oure.core import constants
    from oure.physics.kepler import solve_kepler_vectorized

    n = tle.mean_motion_rev_per_day * constants.TWO_PI / constants.SECONDS_PER_DAY
    a = (
        (constants.MU_KM3_S2 / n**2) ** (1.0 / 3.0)
        if n > 0
        else constants.R_EARTH_KM + 400
    )

    e = tle.eccentricity
    i = math.radians(tle.inclination_deg)
    raan = math.radians(tle.raan_deg)
    omega = math.radians(tle.arg_perigee_deg)
    M = math.radians(tle.mean_anomaly_deg)

    # Solve Kepler for E
    E = float(solve_kepler_vectorized(np.array([M]), np.array([e]))[0])

    # True anomaly
    nu = 2 * math.atan2(
        math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2)
    )

    p = a * (1 - e**2)
    r_mag = p / (1 + e * math.cos(nu))

    # Perifocal coordinates
    r_pqw = r_mag * np.array([math.cos(nu), math.sin(nu), 0.0])
    v_pqw = math.sqrt(constants.MU_KM3_S2 / p) * np.array(
        [-math.sin(nu), e + math.cos(nu), 0.0]
    )

    # Rotation PQW -> ECI
    c_O, s_O = math.cos(raan), math.sin(raan)
    c_i, s_i = math.cos(i), math.sin(i)
    c_w, s_w = math.cos(omega), math.sin(omega)

    R = np.array(
        [
            [c_O * c_w - s_O * s_w * c_i, -c_O * s_w - s_O * c_w * c_i, s_O * s_i],
            [s_O * c_w + c_O * s_w * c_i, -s_O * s_w + c_O * c_w * c_i, -c_O * s_i],
            [s_w * s_i, c_w * s_i, c_i],
        ]
    )

    return StateVector(r=R @ r_pqw, v=R @ v_pqw, epoch=tle.epoch, sat_id=tle.sat_id)


def default_covariance(sat_id: str, sigma_km: float = 0.5) -> CovarianceMatrix:
    """Generate a default diagonal covariance matrix when no CDM is available."""
    logger.warning(
        f"No covariance for {sat_id} — using default {sigma_km} km sigma. "
        "Pc outputs may be inaccurate. Provide a CDM for calibrated results."
    )
    P = np.diag([sigma_km**2] * 3 + [1e-6] * 3)
    return CovarianceMatrix(matrix=P, epoch=datetime.now(UTC), sat_id=sat_id)
