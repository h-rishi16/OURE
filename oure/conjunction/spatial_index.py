"""
OURE Conjunction Assessment - KD-Tree Spatial Index
===================================================
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import KDTree


class KDTreeSpatialIndex:
    """
    KD-Tree wrapper for fast satellite proximity queries.
    Reduces O(N²) pairwise screening to O(N log N) per timestep.
    """

    def __init__(self, positions: np.ndarray):
        """
        Initializes the spatial index with a set of positions.

        Args:
            positions (np.ndarray): Array of shape (N, 3) of ECI positions in km.
        """
        if (
            not isinstance(positions, np.ndarray)
            or positions.ndim != 2
            or positions.shape[1] != 3
        ):
            raise ValueError("Input 'positions' must be a NumPy array of shape (N, 3)")
        self._tree = KDTree(positions)

    def query_radius(self, point: np.ndarray, radius_km: float) -> list[int]:
        """
        Queries the index for all points within a given radius of a point.

        Args:
            point (np.ndarray): The center point of the query sphere, shape (3,).
            radius_km (float): The radius of the query sphere in km.

        Returns:
            List[int]: A list of indices into the original positions array.
        """
        return list(self._tree.query_ball_point(point, r=radius_km))
