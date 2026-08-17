"""
OURE Risk Calculation - Orchestrator
====================================
"""

from __future__ import annotations

from typing import Any

import numpy as np

from oure.core.models import ConjunctionEvent, RiskResult

from .alert import AlertClassifier
from .alfano import AlfanoPcCalculator
from .bplane import BPlaneProjector
from .foster import FosterPcCalculator


class RiskCalculator:
    """
    Computes the Probability of Collision for a ConjunctionEvent.
    """

    def __init__(self, hard_body_radius_m: float = 20.0, method: str = "foster"):
        self.hard_body_radius_km = hard_body_radius_m / 1000.0
        self.bplane_projector = BPlaneProjector()

        self.method = method.lower()
        self.pc_calculator: Any
        if self.method == "alfano":
            self.pc_calculator = AlfanoPcCalculator(self.hard_body_radius_km)
        elif self.method == "chan":
            from .chan import ChanPcCalculator

            self.pc_calculator = ChanPcCalculator(self.hard_body_radius_km)
        else:
            self.pc_calculator = FosterPcCalculator(self.hard_body_radius_km)

    def compute_pc(self, event: ConjunctionEvent) -> RiskResult:
        """
        Full Pc pipeline for one conjunction event.
        """
        import time

        from oure.core.metrics import MetricsManager

        start_time = time.perf_counter()

        # Safety check: Near-zero relative velocity makes B-plane projection singular
        if event.relative_velocity_km_s < 1e-6:
            res = RiskResult(
                conjunction=event,
                pc=0.0,
                max_pc=0.0,
                combined_covariance=np.zeros((2, 2)),
                warning_level="GREEN",
                b_plane_sigma_x=0.0,
                b_plane_sigma_z=0.0,
                hard_body_radius_m=self.hard_body_radius_km * 1000.0,
                method="SKIPPED_SINGULAR",
            )
            MetricsManager.record_risk_duration(time.perf_counter() - start_time)
            return res

        projection = self.bplane_projector.project(event)

        age_p = (event.tca - event.primary_state.epoch).total_seconds() / 3600.0
        age_s = (event.tca - event.secondary_state.epoch).total_seconds() / 3600.0
        propagation_age_hours = max(age_p, age_s)

        pc = self.pc_calculator.compute(
            projection.b_vec_2d, projection.C_2d, propagation_age_hours
        )

        # Calculate the maximum probability bound (Alfano) to detect Probability Dilution
        alfano = AlfanoPcCalculator(self.hard_body_radius_km)
        max_pc = alfano.compute(
            projection.b_vec_2d, projection.C_2d, propagation_age_hours
        )

        sigma_x = np.sqrt(projection.C_2d[0, 0])
        sigma_z = np.sqrt(projection.C_2d[1, 1])

        alert = AlertClassifier()

        result = RiskResult(
            conjunction=event,
            pc=pc,
            max_pc=max_pc,
            combined_covariance=projection.C_2d,
            hard_body_radius_m=self.hard_body_radius_km * 1000,
            b_plane_sigma_x=sigma_x,
            b_plane_sigma_z=sigma_z,
            method=getattr(self.pc_calculator, "method", None)
            and self.pc_calculator.method.value
            or "Alfano_Max_Prob",
        )

        result.warning_level = alert.classify(result)

        # Record metrics
        MetricsManager.record_risk_duration(time.perf_counter() - start_time)

        return result
