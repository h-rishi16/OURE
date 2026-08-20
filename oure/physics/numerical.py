"""
OURE Physics Engine - High Precision Orbit Propagator (HPOP)
============================================================
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

import numpy as np
from scipy.integrate import solve_ivp

from oure.core import constants
from oure.core.models import StateVector

from .atmosphere import AtmosphericModel
from .base import BasePropagator


def _compute_sun_hat(epoch: datetime) -> np.ndarray:
    from datetime import UTC
    from math import cos, sin

    if epoch.tzinfo is None:
        epoch = epoch.replace(tzinfo=UTC)
    t_j2000 = (
        epoch - datetime(2000, 1, 1, 12, 0, tzinfo=UTC)
    ).total_seconds() / 86400.0
    mean_long = (280.460 + 0.9856474 * t_j2000) % 360
    g = (357.528 + 0.9856003 * t_j2000) % 360
    lamb = (
        mean_long + 1.915 * sin(np.radians(g)) + 0.020 * sin(np.radians(2 * g))
    ) % 360
    eps = 23.439 - 0.0000004 * t_j2000
    r_sun = np.array(
        [
            cos(np.radians(lamb)),
            sin(np.radians(lamb)) * cos(np.radians(eps)),
            sin(np.radians(lamb)) * sin(np.radians(eps)),
        ]
    )
    from typing import cast

    return cast(np.ndarray, r_sun / np.linalg.norm(r_sun))


class NumericalPropagator(BasePropagator):
    """
    High-Precision Orbit Propagator using Runge-Kutta 4(5) numerical integration.

    Unlike SGP4 (which uses analytical mean elements), this integrates the exact
    equations of motion [r, v] step-by-step. It easily supports injecting instant
    delta-V maneuvers.

    Includes:
    - Point-mass gravity
    - J2 Oblateness
    - Exponential Atmospheric Drag
    - Solar Radiation Pressure (SRP)
    """

    def __init__(
        self,
        cd: float = 2.2,
        cr: float = 1.2,
        area_m2: float = 10.0,
        mass_kg: float = 500.0,
        solar_flux: float = 150.0,
        include_srp: bool = True,
        ap: float = 4.0,
        use_third_body: bool = False,
    ):
        self.cd = cd
        self.cr = cr
        self.am_ratio = area_m2 / mass_kg
        self.f10_7 = solar_flux
        self.include_srp = include_srp
        self.ap = ap
        self.use_third_body = use_third_body

        self._atmo = AtmosphericModel(solar_flux=solar_flux, ap=ap)
        self._base_epoch: datetime | None = None

    def _dynamics(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        The state derivative function for solve_ivp: dy/dt = f(t, y)
        y = [x, y, z, vx, vy, vz]
        """
        r = y[:3]
        v = y[3:]
        r_mag = np.linalg.norm(r)

        # 1. Two-Body Gravity
        a_grav = -constants.MU_KM3_S2 * r / (r_mag**3)

        # 2. J2 Perturbation
        z = r[2]
        factor = (
            -1.5
            * constants.J2
            * constants.MU_KM3_S2
            * constants.R_EARTH_KM**2
            / (r_mag**5)
        )
        z_ratio = (z / r_mag) ** 2
        a_j2 = factor * np.array(
            [
                r[0] * (1 - 5 * z_ratio),
                r[1] * (1 - 5 * z_ratio),
                r[2] * (3 - 5 * z_ratio),
            ]
        )

        # 3. Atmospheric Drag
        altitude = r_mag - constants.R_EARTH_KM
        sim_epoch = (self._base_epoch or datetime.now(UTC)) + timedelta(seconds=t)
        rho = self._atmo.get_density(r, sim_epoch)

        # Co-rotation of atmosphere
        v_rel = v.copy()
        v_rel[0] += constants.OMEGA_EARTH_RAD_S * r[1]
        v_rel[1] -= constants.OMEGA_EARTH_RAD_S * r[0]

        v_mag = np.linalg.norm(v_rel)
        if v_mag > 1e-9:
            v_mag_ms = v_mag * 1000.0
            a_drag_ms2 = -0.5 * self.cd * self.am_ratio * rho * (v_mag_ms**2)
            a_drag = (a_drag_ms2 / 1000.0) * (v_rel / v_mag)
        else:
            a_drag = np.zeros(3)

        # 4. Solar Radiation Pressure (SRP)
        a_srp = np.zeros(3)
        if self.include_srp:
            p_sun = 4.56e-6
            a_srp_ms2 = -p_sun * self.cr * self.am_ratio * self._cached_sun_hat
            a_srp = a_srp_ms2 / 1000.0

        # 5. Third-Body Gravity
        a_third = np.zeros(3)
        if self.use_third_body and altitude > 2000.0:
            for gm, r_body in [
                (4.9048695e12 / 1e9, self._cached_moon_pos),
                (1.32712440018e20 / 1e9, self._cached_sun_pos),
            ]:
                r_rel = r_body - r
                a_third += gm * (
                    r_rel / (np.linalg.norm(r_rel) ** 3)
                    - r_body / (np.linalg.norm(r_body) ** 3)
                )

        a_tot = a_grav + a_j2 + a_drag + a_srp + a_third
        return np.concatenate([v, a_tot])

    def propagate(self, state: StateVector, dt_seconds: float) -> StateVector:
        if dt_seconds == 0:
            return state

        self._base_epoch = state.epoch
        y0 = state.state_vector_6d

        mid_epoch = state.epoch + timedelta(seconds=dt_seconds / 2)
        if self.include_srp:
            self._cached_sun_hat = _compute_sun_hat(mid_epoch)
        if self.use_third_body:
            import astropy.units as u
            from astropy.coordinates import GCRS, get_body
            from astropy.time import Time

            t_mid = Time(mid_epoch)
            moon_pos = (
                get_body("moon", t_mid).transform_to(GCRS(obstime=t_mid)).cartesian
            )
            self._cached_moon_pos = np.array(
                [
                    moon_pos.x.to_value(u.km),
                    moon_pos.y.to_value(u.km),
                    moon_pos.z.to_value(u.km),
                ]
            )
            sun_pos = get_body("sun", t_mid).transform_to(GCRS(obstime=t_mid)).cartesian
            self._cached_sun_pos = np.array(
                [
                    sun_pos.x.to_value(u.km),
                    sun_pos.y.to_value(u.km),
                    sun_pos.z.to_value(u.km),
                ]
            )

        # Integrate using RK45
        sol = solve_ivp(
            fun=self._dynamics,
            t_span=[0, dt_seconds],
            y0=y0,
            method="RK45",
            rtol=1e-8,
            atol=1e-8,
        )

        if not sol.success:
            from oure.core.exceptions import PropagationError

            raise PropagationError(f"Numerical integration failed: {sol.message}")

        y_final = sol.y[:, -1]

        r_final = y_final[:3]
        if np.linalg.norm(r_final) < constants.R_EARTH_KM:
            from oure.core.exceptions import PropagationError

            raise PropagationError(
                "Trajectory impacted Earth's surface during numerical propagation."
            )

        target_epoch = state.epoch + timedelta(seconds=dt_seconds)
        return StateVector.from_6d(y_final, target_epoch, state.sat_id)

    def propagate_to(self, state: StateVector, target_epoch: datetime) -> StateVector:
        dt = (target_epoch - state.epoch).total_seconds()
        return self.propagate(state, dt)

    def _dynamics_vectorized(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        Vectorized dynamics for N satellites. y is shape (6N,).
        """
        y_reshaped = y.reshape(-1, 6)
        r = y_reshaped[:, :3]
        v = y_reshaped[:, 3:]

        r_mag = np.linalg.norm(r, axis=1)

        # 1. Two-Body Gravity
        a_grav = -constants.MU_KM3_S2 * r / (r_mag[:, np.newaxis] ** 3)

        # 2. J2 Perturbation
        z = r[:, 2]
        factor = (
            -1.5
            * constants.J2
            * constants.MU_KM3_S2
            * constants.R_EARTH_KM**2
            / (r_mag**5)
        )
        z_ratio = (z / r_mag) ** 2

        a_j2 = np.zeros_like(r)
        a_j2[:, 0] = factor * r[:, 0] * (1 - 5 * z_ratio)
        a_j2[:, 1] = factor * r[:, 1] * (1 - 5 * z_ratio)
        a_j2[:, 2] = factor * r[:, 2] * (3 - 5 * z_ratio)

        # 3. Atmospheric Drag
        altitude = r_mag - constants.R_EARTH_KM
        sim_epoch = (self._base_epoch or datetime.now(UTC)) + timedelta(seconds=t)
        epochs = [sim_epoch] * len(r)
        rho = self._atmo.get_density_vectorized(r, epochs)

        # Co-rotation
        v_rel = v.copy()
        v_rel[:, 0] += constants.OMEGA_EARTH_RAD_S * r[:, 1]
        v_rel[:, 1] -= constants.OMEGA_EARTH_RAD_S * r[:, 0]

        v_mag = np.linalg.norm(v_rel, axis=1)

        a_drag = np.zeros_like(v)
        valid = v_mag > 1e-9
        if np.any(valid):
            v_mag_ms = v_mag[valid] * 1000.0
            a_drag_ms2 = -0.5 * self.cd * self.am_ratio * rho[valid] * (v_mag_ms**2)
            v_hat = v_rel[valid] / v_mag[valid][:, np.newaxis]
            a_drag[valid] = (a_drag_ms2 / 1000.0)[:, np.newaxis] * v_hat

        # 4. Solar Radiation Pressure (SRP)
        a_srp = np.zeros_like(v)
        if self.include_srp:
            p_sun = 4.56e-6
            a_srp_ms2 = -p_sun * self.cr * self.am_ratio * self._cached_sun_hat
            a_srp[:] = a_srp_ms2 / 1000.0

        # 5. Third-Body Gravity
        a_third = np.zeros_like(v)
        if self.use_third_body:
            for gm, r_body in [
                (4.9048695e12 / 1e9, self._cached_moon_pos),
                (1.32712440018e20 / 1e9, self._cached_sun_pos),
            ]:
                r_rel = r_body - r
                r_rel_mag = np.linalg.norm(r_rel, axis=1)
                r_body_mag = np.linalg.norm(r_body)
                a_third += gm * (
                    r_rel / (r_rel_mag[:, np.newaxis] ** 3) - r_body / (r_body_mag**3)
                )

            # Mask out for altitude < 2000 km
            mask_alt = altitude <= 2000.0
            a_third[mask_alt] = 0.0

        a_tot = a_grav + a_j2 + a_drag + a_srp + a_third
        return np.hstack([v, a_tot]).flatten()

    def propagate_many_to(
        self, states: np.ndarray, initial_epoch: datetime, target_epoch: datetime
    ) -> np.ndarray:
        dt_seconds = (target_epoch - initial_epoch).total_seconds()
        if dt_seconds == 0:
            return states

        self._base_epoch = initial_epoch
        y0 = states.flatten()

        mid_epoch = initial_epoch + timedelta(seconds=dt_seconds / 2)
        if self.include_srp:
            self._cached_sun_hat = _compute_sun_hat(mid_epoch)
        if self.use_third_body:
            import astropy.units as u
            from astropy.coordinates import GCRS, get_body
            from astropy.time import Time

            t_mid = Time(mid_epoch)
            moon_pos = (
                get_body("moon", t_mid).transform_to(GCRS(obstime=t_mid)).cartesian
            )
            self._cached_moon_pos = np.array(
                [
                    moon_pos.x.to_value(u.km),
                    moon_pos.y.to_value(u.km),
                    moon_pos.z.to_value(u.km),
                ]
            )
            sun_pos = get_body("sun", t_mid).transform_to(GCRS(obstime=t_mid)).cartesian
            self._cached_sun_pos = np.array(
                [
                    sun_pos.x.to_value(u.km),
                    sun_pos.y.to_value(u.km),
                    sun_pos.z.to_value(u.km),
                ]
            )

        sol = solve_ivp(
            fun=self._dynamics_vectorized,
            t_span=[0, dt_seconds],
            y0=y0,
            method="RK45",
            rtol=1e-8,
            atol=1e-8,
        )

        if not sol.success:
            from oure.core.exceptions import PropagationError

            raise PropagationError(
                f"Numerical integration failed in batch: {sol.message}"
            )

        y_final = sol.y[:, -1]

        # Record performance metrics
        from oure.core.metrics import MetricsManager

        MetricsManager.record_propagation(len(states), p_type="numerical")

        return cast("np.ndarray", y_final.reshape(-1, 6))
