import numpy as np


def eci_to_ecef_vectorized(
    eci_coords: np.ndarray, timestamps: np.ndarray
) -> np.ndarray:
    """
    Vectorized transformation from ECI to ECEF coordinates.
    eci_coords: numpy array of shape (N, 3)
    timestamps: numpy array of shape (N, 1) or (N,) representing time in seconds

    Returns ECEF coordinates of shape (N, 3)
    """
    # Earth's rotation rate in radians per second
    omega_e = 7.2921159e-5

    # Calculate the rotation angle (theta) for each timestamp
    theta = omega_e * timestamps.flatten()

    # Calculate cos and sin of theta
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    # The rotation matrix for each point around the Z axis
    # R = [[cos, sin, 0],
    #      [-sin, cos, 0],
    #      [0,    0,    1]]

    # We can do this efficiently without building N 3x3 matrices using direct array operations
    x_eci = eci_coords[:, 0]
    y_eci = eci_coords[:, 1]
    z_eci = eci_coords[:, 2]

    x_ecef = x_eci * cos_t + y_eci * sin_t
    y_ecef = -x_eci * sin_t + y_eci * cos_t
    z_ecef = z_eci

    return np.column_stack((x_ecef, y_ecef, z_ecef))
