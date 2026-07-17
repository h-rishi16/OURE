import numpy as np

from oure.risk.conjunction import check_conjunctions


def generate_mock_sats(n: int) -> list[dict]:
    sats = []
    for i in range(n):
        path = np.array([[x, i * 2.0, 0.0] for x in range(10)])
        sats.append(
            {
                "id": i,
                "min_coords": np.min(path, axis=0) - 1.0,
                "max_coords": np.max(path, axis=0) + 1.0,
                "path": path,
            }
        )
    sats[1]["path"] = sats[0]["path"].copy()
    sats[1]["min_coords"] = sats[0]["min_coords"].copy()
    sats[1]["max_coords"] = sats[0]["max_coords"].copy()
    return sats


def test_conjunctions_parallel_vs_single() -> None:
    sats = generate_mock_sats(50)
    res_single = check_conjunctions(sats, threshold=5.0, workers=1)
    res_multi = check_conjunctions(sats, threshold=5.0, workers=4)
    assert len(res_single) == len(res_multi)
    assert res_single == res_multi
    assert any(
        (r[0] == 0 and r[1] == 1) or (r[0] == 1 and r[1] == 0) for r in res_single
    )
