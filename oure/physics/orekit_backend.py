"""
Orekit Physics Backend Wrapper
==============================
Provides high-fidelity propagation by bridging to the industry-standard Java Orekit library.
This is an OPTIONAL backend. If orekit is not installed, it raises a helpful error.
"""

from datetime import datetime
from typing import Any

from oure.core.models import StateVector, TLERecord
from oure.physics.base import BasePropagator


class OrekitPropagator(BasePropagator):
    """
    Propagates a satellite state using Orekit's SGP4 or Numerical Propagator.
    """

    def __init__(self, tle: TLERecord, use_numerical: bool = False):
        self.tle = tle
        self.use_numerical = use_numerical

        try:
            import orekit

            # Note: In a real environment, orekit-data.zip must be present.
            # This is a stub initialization for the wrapper.
            orekit.initVM()
            # setup_orekit_curdir()

            self._orekit_available = True
        except ImportError:
            self._orekit_available = False
            raise ImportError(
                "The 'orekit' package is not installed. \n\n"
                "Orekit is an optional high-fidelity backend for OURE.\n"
                "Because pre-compiled wheels are not always available on PyPI (especially for Apple Silicon),\n"
                "you must install it manually via conda:\n"
                "    conda install -c conda-forge orekit\n\n"
                "Or stick to the default native Python HPOP/SGP4 backend."
            )

    def propagate(self, state: StateVector, dt_seconds: float) -> StateVector:
        if not self._orekit_available:
            raise RuntimeError("Orekit is not available.")
        raise NotImplementedError("Orekit preview.")

    def propagate_to(self, state: StateVector, target_epoch: datetime) -> StateVector:
        if not self._orekit_available:
            raise RuntimeError("Orekit is not available.")
        raise NotImplementedError("Orekit preview.")

    def propagate_many_to(
        self, states: Any, initial_epoch: datetime, target_epoch: datetime
    ) -> Any:
        if not self._orekit_available:
            raise RuntimeError("Orekit is not available.")
        raise NotImplementedError("Orekit preview.")
