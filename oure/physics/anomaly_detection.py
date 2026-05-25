"""
OURE Physics Engine - Anomaly & Maneuver Detection
==================================================
Detects unannounced maneuvers by comparing older propagated states
against newly observed states (Non-Cooperative Tracking).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from oure.core.models import StateVector
from oure.physics.base import BasePropagator

logger = logging.getLogger("oure.physics.anomaly")


@dataclass
class AnomalyReport:
    """Report generated after comparing an expected state vs actual state."""

    is_anomaly: bool
    position_diff_km: float
    velocity_diff_km_s: float
    expected_state: StateVector
    actual_state: StateVector
    threshold_km: float


class ManeuverDetector:
    """
    Detects unannounced maneuvers by comparing a previously known state
    propagated forward in time against a freshly observed state.
    """

    def __init__(self, propagator: BasePropagator, position_threshold_km: float = 10.0):
        """
        Args:
            propagator: The physics engine used to predict the expected state.
            position_threshold_km: Deviation in position (km) considered anomalous.
        """
        self.propagator = propagator
        self.threshold = position_threshold_km

    def detect(self, old_state: StateVector, new_state: StateVector) -> AnomalyReport:
        """
        Detects if a maneuver occurred between old_state.epoch and new_state.epoch.

        Args:
            old_state: The baseline StateVector.
            new_state: The newly observed StateVector at a later epoch.

        Returns:
            AnomalyReport detailing the magnitude of the divergence.
        """
        if new_state.epoch <= old_state.epoch:
            raise ValueError("new_state epoch must be strictly after old_state epoch.")

        # Predict where the satellite *should* be based on natural physics
        expected_state = self.propagator.propagate_to(old_state, new_state.epoch)

        # Calculate divergence
        diff_r = float(np.linalg.norm(expected_state.r - new_state.r))
        diff_v = float(np.linalg.norm(expected_state.v - new_state.v))

        is_anomaly = diff_r > self.threshold

        if is_anomaly:
            logger.warning(
                f"ANOMALY DETECTED for {old_state.sat_id}: "
                f"Deviation of {diff_r:.2f} km exceeds threshold of {self.threshold} km."
            )
        else:
            logger.debug(
                f"Nominal tracking for {old_state.sat_id}: dev={diff_r:.2f} km."
            )

        return AnomalyReport(
            is_anomaly=is_anomaly,
            position_diff_km=diff_r,
            velocity_diff_km_s=diff_v,
            expected_state=expected_state,
            actual_state=new_state,
            threshold_km=self.threshold,
        )
