"""
OURE Risk Calculation - Maneuver Optimizer
==========================================
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import numpy as np
from scipy.optimize import minimize

from oure.conjunction.tca_finder import TCARefinementEngine
from oure.core.models import (
    ConjunctionEvent,
    CovarianceMatrix,
    OptimizationResult,
    StateVector,
)
from oure.physics.base import BasePropagator
from oure.physics.maneuver import Maneuver, ManeuverPropagator
from oure.risk.calculator import RiskCalculator

logger = logging.getLogger("oure.risk.optimizer")


class ManeuverOptimizer:
    """
    Finds the optimal Delta-V to mitigate collision risk.
    """

    def __init__(
        self,
        base_prop: BasePropagator,
        primary_state: StateVector,
        secondary_state: StateVector,
        primary_cov: CovarianceMatrix,
        secondary_cov: CovarianceMatrix,
        burn_epoch: datetime,
        target_pc: float = 1e-5,
    ):
        self.base_prop = base_prop
        self.primary_state = primary_state
        self.secondary_state = secondary_state
        self.primary_cov = primary_cov
        self.secondary_cov = secondary_cov
        self.burn_epoch = burn_epoch
        self.target_pc = target_pc

        self.tca_finder = TCARefinementEngine()
        self.risk_calc = RiskCalculator()

        # Find the nominal TCA (without maneuver)
        search_start = self.primary_state.epoch
        search_end = search_start + timedelta(hours=72)
        res = self.tca_finder.find_tca(
            primary_state,
            base_prop,
            secondary_state,
            base_prop,
            search_start,
            search_end,
        )
        if not res:
            raise ValueError("No nominal conjunction found to optimize.")

        self.nominal_tca, self.nominal_miss = res

    def optimize(
        self,
        max_dv_km_s: float = 0.05,
        isp: float = 220.0,
        dry_mass_kg: float = 100.0,
        raan_tolerance_deg: float = 0.05,
    ) -> OptimizationResult:
        import math

        start_epoch = self.primary_state.epoch
        end_epoch = self.nominal_tca - timedelta(minutes=30)

        best_result = None
        best_dv_mag = float("inf")

        r0 = self.primary_state.r
        v0 = self.primary_state.v
        h0 = np.cross(r0, v0)
        n0 = np.cross([0, 0, 1], h0)
        n0_mag = float(np.linalg.norm(n0))
        orig_raan = 0.0
        if n0_mag >= 1e-12:
            orig_raan = math.acos(n0[0] / n0_mag)
            if n0[1] < 0:
                orig_raan = 2 * math.pi - orig_raan
        orig_raan_deg = math.degrees(orig_raan)

        current_epoch = start_epoch
        while current_epoch <= end_epoch:
            res = self._optimize_for_epoch(current_epoch, max_dv_km_s)
            if res.success:
                dv_mag = float(np.linalg.norm(res.optimal_dv_km_s))
                if dv_mag < best_dv_mag:
                    man = Maneuver(
                        burn_epoch=current_epoch, delta_v_eci=res.optimal_dv_km_s
                    )
                    man_prop = ManeuverPropagator(self.base_prop, [man])

                    p_post_burn = man_prop.propagate_to(
                        self.primary_state, current_epoch + timedelta(seconds=1)
                    )
                    h_post = np.cross(p_post_burn.r, p_post_burn.v)
                    n_post = np.cross([0, 0, 1], h_post)
                    n_post_mag = float(np.linalg.norm(n_post))
                    post_raan = 0.0
                    if n_post_mag >= 1e-12:
                        post_raan = math.acos(n_post[0] / n_post_mag)
                        if n_post[1] < 0:
                            post_raan = 2 * math.pi - post_raan
                    post_raan_deg = math.degrees(post_raan)

                    raan_diff = abs(orig_raan_deg - post_raan_deg)
                    raan_diff = min(raan_diff, 360.0 - raan_diff)

                    station_keeping_ok = raan_diff <= raan_tolerance_deg

                    dv_m_s = dv_mag * 1000.0
                    fuel_cost_kg = dry_mass_kg * (
                        math.exp(dv_m_s / (isp * 9.80665)) - 1.0
                    )

                    res.burn_epoch = current_epoch
                    res.fuel_cost_kg = fuel_cost_kg
                    res.station_keeping_ok = station_keeping_ok

                    best_result = res
                    best_dv_mag = dv_mag

            current_epoch += timedelta(minutes=10)

        if best_result is None:
            return OptimizationResult(
                optimal_dv_km_s=np.zeros(3),
                final_pc=0.0,
                iterations=0,
                success=False,
                message="No maneuver found satisfying constraints.",
            )
        return best_result

    def _objective(self, dv: np.ndarray) -> float:
        """Objective: Minimize the magnitude of the Delta-V vector (save fuel)."""
        return float(np.sum(dv**2) * 1e6)

    def _constraint_pc(
        self, dv: np.ndarray, burn_epoch: datetime, s_tca_nominal: StateVector
    ) -> float:
        """Constraint: Target Pc - Actual Pc >= 0."""
        maneuver = Maneuver(burn_epoch=burn_epoch, delta_v_eci=dv)
        man_prop = ManeuverPropagator(self.base_prop, [maneuver])

        tca_res = self.tca_finder.find_tca(
            self.primary_state,
            man_prop,
            self.secondary_state,
            self.base_prop,
            self.nominal_tca - timedelta(hours=1),
            self.nominal_tca + timedelta(hours=1),
        )

        if not tca_res:
            return self.target_pc

        new_tca, new_miss = tca_res

        p_tca = man_prop.propagate_to(self.primary_state, new_tca)
        if abs((new_tca - self.nominal_tca).total_seconds()) < 60.0:
            s_tca = s_tca_nominal
        else:
            s_tca = self.base_prop.propagate_to(self.secondary_state, new_tca)

        v_rel = float(np.linalg.norm(p_tca.v - s_tca.v))

        event = ConjunctionEvent(
            primary_id=self.primary_state.sat_id,
            secondary_id=self.secondary_state.sat_id,
            tca=new_tca,
            miss_distance_km=new_miss,
            relative_velocity_km_s=v_rel,
            primary_state=p_tca,
            secondary_state=s_tca,
            primary_covariance=self.primary_cov,
            secondary_covariance=self.secondary_cov,
        )

        risk = self.risk_calc.compute_pc(event)
        return self.target_pc - risk.pc

    def _optimize_for_epoch(
        self, burn_epoch: datetime, max_dv_km_s: float = 0.05
    ) -> OptimizationResult:
        """
        Runs SLSQP optimization to find minimum Delta-V.
        """
        s_tca_nominal = self.base_prop.propagate_to(
            self.secondary_state, self.nominal_tca
        )

        burn_state = self.base_prop.propagate_to(self.primary_state, burn_epoch)

        v_hat = burn_state.v / np.linalg.norm(burn_state.v)
        x0 = v_hat * 1e-5

        bnds = [(-max_dv_km_s, max_dv_km_s)] * 3

        # lambda to pass extra arguments
        cons = {
            "type": "ineq",
            "fun": lambda dv: self._constraint_pc(dv, burn_epoch, s_tca_nominal),
        }

        logger.info("Starting SLSQP maneuver optimization...")
        res = minimize(  # type: ignore[call-overload]
            fun=self._objective,
            x0=x0,
            method="SLSQP",
            bounds=bnds,
            constraints=cons,
            options={"disp": False, "ftol": 1e-8, "maxiter": 25},
        )

        if res.success:
            optimal_dv = res.x
            man = Maneuver(burn_epoch=burn_epoch, delta_v_eci=optimal_dv)
            man_prop = ManeuverPropagator(self.base_prop, [man])

            tca_res = self.tca_finder.find_tca(
                self.primary_state,
                man_prop,
                self.secondary_state,
                self.base_prop,
                self.nominal_tca - timedelta(minutes=5),
                self.nominal_tca + timedelta(minutes=5),
            )

            if tca_res:
                final_tca, final_miss = tca_res
                p_final = man_prop.propagate_to(self.primary_state, final_tca)
                s_final = self.base_prop.propagate_to(self.secondary_state, final_tca)
                v_rel = float(np.linalg.norm(p_final.v - s_final.v))

                final_event = ConjunctionEvent(
                    primary_id=self.primary_state.sat_id,
                    secondary_id=self.secondary_state.sat_id,
                    tca=final_tca,
                    miss_distance_km=final_miss,
                    relative_velocity_km_s=v_rel,
                    primary_state=p_final,
                    secondary_state=s_final,
                    primary_covariance=self.primary_cov,
                    secondary_covariance=self.secondary_cov,
                )
                final_risk = self.risk_calc.compute_pc(final_event)
                final_pc = final_risk.pc
            else:
                margin = self._constraint_pc(optimal_dv, burn_epoch, s_tca_nominal)
                final_pc = self.target_pc - margin

            return OptimizationResult(
                optimal_dv_km_s=optimal_dv,
                final_pc=final_pc,
                iterations=res.nit,
                success=True,
                message="Optimization successful",
            )
        else:
            return OptimizationResult(
                optimal_dv_km_s=np.zeros(3),
                final_pc=0.0,
                iterations=res.nit,
                success=False,
                message=res.message,
            )
