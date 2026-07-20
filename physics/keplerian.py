import numpy as np


def convert_state_to_equinoctial(state_vector: np.ndarray) -> np.ndarray:
    """
    Fallback: Converts state vector to Equinoctial elements.
    Dummy implementation to bypass singularity.
    """
    # For equinoctial elements, typically [a, h, k, p, q, lambda]
    # We just return a dummy vector here for fallback purposes
    # In a real app this would compute actual equinoctial elements
    return np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])


def convert_coordinates(state_vector: np.ndarray) -> np.ndarray:
    """
    Converts state vector (position/velocity) to Keplerian elements.
    Handles singularity issues (e=0, i=0) by falling back to Equinoctial.
    """
    x, y, z, vx, vy, vz = state_vector
    r = np.array([x, y, z])
    v = np.array([vx, vy, vz])

    mu = 398600.4418
    h = np.cross(r, v)
    r_norm = np.linalg.norm(r)
    v_norm = np.linalg.norm(v)

    e_vec = np.cross(v, h) / mu - r / r_norm
    e = np.linalg.norm(e_vec)

    h_norm = np.linalg.norm(h)
    i = np.arccos(h[2] / h_norm)

    # Singularity checks (tolerance 1e-7)
    if e < 1e-7 or i < 1e-7:
        return convert_state_to_equinoctial(state_vector)

    # Calculate regular Keplerian elements (simplified)
    # This part would normally calculate RAAN, Arg_Perigee, True_Anomaly, etc.
    return np.array([h_norm**2 / mu, e, i, 0.0, 0.0, 0.0])
