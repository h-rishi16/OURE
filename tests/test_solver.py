import numpy as np

from physics.solver import propagate_orbit


def test_propagate_orbit():
    # Initial state (LEO circular orbit)
    # Altitude ~ 400km
    r0 = np.array([6778.0, 0.0, 0.0])  # km
    v0 = np.array([0.0, 7.668, 0.0])  # km/s
    initial_state = np.concatenate((r0, v0))

    t_span = [0, 5400]  # roughly 90 minutes (1 period)

    result = propagate_orbit(initial_state, t_span)

    assert result.success
    # The magnitude of position and velocity should remain roughly constant for a circular two-body orbit
    r_final = result.y[:3, -1]
    v_final = result.y[3:, -1]

    assert np.isclose(np.linalg.norm(r_final), np.linalg.norm(r0), rtol=1e-5)
    assert np.isclose(np.linalg.norm(v_final), np.linalg.norm(v0), rtol=1e-5)
