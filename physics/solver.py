from typing import Any, List

import numpy as np
from scipy.integrate import solve_ivp


def compute_derivatives(t: float, state: np.ndarray) -> List[float]:
    """
    Computes the derivatives for the orbital propagation.
    state = [x, y, z, vx, vy, vz]
    """
    x, y, z, vx, vy, vz = state
    r = np.array([x, y, z])
    r_norm = np.linalg.norm(r)

    # Simple two-body gravity: a = -mu * r / r^3
    mu = 398600.4418  # Earth's gravitational parameter in km^3/s^2
    ax, ay, az = -mu * r / r_norm**3

    return [float(vx), float(vy), float(vz), float(ax), float(ay), float(az)]


def propagate_orbit(
    initial_state: np.ndarray, t_span: List[float], t_eval: Any = None
) -> Any:
    """
    Propagates the orbit using scipy.integrate.solve_ivp with DOP853.
    """
    result = solve_ivp(
        fun=compute_derivatives,
        t_span=t_span,
        y0=initial_state,
        method="DOP853",
        atol=1e-12,
        rtol=1e-12,
        t_eval=t_eval,
    )
    return result
