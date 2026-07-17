import numpy as np

from physics.keplerian import convert_coordinates


def test_circular_orbit():
    # Circular orbit, equatorial (e=0, i=0)
    # This should trigger the fallback
    r0 = np.array([6778.0, 0.0, 0.0])  # km
    v0 = np.array([0.0, 7.668, 0.0])  # km/s
    initial_state = np.concatenate((r0, v0))

    result = convert_coordinates(initial_state)

    # We check if it returned the equinoctial dummy vector
    assert np.allclose(result, np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]))
