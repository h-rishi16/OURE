import numpy as np

from coords.transforms import eci_to_ecef_vectorized


def test_eci_to_ecef():
    N = 1000
    eci_coords = np.zeros((N, 3))
    eci_coords[:, 0] = 6778.0  # all on x-axis in ECI

    # Let's say earth rotates 90 degrees
    # theta = omega * t => t = theta / omega
    omega_e = 7.2921159e-5
    t_90 = (np.pi / 2) / omega_e

    timestamps = np.full(N, t_90)

    ecef_coords = eci_to_ecef_vectorized(eci_coords, timestamps)

    # In ECEF, the x-axis points should now be on the negative y-axis
    # x_ecef = x_eci * cos(90) + y_eci * sin(90) = 0
    # y_ecef = -x_eci * sin(90) + y_eci * cos(90) = -6778.0

    assert ecef_coords.shape == (N, 3)
    assert np.allclose(ecef_coords[:, 0], 0.0, atol=1e-5)
    assert np.allclose(ecef_coords[:, 1], -6778.0, atol=1e-5)
    assert np.allclose(ecef_coords[:, 2], 0.0, atol=1e-5)
