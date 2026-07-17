import numpy as np

from risk.conjunction import check_conjunctions


def test_check_conjunctions():
    # Sat 1 path from (0,0,0) to (10,0,0)
    path1 = np.array([[x, 0.0, 0.0] for x in range(11)])
    sat1 = {
        "id": 1,
        "min_coords": np.min(path1, axis=0) - 2.0,  # Add a margin
        "max_coords": np.max(path1, axis=0) + 2.0,
        "path": path1,
    }

    # Sat 2 path from (5,5,0) to (5,-5,0) -> Crosses sat 1 at (5,0,0) at step 5
    path2 = np.array([[5.0, 5.0 - x, 0.0] for x in range(11)])
    sat2 = {
        "id": 2,
        "min_coords": np.min(path2, axis=0) - 2.0,
        "max_coords": np.max(path2, axis=0) + 2.0,
        "path": path2,
    }

    # Sat 3 path far away
    path3 = np.array([[100.0, 100.0, 0.0] for x in range(11)])
    sat3 = {
        "id": 3,
        "min_coords": np.min(path3, axis=0) - 2.0,
        "max_coords": np.max(path3, axis=0) + 2.0,
        "path": path3,
    }

    conjunctions = check_conjunctions([sat1, sat2, sat3], threshold=5.0)

    # Only sat1 and sat2 should have a conjunction
    assert len(conjunctions) == 1
    id1, id2, dist = conjunctions[0]
    assert (id1 == 1 and id2 == 2) or (id1 == 2 and id2 == 1)
    assert dist == 0.0  # They cross exactly
