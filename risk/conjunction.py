from typing import Any, Dict, List, Tuple

import numpy as np


def check_conjunctions(
    satellites: List[Dict[str, Any]], threshold: float = 10.0
) -> List[Tuple[Any, Any, float]]:
    """
    Finds possible conjunctions (collisions) using AABB pre-filtering followed by SciPy distance.
    satellites: list of dicts with 'id', 'min_coords' (3,), 'max_coords' (3,), 'path' (N, 3)
    """
    conjunctions = []
    num_sats = len(satellites)

    # 1. AABB Pre-filtering (Vectorized Bounding Box Check)
    # Extract min and max coordinates for all satellites
    min_coords = np.array([s["min_coords"] for s in satellites])
    max_coords = np.array([s["max_coords"] for s in satellites])

    # We want to check overlap:
    # Two AABBs A and B overlap if:
    # A.min[i] <= B.max[i] AND A.max[i] >= B.min[i] for all i in [x, y, z]
    # To do this for all pairs (i, j):

    # min_coords[:, None, :] shape (N, 1, 3) compared with max_coords[None, :, :] shape (1, N, 3)
    overlap = (min_coords[:, None, :] <= max_coords[None, :, :]) & (
        max_coords[:, None, :] >= min_coords[None, :, :]
    )

    # Overlap in all 3 dimensions
    overlap_all_dims = np.all(overlap, axis=2)

    # Get indices of overlapping pairs (i < j to avoid self and duplicates)
    i_idx, j_idx = np.where(overlap_all_dims)
    valid_pairs = [(i, j) for i, j in zip(i_idx, j_idx) if i < j]

    # 2. Heavy SciPy Distance Checking on candidates
    for i, j in valid_pairs:
        path_i = satellites[i]["path"]
        path_j = satellites[j]["path"]

        # cdist computes distance between each pair of points.
        # Assuming timestamps are aligned, we actually just need distance at each step
        # np.linalg.norm(path_i - path_j, axis=1) would be faster if aligned.
        # But if they are just clouds of points, cdist works. Let's assume aligned points.
        dist = np.linalg.norm(path_i - path_j, axis=1)
        min_dist = np.min(dist)

        if min_dist < threshold:
            conjunctions.append((satellites[i]["id"], satellites[j]["id"], min_dist))

    return conjunctions
