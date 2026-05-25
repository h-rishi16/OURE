"""
OURE Physics Engine - Propagator Factory
========================================
"""

from __future__ import annotations

import logging

from oure.core.constants import SOLAR_FLUX_MEAN_SFU
from oure.core.models import TLERecord

from .base import BasePropagator
from .numerical import NumericalPropagator
from .sgp4_propagator import SGP4Propagator

logger = logging.getLogger("oure.physics.factory")


class PropagatorFactory:
    """
    Assembles the layered propagator chain from a TLE + space weather context.
    """

    @staticmethod
    def build(
        tle: TLERecord,
        solar_flux: float = SOLAR_FLUX_MEAN_SFU,
        use_analytical: bool = True,
        include_srp: bool = False,
        use_third_body: bool = False,
        cd: float = 2.2,
        cr: float = 1.2,
        area_m2: float = 10.0,
        mass_kg: float = 500.0,
        ap: float = 4.0,
    ) -> BasePropagator:
        """
        Builds and returns the configured propagator chain.
        """
        if use_analytical:
            # Analytical Track: Pure SGP4.
            # Note: SGP4 implicitly models J2 and Drag (via B*), so it must NEVER
            # be wrapped in additional J2 or Drag decorators.
            logger.debug("Using Analytical SGP4 Track")
            return SGP4Propagator.from_tle(tle)

        # Numerical Track: HPOP (High-Precision Orbit Propagator)
        # The NumericalPropagator inherently calculates J2, Drag, SRP, and Third Body
        logger.debug(f"Using Numerical HPOP Track (F10.7={solar_flux})")
        return NumericalPropagator(
            cd=cd,
            cr=cr,
            area_m2=area_m2,
            mass_kg=mass_kg,
            solar_flux=solar_flux,
            include_srp=include_srp,
            ap=ap,
            use_third_body=use_third_body,
        )
